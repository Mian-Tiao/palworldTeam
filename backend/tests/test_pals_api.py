"""帕魯資料 API 測試(T-6;對應 test-plan TC-002/003/004/022)。"""


def test_list_pals_returns_all_seeded(client):
    resp = client.get("/api/pals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 15
    assert len(body["data"]) == 15
    first = body["data"][0]
    assert set(first) == {
        "id", "dev_name", "name_zh", "elements", "attack", "defense_stat", "hp_stat"
    }
    assert isinstance(first["attack"], int)


def test_search_by_chinese_name(client):
    """TC-002:搜尋回傳名稱含關鍵字的帕魯,不多不少。"""
    resp = client.get("/api/pals", params={"search": "棉悠悠"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["name_zh"] == "棉悠悠"
    assert body["data"][0]["dev_name"] == "SheepBall"


def test_search_by_dev_name_case_insensitive(client):
    resp = client.get("/api/pals", params={"search": "sheepball"})
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


def test_search_no_match_returns_empty_list(client):
    """TC-022:無匹配 → 200 空清單,非錯誤。"""
    resp = client.get("/api/pals", params={"search": "不存在的名字"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


def test_filter_by_element(client):
    """TC-003:僅回傳含該屬性的帕魯(含雙屬性)。"""
    resp = client.get("/api/pals", params={"element": "fire"})
    assert resp.status_code == 200
    body = resp.json()
    dev_names = {p["dev_name"] for p in body["data"]}
    assert dev_names == {"FlameBambi", "Baphomet"}
    for pal in body["data"]:
        assert any(e["code"] == "fire" for e in pal["elements"])


def test_search_and_element_filters_combine(client):
    resp = client.get("/api/pals", params={"search": "炎魔羊", "element": "dark"})
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] == 1


def test_filter_by_unknown_element_returns_422(client):
    resp = client.get("/api/pals", params={"element": "plasma"})
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "屬性代碼" in error["message"]


def test_get_pal_detail(client):
    listing = client.get("/api/pals", params={"search": "棉悠悠"}).json()
    pal_id = listing["data"][0]["id"]

    resp = client.get(f"/api/pals/{pal_id}")
    assert resp.status_code == 200
    pal = resp.json()["data"]
    assert pal["dev_name"] == "SheepBall"
    assert pal["shot_attack_stat"] == 70
    assert pal["partner_skill"]["effect_type"] == "other"
    levels = [s["learned_level"] for s in pal["active_skills"]]
    assert levels == sorted(levels) and len(levels) >= 3
    assert {s["category"] for s in pal["active_skills"]} <= {"Shot", "Melee"}


def test_get_pal_detail_dual_element(client):
    listing = client.get("/api/pals", params={"search": "企丸丸"}).json()
    pal = client.get(f"/api/pals/{listing['data'][0]['id']}").json()["data"]
    assert [e["code"] for e in pal["elements"]] == ["water", "ice"]


def test_get_pal_detail_team_buff_fields(client):
    listing = client.get("/api/pals", params={"search": "水靈兒"}).json()
    pal = client.get(f"/api/pals/{listing['data'][0]['id']}").json()["data"]
    partner = pal["partner_skill"]
    assert partner["effect_type"] == "team_buff"
    assert partner["buff_target"] == "pal_attack"
    assert partner["buff_element"] == "water"
    assert partner["buff_mechanic"] == "flat"
    # 專注 0~4 星逐星有效加成(遊戲 1.0 解包實值)
    assert partner["buff_tiers"] == [0.15, 0.17, 0.2, 0.24, 0.3]


def test_get_pal_detail_stack_buff(client):
    """波魯傑克斯(1.0):疊層型全隊攻擊加成,各星以滿疊理論值計。"""
    listing = client.get("/api/pals", params={"search": "波魯傑克斯"}).json()
    pal = client.get(f"/api/pals/{listing['data'][0]['id']}").json()["data"]
    partner = pal["partner_skill"]
    assert partner["effect_type"] == "team_buff"
    assert partner["buff_target"] == "pal_attack"
    assert partner["buff_element"] is None
    assert partner["buff_mechanic"] == "stack"
    assert partner["buff_max_stacks"] == 30
    # 0 星每層 1%×30=30%;4 星每層 5%×30=150%(對應遊戲滿星描述)
    assert partner["buff_tiers"][0] == 0.3
    assert partner["buff_tiers"][4] == 1.5


def test_get_pal_not_found_returns_404(client):
    """TC-004:不存在的 id → 404,{error} 格式,繁中訊息,無堆疊。"""
    resp = client.get("/api/pals/99999")
    assert resp.status_code == 404
    body = resp.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "PAL_NOT_FOUND"
    assert body["error"]["message"] == "找不到指定的帕魯"


def test_get_pal_invalid_id_returns_422(client):
    resp = client.get("/api/pals/abc")
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "請求參數格式不正確"
