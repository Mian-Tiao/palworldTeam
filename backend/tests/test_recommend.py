"""推薦引擎單元測試(P-3)。純函式測試,不需要 client fixture。"""

import pytest

from app.services.damage import PalSpec, SkillSpec, TeamBuff
from app.services.recommend import CandidatePal, recommend_teams

MATCHUPS = {}  # 引擎測試不需要克制(倍率預設 1.0)


def make_candidate(dev_name, power, element="water", buff=None):
    """單技能帕魯:輸出大小由 power 控制,方便手排名次。"""
    pal = PalSpec(
        dev_name=dev_name,
        name_zh=dev_name,
        elements=(element,),
        shot_attack_stat=100,
        melee_attack_stat=100,
        skills=(
            SkillSpec(
                name_zh=f"{dev_name}的技能", element="normal", power=power,
                cooldown_seconds=10.0, category="Shot", learned_level=1,
            ),
        ),
    )
    return CandidatePal(pal=pal, team_buff=buff)


class TestRecommendTeams:
    def test_fixed_members_always_included_and_team_full(self):
        candidates = [make_candidate(f"P{i}", power=10 * (i + 1)) for i in range(8)]
        teams = recommend_teams(
            candidates, fixed_dev_names=["P0", "P1"], level=50, matchups=MATCHUPS,
        )
        for team in teams:
            names = [m.damage.pal.dev_name for m in team.members]
            assert len(names) == 5
            assert {"P0", "P1"} <= set(names)
            fixed_flags = {
                m.damage.pal.dev_name: m.is_fixed for m in team.members
            }
            assert fixed_flags["P0"] and fixed_flags["P1"]

    def test_best_team_picks_strongest_fillers(self):
        # P0 固定;P7(80)、P6(70)、P5(60)、P4(50)為最強填充
        candidates = [make_candidate(f"P{i}", power=10 * (i + 1)) for i in range(8)]
        teams = recommend_teams(
            candidates, fixed_dev_names=["P0"], level=50, matchups=MATCHUPS,
        )
        best = teams[0]
        names = {m.damage.pal.dev_name for m in best.members}
        assert names == {"P0", "P7", "P6", "P5", "P4"}

    def test_teams_sorted_by_fixed_output_then_team_output(self):
        candidates = [make_candidate(f"P{i}", power=10 * (i + 1)) for i in range(8)]
        teams = recommend_teams(
            candidates, fixed_dev_names=["P0"], level=50, matchups=MATCHUPS,
        )
        keys = [(t.fixed_total_dps, t.total_dps) for t in teams]
        assert keys == sorted(keys, reverse=True)

    def test_buffer_for_fixed_pal_beats_high_damage_filler(self):
        """推薦目標是提高固定帕魯,不是讓支援位自己打出更高傷害。"""
        fixed = make_candidate("Fixed", power=100, element="fire")
        buffer = make_candidate(
            "Buffer", power=1, element="fire",
            buff=TeamBuff("pal_attack", "fire", 0.50),
        )
        selfish_damage = make_candidate("Selfish1000", power=1000, element="water")
        best = recommend_teams(
            [fixed, buffer, selfish_damage], fixed_dev_names=["Fixed"],
            level=50, matchups=MATCHUPS, team_size=2,
        )[0]

        assert {m.damage.pal.dev_name for m in best.members} == {"Fixed", "Buffer"}
        assert best.fixed_total_dps == pytest.approx(
            next(m.damage.total_dps for m in best.members if m.is_fixed)
        )

    def test_buffer_chosen_when_synergy_beats_raw_power(self):
        """火系加成者(自身威力 10)+ 火系主攻(200)勝過純堆威力(90)。

        名額 2(固定 1):
        - {Buffer, Fire200}:200×1.5 + 10 = 310
        - {Fire200, Water90}:200 + 90 = 290
        """
        buffer = make_candidate(
            "Buffer", power=10, element="fire",
            buff=TeamBuff("pal_attack", "fire", 0.50),
        )
        fire_dps = make_candidate("Fire200", power=200, element="fire")
        water_dps = make_candidate("Water90", power=90, element="water")
        fixed = make_candidate("Fixed", power=10, element="water")
        teams = recommend_teams(
            [fixed, buffer, fire_dps, water_dps],
            fixed_dev_names=["Fixed"], level=50, matchups=MATCHUPS, team_size=3,
        )
        best = teams[0]
        names = {m.damage.pal.dev_name for m in best.members}
        assert names == {"Fixed", "Buffer", "Fire200"}
        # 加成正確套用:Fire200 的 attack_buff_rate = 0.5,Fixed(水)不受火限定加成
        rates = {m.damage.pal.dev_name: m.damage.attack_buff_rate for m in best.members}
        assert rates["Fire200"] == pytest.approx(0.50)
        assert rates["Fixed"] == 0.0
        # 呈現用的生效加成清單含提供者
        assert [b.provider_dev_name for b in best.active_buffs] == ["Buffer"]

    def test_all_fixed_team_returns_single_combination(self):
        candidates = [make_candidate(f"P{i}", power=10) for i in range(6)]
        teams = recommend_teams(
            candidates,
            fixed_dev_names=["P0", "P1", "P2", "P3", "P4"],
            level=50, matchups=MATCHUPS,
        )
        assert len(teams) == 1
        assert {m.damage.pal.dev_name for m in teams[0].members} == {
            "P0", "P1", "P2", "P3", "P4"
        }

    def test_total_equals_sum_of_members(self):
        candidates = [
            make_candidate(f"P{i}", power=10 * (i + 1), element="fire") for i in range(6)
        ] + [
            make_candidate(
                "Buffer", power=5, element="fire",
                buff=TeamBuff("pal_attack", "fire", 0.10),
            )
        ]
        teams = recommend_teams(
            candidates, fixed_dev_names=["P0"], level=50, matchups=MATCHUPS,
        )
        for team in teams:
            assert team.total_dps == pytest.approx(
                sum(m.damage.total_dps for m in team.members)
            )
            assert team.fixed_total_dps == pytest.approx(
                sum(m.damage.total_dps for m in team.members if m.is_fixed)
            )
