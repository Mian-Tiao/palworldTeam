"""加成速查矩陣測試(P-16):純函式邏輯 + API。"""

import pytest

from app.services.buff_matrix import (
    MatrixPal,
    build_buff_matrix,
    build_conditional_buffs,
)
from app.services.damage import PalSpec, TeamBuff, attack_buff_rate


def pal(pid, name, elements, attack=100):
    return MatrixPal(pal_id=pid, dev_name=name, name_zh=name,
                     elements=tuple(elements), attack_stat=attack)


def cand(p, value, element=None, mechanic="flat", max_stacks=None):
    return (p, f"{p.name_zh}的被動",
            TeamBuff("pal_attack", element, value), mechanic, max_stacks)


class TestBuildBuffMatrix:
    def test_element_restricted_buff_only_lists_matching_pals(self):
        dark = pal(1, "暗帕", ["dark"])
        earth = pal(2, "地帕", ["earth"])
        dark_buffer = pal(10, "暗加成", ["dark"])
        m = build_buff_matrix([dark, earth], [cand(dark_buffer, 0.3, "dark")])
        assert len(m.buffers) == 1
        assert m.buffers[0].applies_to_pal_ids == (1,)  # 只影響暗屬
        assert m.buffers[0].affected_count == 1

    def test_universal_buff_applies_to_all_fixed(self):
        dark, earth = pal(1, "暗帕", ["dark"]), pal(2, "地帕", ["earth"])
        uni = pal(10, "通用", ["fire"])
        m = build_buff_matrix([dark, earth], [cand(uni, 1.5, None)])
        assert m.buffers[0].applies_to_pal_ids == (1, 2)

    def test_irrelevant_buff_is_excluded(self):
        """對使用者的帕魯毫無作用者不列出。"""
        dark = pal(1, "暗帕", ["dark"])
        fire_buffer = pal(10, "火加成", ["fire"])
        m = build_buff_matrix([dark], [cand(fire_buffer, 0.3, "fire")])
        assert m.buffers == ()

    def test_sorted_by_value_times_affected_count(self):
        """排序= 幅度×影響隻數,不使用任何傷害模型。"""
        dark, earth = pal(1, "暗帕", ["dark"]), pal(2, "地帕", ["earth"])
        weak_uni = pal(10, "弱通用", ["fire"])      # 0.3 × 2 = 0.6
        strong_dark = pal(11, "強暗", ["dark"])     # 0.5 × 1 = 0.5
        m = build_buff_matrix(
            [dark, earth],
            [cand(strong_dark, 0.5, "dark"), cand(weak_uni, 0.3, None)],
        )
        assert [b.pal.name_zh for b in m.buffers] == ["弱通用", "強暗"]

    def test_dual_element_pal_matches_either_element(self):
        dual = pal(1, "水龍", ["water", "dragon"])
        dragon_buffer = pal(10, "龍加成", ["dragon"])
        m = build_buff_matrix([dual], [cand(dragon_buffer, 0.3, "dragon")])
        assert m.buffers[0].applies_to_pal_ids == (1,)

    def test_free_slots_and_tradeoff_flag(self):
        one = pal(1, "暗帕", ["dark"])
        buffers = [cand(pal(10 + i, f"B{i}", ["dark"]), 0.3, "dark") for i in range(4)]
        m = build_buff_matrix([one], buffers)
        assert m.free_slots == 4 and m.recruitable_count == 4
        assert m.needs_tradeoff is False  # 4 隻搶 4 空位 → 全帶

        m2 = build_buff_matrix([one], buffers + [cand(pal(99, "B5", ["dark"]), 0.3, "dark")])
        assert m2.recruitable_count == 5
        assert m2.needs_tradeoff is True  # 5 隻搶 4 空位 → 要選

    def test_fixed_member_providing_buff_does_not_consume_slot(self):
        """固定成員自己就是加成者時,不佔額外空位。"""
        self_buffer = pal(1, "自帶加成", ["dark"])
        m = build_buff_matrix([self_buffer], [cand(self_buffer, 0.3, "dark")])
        assert len(m.buffers) == 1
        assert m.recruitable_count == 0
        assert m.needs_tradeoff is False

    def test_matches_damage_module_applicability_rule(self):
        """矩陣的生效判斷必須與傷害計算同源(驗收條件)。"""
        dark = pal(1, "暗帕", ["dark"])
        spec = PalSpec("暗帕", "暗帕", ("dark",), 100, 100, ())
        for element, expect_applies in [("dark", True), ("fire", False), (None, True)]:
            buff = TeamBuff("pal_attack", element, 0.3)
            m = build_buff_matrix([dark], [(pal(10, "B", ["dark"]), "s", buff, "flat", None)])
            listed = bool(m.buffers)
            counted = attack_buff_rate(spec, [buff]) > 0
            assert listed == counted == expect_applies


