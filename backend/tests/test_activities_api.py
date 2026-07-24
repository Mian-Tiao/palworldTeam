"""活動夥伴技能總表 API 測試(釣魚/挖礦/伐木/採集/搬運)。種子含碎岩龜(挖礦)。"""


def test_activity_skills_lists_all_activities(client):
    resp = client.get("/api/activity-skills")
    assert resp.status_code == 200
    body = resp.json()
    codes = [a["activity"] for a in body["data"]["activities"]]
    assert codes == ["fishing", "mining", "logging", "gather", "carry"]


def test_mining_includes_drillgame(client):
    resp = client.get("/api/activity-skills", params={"activity": "mining"})
    assert resp.status_code == 200
    activities = resp.json()["data"]["activities"]
    assert len(activities) == 1
    skills = activities[0]["skills"]
    drill = next((s for s in skills if s["name_zh"] == "碎岩龜"), None)
    assert drill is not None
    assert drill["label_zh"] == "破壞礦石效率"
    assert drill["kind"] == "yield"
    assert drill["unit"] == "pct"
    assert len(drill["values_by_star"]) == 5
    # 0 星 ≤ 4 星(星級遞增)
    assert drill["values_by_star"][0] <= drill["values_by_star"][4]


def test_unknown_activity_returns_422(client):
    resp = client.get("/api/activity-skills", params={"activity": "cooking"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
