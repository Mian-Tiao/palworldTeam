"""推薦 API 測試(P-3;對應 test-plan TC-005/006)。使用 12 隻種子資料。"""

import pytest


def _pal_id(client, name):
    return client.get("/api/pals", params={"search": name}).json()["data"][0]["id"]


def test_recommendation_success(client):
    """TC-005:每隊皆含固定成員、人數 = 5、依相對輸出由高到低排序。"""
    fixed = [_pal_id(client, "棉悠悠"), _pal_id(client, "碧海龍")]
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "target": {"elements": ["fire"]}},
    )
    assert resp.status_code == 200
    body = resp.json()
    teams = body["data"]["teams"]
    assert len(teams) >= 1

    fixed_totals = [t["fixed_total_dps"] for t in teams]
    assert fixed_totals == sorted(fixed_totals, reverse=True)

    for team in teams:
        assert len(team["members"]) == 5
        fixed_ids = {m["pal"]["id"] for m in team["members"] if m["is_fixed"]}
        assert fixed_ids == set(fixed)
        assert all("partner_skill" in m["pal"] for m in team["members"])

    assert body["meta"]["level"] == 50
    assert body["meta"]["target_elements"] == ["fire"]
    assert body["meta"]["calculation_mode"] == "palworld_1_0_passive_relative_score"
    assert body["meta"]["optimization_target"] == "fixed_pals_output"
    assert all(
        buff["buff_target"] == "pal_attack"
        and buff["buff_mechanic"] in ("flat", "stack")
        for team in teams
        for buff in team["active_buffs"]
    )


def test_breakdown_is_verifiable(client):
    """TC-006 精神:成員分數合計=隊伍分數;每秒分數=單次分數÷冷卻。"""
    fixed = [_pal_id(client, "棉悠悠")]
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "target": {"elements": ["fire"]}},
    )
    team = resp.json()["data"]["teams"][0]
    assert team["total_dps"] == pytest.approx(
        sum(m["total_dps"] for m in team["members"])
    )
    assert team["fixed_total_dps"] == pytest.approx(
        sum(m["total_dps"] for m in team["members"] if m["is_fixed"])
    )
    for member in team["members"]:
        assert member["total_dps"] == pytest.approx(
            sum(s["dps"] for s in member["equipped_skills"])
        )
        for s in member["equipped_skills"]:
            assert len(member["equipped_skills"]) <= 3
            assert s["dps"] == pytest.approx(
                s["damage_per_hit"] / s["cooldown_seconds"]
            )
            assert s["learned_level"] <= 50


def test_fire_target_favors_water_attackers(client):
    """對火目標,最佳隊伍應包含水系輸出(克制 1.5×)。"""
    fixed = [_pal_id(client, "棉悠悠")]
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "target": {"elements": ["fire"]}},
    )
    best = resp.json()["data"]["teams"][0]
    element_codes = {
        e["code"] for m in best["members"] for e in m["pal"]["elements"]
    }
    assert "water" in element_codes


def test_generic_target_works_without_target(client):
    fixed = [_pal_id(client, "棉悠悠")]
    resp = client.post(
        "/api/team-recommendations", json={"fixed_pal_ids": fixed, "level": 30},
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["target_elements"] == []
    assert resp.json()["meta"]["star_level"] == 4  # 預設滿星


def test_uncounted_partner_skill_is_explained(client):
    """非帕魯攻擊型夥伴技能仍回傳說明,但不得標成已計入。"""
    fixed = [_pal_id(client, "棉悠悠")]
    team = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50},
    ).json()["data"]["teams"][0]
    member = next(m for m in team["members"] if m["is_fixed"])
    passive = member["pal"]["partner_skill"]

    assert passive["effect_type"] == "other"
    assert passive["is_counted"] is False
    assert passive["current_buff_value"] is None
    assert passive["applies_to_fixed_pal_names"] == []
    assert passive["description_note"] is None


def test_star_level_scales_buff(client):
    """星級提高 → 夥伴技能加成變強 → 帕魯攻擊加成%上升。"""
    fixed = [_pal_id(client, "波魯傑克斯")]

    def response(star):
        body = client.post(
            "/api/team-recommendations",
            json={"fixed_pal_ids": fixed, "level": 50, "star_level": star},
        ).json()
        return body["data"]["teams"][0]

    # 波魯傑克斯是固定成員,其命中疊層必須進入實際推薦加成清單。
    for star, expected in ((0, 0.3), (4, 1.5)):
        team = response(star)
        orsek_buff = next(
            b for b in team["active_buffs"] if b["provider_name_zh"] == "波魯傑克斯"
        )
        assert orsek_buff["buff_mechanic"] == "stack"
        assert orsek_buff["buff_max_stacks"] == 30
        assert orsek_buff["buff_value"] == pytest.approx(expected)
        orsek_member = next(
            m for m in team["members"] if m["pal"]["name_zh"] == "波魯傑克斯"
        )
        passive = orsek_member["pal"]["partner_skill"]
        assert passive["is_counted"] is True
        assert passive["current_buff_value"] == pytest.approx(expected)
        assert passive["buff_mechanic"] == "stack"
        assert passive["buff_max_stacks"] == 30
        assert passive["applies_to_fixed_pal_names"] == ["波魯傑克斯"]
        assert "提升1%" not in passive["description"]
        assert "數值見上方目前星級" in passive["description"]
        assert "無星模板" in passive["description_note"]

        lifedrain_member = next(
            m for m in team["members"] if m["pal"]["name_zh"] == "織夜鹿"
        )
        lifedrain = lifedrain_member["pal"]["partner_skill"]
        assert lifedrain["is_counted"] is True
        assert "提升%" not in lifedrain["description"]
        assert "數值見上方目前星級" in lifedrain["description"]
    assert client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "star_level": 5},
    ).status_code == 422  # 超出 0~4 範圍


def test_duplicate_fixed_ids_rejected(client):
    pid = _pal_id(client, "棉悠悠")
    resp = client.post(
        "/api/team-recommendations", json={"fixed_pal_ids": [pid, pid], "level": 50},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["message"] == "固定成員不可重複"


def test_unknown_pal_id_rejected(client):
    resp = client.post(
        "/api/team-recommendations", json={"fixed_pal_ids": [99999], "level": 50},
    )
    assert resp.status_code == 422
    assert "99999" in resp.json()["error"]["message"]


def test_too_many_fixed_members_rejected(client):
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": [1, 2, 3, 4, 5, 6], "level": 50},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_level_out_of_range_rejected(client):
    pid = _pal_id(client, "棉悠悠")
    for level in (0, 81):
        resp = client.post(
            "/api/team-recommendations",
            json={"fixed_pal_ids": [pid], "level": level},
        )
        assert resp.status_code == 422


def test_unknown_target_element_rejected(client):
    pid = _pal_id(client, "棉悠悠")
    resp = client.post(
        "/api/team-recommendations",
        json={
            "fixed_pal_ids": [pid], "level": 50, "target": {"elements": ["plasma"]},
        },
    )
    assert resp.status_code == 422
    assert "屬性代碼" in resp.json()["error"]["message"]