class TestConditionalBuffs:
    """克制增傷:需以該屬性攻擊剋制的敵人才生效。"""

    MATCHUPS = {("dark", "normal"): 1.5, ("water", "fire"): 1.5}
    ALL = ("normal", "fire", "water", "dark")

    def _build(self, target=(), fixed_pals=None):
        cands = [
            (pal(10, "極道蛙", ["dark"]), "惡道", "dark", 0.4),
            (pal(11, "閃丸王", ["water"]), "水擊", "water", 0.4),
        ]
        return build_conditional_buffs(
            cands, self.MATCHUPS, fixed_pals=fixed_pals,
            target_elements=target, all_elements=self.ALL,
        )

    def test_effective_vs_derived_from_matchup(self):
        entries = self._build(())
        by_name = {e.pal.name_zh: e for e in entries}
        assert by_name["極道蛙"].effective_vs == ("normal",)  # 暗剋無
        assert by_name["閃丸王"].effective_vs == ("fire",)  # 水剋火

    def test_no_target_leaves_applicability_unknown(self):
        assert all(e.applies_to_target is None for e in self._build(()))

    def test_marks_applicability_against_selected_target(self):
        by_name = {e.pal.name_zh: e for e in self._build(("normal",))}
        assert by_name["極道蛙"].applies_to_target is True
        assert by_name["閃丸王"].applies_to_target is False

    def test_applicable_entries_sort_first(self):
        entries = self._build(("fire",))
        assert entries[0].pal.name_zh == "閃丸王"  # 對火目標生效者排前面

    def test_relevant_to_selected_pal_by_element(self):
        """選了暗屬帕魯 → 暗屬克制增傷(極道蛙)標記為與其相關並排最前。"""
        dark_pal = pal(1, "貝菈露潔", ["dark"])
        entries = self._build(fixed_pals=[dark_pal])
        by_name = {e.pal.name_zh: e for e in entries}
        assert by_name["極道蛙"].relevant_to_pal_ids == (1,)
        assert by_name["閃丸王"].relevant_to_pal_ids == ()
        assert entries[0].pal.name_zh == "極道蛙"  # 相關者排最前

    def test_dual_element_pal_matches_either_weakness(self):
        earth_water = pal(1, "趴趴鯰", ["earth", "water"])
        entries = self._build(fixed_pals=[earth_water])
        by_name = {e.pal.name_zh: e for e in entries}
        assert by_name["閃丸王"].relevant_to_pal_ids == (1,)  # 水屬相關

    def test_no_selected_pal_leaves_relevance_empty(self):
        assert all(e.relevant_to_pal_ids == () for e in self._build())

    def test_never_mixed_into_main_buffer_list(self):
        """條件型不得混入常駐加成矩陣(相加會誤導)。"""
        dark = pal(1, "暗帕", ["dark"])
        m = build_buff_matrix([dark], [])
        assert m.buffers == ()


class TestBuffMatrixApi:
    def test_returns_matrix_for_dark_pal(self, client):
        listing = client.get("/api/pals", params={"search": "啼卡爾"}).json()
        pid = listing["data"][0]["id"]
        resp = client.post("/api/buff-matrix", json={"fixed_pal_ids": [pid], "star_level": 4})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]["fixed_pals"]) == 1
        assert body["meta"]["free_slots"] == 4
        # 每個列出的加成都必須至少影響到該固定帕魯
        for b in body["data"]["buffers"]:
            assert pid in b["applies_to_pal_ids"]

    def test_star_level_changes_values(self, client):
        listing = client.get("/api/pals", params={"search": "啼卡爾"}).json()
        pid = listing["data"][0]["id"]

        def values(star):
            r = client.post("/api/buff-matrix", json={"fixed_pal_ids": [pid], "star_level": star})
            return {b["pal"]["name_zh"]: b["buff_value"] for b in r.json()["data"]["buffers"]}

        v0, v4 = values(0), values(4)
        assert v0 and v4
        assert all(v4[name] >= v0[name] for name in v0)
        assert any(v4[name] > v0[name] for name in v0)

    def test_duplicate_and_unknown_ids_rejected(self, client):
        listing = client.get("/api/pals", params={"search": "啼卡爾"}).json()
        pid = listing["data"][0]["id"]
        assert client.post(
            "/api/buff-matrix", json={"fixed_pal_ids": [pid, pid]}
        ).status_code == 422
        assert client.post(
            "/api/buff-matrix", json={"fixed_pal_ids": [999999]}
        ).status_code == 422

    def test_star_level_out_of_range_rejected(self, client):
        listing = client.get("/api/pals", params={"search": "啼卡爾"}).json()
        pid = listing["data"][0]["id"]
        resp = client.post("/api/buff-matrix", json={"fixed_pal_ids": [pid], "star_level": 5})
        assert resp.status_code == 422
