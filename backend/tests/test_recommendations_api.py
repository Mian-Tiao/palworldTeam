"""推薦 API 測試(P-3;對應 test-plan TC-005/006)。使用 12 隻種子資料。"""

import pytest


def _pal_id(client, name):
    return client.get("/api/pals", params={"search": name}).json()["data"][0]["id"]


def test_recommendation_success(client):
    """TC-005:每隊皆含固定成員、人數 = 5、依總傷害由高到低排序。"""
    fixed = [_pal_id(client, "棉悠悠"), _pal_id(client, "碧海龍")]
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "target": {"elements": ["fire"]}},
    )
    assert resp.status_code == 200
    body = resp.json()
    teams = body["data"]["teams"]
    assert len(teams) >= 1

    totals = [t["total_dps"] for t in teams]
    assert totals == sorted(totals, reverse=True)

    for team in teams:
        assert len(team["members"]) == 5
        fixed_ids = {m["pal"]["id"] for m in team["members"] if m["is_fixed"]}
        assert fixed_ids == set(fixed)

    assert body["meta"]["level"] == 50
    assert body["meta"]["target_elements"] == ["fire"]


def test_breakdown_is_verifiable(client):
    """TC-006 精神:成員 DPS 合計=隊伍總傷害;技能 DPS=單發傷害÷冷卻。"""
    fixed = [_pal_id(client, "棉悠悠")]
    resp = client.post(
        "/api/team-recommendations",
        json={"fixed_pal_ids": fixed, "level": 50, "target": {"elements": ["fire"]}},
    )
    team = resp.json()["data"]["teams"][0]
    assert team["total_dps"] == pytest.approx(
        sum(m["total_dps"] for m in team["members"])
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
    """對火目標,最佳隊伍應包含水系輸出(克制 2×)。"""
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


def test_star_level_scales_buff(client):
    """星級提高 → 夥伴技能加成變強 → 帕魯攻擊加成%上升。"""
    fixed = [_pal_id(client, "波魯傑克斯")]

    def buff_rate(star):
        body = client.post(
            "/api/team-recommendations",
            json={"fixed_pal_ids": fixed, "level": 50, "star_level": star},
        ).json()
        provider = body["data"]["teams"][0]["members"][0]  # 固定成員=波魯傑克斯
        return provider["attack_buff_rate"]

    # 0 星滿疊 30%(自身 stack)、4 星滿疊 150%;星級越高加成越大
    assert buff_rate(4) > buff_rate(0) > 0
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
