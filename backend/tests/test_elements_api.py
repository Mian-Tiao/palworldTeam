"""屬性與克制表 API 測試(T-6;對應 test-plan TC-001)。"""


def test_elements_returns_nine_elements_and_81_matchups(client):
    resp = client.get("/api/elements")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]["elements"]) == 9
    assert len(body["data"]["matchups"]) == 81
    assert body["meta"] == {"element_total": 9, "matchup_total": 81}

    codes = {e["code"] for e in body["data"]["elements"]}
    assert codes == {
        "normal", "fire", "water", "leaf", "electricity",
        "ice", "earth", "dark", "dragon",
    }


def test_matchup_multipliers_are_correct(client):
    body = client.get("/api/elements").json()
    table = {
        (m["attacker"], m["defender"]): m["multiplier"]
        for m in body["data"]["matchups"]
    }
    assert table[("water", "fire")] == 1.5
    assert table[("fire", "water")] == 0.66
    assert table[("dark", "normal")] == 1.5
    assert table[("normal", "normal")] == 1.0


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"data": {"status": "ok"}, "meta": {}}
