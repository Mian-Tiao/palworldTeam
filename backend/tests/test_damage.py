"""傷害計算器單元測試(P-2)。

對照值皆為依 project-memory「已確認的業務規則(傷害公式)」手算的結果。
純函式測試,不需要 client fixture 與資料庫。
"""

import pytest

from app.services.damage import (
    DEFAULT_ENEMY_DEFENSE,
    PalSpec,
    SkillSpec,
    TargetSpec,
    TeamBuff,
    attack_buff_rate,
    attack_value,
    calculate_pal_damage,
    enemy_defense,
    skill_damage,
    stab_multiplier,
    type_multiplier,
)

# 測試用克制表片段(完整 81 筆由資料庫提供,計算器只查字典)
MATCHUPS = {
    ("water", "fire"): 2.0,
    ("fire", "water"): 0.5,
    ("fire", "leaf"): 2.0,
    ("fire", "ice"): 2.0,
    ("normal", "dark"): 0.5,
}


def make_pal(**overrides):
    defaults = dict(
        dev_name="TestPal",
        name_zh="測試帕魯",
        elements=("water",),
        shot_attack_stat=70,
        melee_attack_stat=80,
        skills=(),
    )
    defaults.update(overrides)
    return PalSpec(**defaults)


def make_skill(**overrides):
    defaults = dict(
        name_zh="測試技能",
        element="water",
        power=100,
        cooldown_seconds=10.0,
        category="Shot",
        learned_level=1,
    )
    defaults.update(overrides)
    return SkillSpec(**defaults)


class TestAttackValue:
    def test_formula_with_floor(self):
        # FLOOR(100 + 70×0.075×50) = FLOOR(362.5) = 362
        assert attack_value(70, 50) == 362

    def test_level_one(self):
        # FLOOR(100 + 100×0.075×1) = FLOOR(107.5) = 107
        assert attack_value(100, 1) == 107


class TestEnemyDefense:
    def test_boss_defense_formula(self):
        # 50 + 93×0.075×50 = 398.75(Q-D3:指定頭目)
        target = TargetSpec(elements=("dark",), defense_stat=93, level=50)
        assert enemy_defense(target) == pytest.approx(398.75)

    def test_no_target_uses_constant(self):
        assert enemy_defense(None) == DEFAULT_ENEMY_DEFENSE

    def test_target_without_stats_uses_constant(self):
        # 屬性組合模式(無防禦/等級資料)也用常數
        assert enemy_defense(TargetSpec(elements=("fire",))) == DEFAULT_ENEMY_DEFENSE


class TestMultipliers:
    def test_single_element_advantage(self):
        assert type_multiplier("water", ("fire",), MATCHUPS) == 2.0

    def test_disadvantage(self):
        assert type_multiplier("fire", ("water",), MATCHUPS) == 0.5

    def test_dual_element_multiplies(self):
        # 火技能對(草、冰)雙屬性:2×2 = 4(最高 4×)
        assert type_multiplier("fire", ("leaf", "ice"), MATCHUPS) == 4.0

    def test_unknown_pair_defaults_to_one(self):
        assert type_multiplier("water", ("dragon",), MATCHUPS) == 1.0

    def test_empty_target_is_neutral(self):
        assert type_multiplier("water", (), MATCHUPS) == 1.0

    def test_stab_applies_to_matching_element(self):
        assert stab_multiplier("water", ("water", "dragon")) == 1.2

    def test_stab_not_applied_otherwise(self):
        assert stab_multiplier("fire", ("water", "dragon")) == 1.0


class TestTeamBuff:
    def test_same_kind_buffs_add_up(self):
        pal = make_pal(elements=("fire",))
        buffs = [
            TeamBuff("pal_attack", "fire", 0.10),
            TeamBuff("pal_attack", "fire", 0.10),
        ]
        assert attack_buff_rate(pal, buffs) == pytest.approx(0.20)

    def test_element_restricted_buff_skips_other_pals(self):
        pal = make_pal(elements=("water",))
        buffs = [TeamBuff("pal_attack", "fire", 0.10)]
        assert attack_buff_rate(pal, buffs) == 0.0

    def test_unrestricted_buff_applies_to_all(self):
        pal = make_pal(elements=("water",))
        buffs = [TeamBuff("pal_attack", None, 0.10)]
        assert attack_buff_rate(pal, buffs) == pytest.approx(0.10)

    def test_player_attack_buff_ignored_for_pals(self):
        pal = make_pal(elements=("water",))
        buffs = [TeamBuff("player_attack", None, 0.10)]
        assert attack_buff_rate(pal, buffs) == 0.0


class TestSkillDamage:
    def test_hand_computed_reference_case(self):
        """完整公式手算對照:
        水帕魯(shot 70)Lv50 以水技能(威力 100)打火目標,防禦 400:
        攻擊值 = 362;傷害 = 1.1×((1.5×50+20)×100×362÷400)÷15 ×2(克制)×1.2(STAB)
                = 1.1×(95×100×362÷400)÷15×2.4 = 1513.16
        """
        pal = make_pal()
        result = skill_damage(
            pal, make_skill(), level=50, defense=400.0,
            matchups=MATCHUPS, target_elements=("fire",),
        )
        assert result.base_attack_value == 362
        assert result.type_multiplier == 2.0
        assert result.stab_multiplier == 1.2
        assert result.damage_per_hit == pytest.approx(1513.16)
        assert result.dps == pytest.approx(151.316)  # 冷卻 10 秒

    def test_melee_skill_uses_melee_stat(self):
        pal = make_pal()  # shot 70, melee 80
        result = skill_damage(
            pal, make_skill(category="Melee"), level=50, defense=400.0,
            matchups=MATCHUPS,
        )
        # FLOOR(100 + 80×0.075×50) = 400
        assert result.attack_stat_used == 80
        assert result.base_attack_value == 400

    def test_buff_multiplies_attack_value(self):
        pal = make_pal()
        result = skill_damage(
            pal, make_skill(), level=50, defense=400.0,
            matchups=MATCHUPS, buff_rate=0.20,
        )
        assert result.buffed_attack_value == pytest.approx(362 * 1.2)


class TestCalculatePalDamage:
    def test_filters_by_learned_level_and_picks_top3_dps(self):
        """5 技能:1 個未習得(Lv60);其餘 4 個取加權 DPS 前 3。"""
        pal = make_pal(skills=(
            make_skill(name_zh="未習得", power=999, learned_level=60),
            # DPS 排序(Lv50、防禦 400、無目標屬性、水系 STAB 1.2):
            make_skill(name_zh="小水槍", power=30, cooldown_seconds=2.0),   # 高頻
            make_skill(name_zh="中水彈", power=60, cooldown_seconds=6.0),
            make_skill(name_zh="大水炮", power=150, cooldown_seconds=55.0),  # 低 DPS
            make_skill(name_zh="能量彈", element="normal", power=35,
                       cooldown_seconds=4.0),  # 無 STAB
        ))
        result = calculate_pal_damage(pal, level=50, matchups=MATCHUPS)

        names = [d.skill.name_zh for d in result.equipped_skills]
        assert "未習得" not in names
        assert len(names) == 3
        # 威力/冷卻×1.2:小水槍 18、中水彈 12、能量彈 8.75、大水炮 3.27 → 前三
        assert names == ["小水槍", "中水彈", "能量彈"]
        assert result.total_dps == pytest.approx(
            sum(d.dps for d in result.equipped_skills)
        )

    def test_fewer_than_three_skills(self):
        pal = make_pal(skills=(make_skill(),))
        result = calculate_pal_damage(pal, level=50, matchups=MATCHUPS)
        assert len(result.equipped_skills) == 1
        assert result.total_dps == pytest.approx(result.equipped_skills[0].dps)

    def test_no_usable_skills_gives_zero(self):
        pal = make_pal(skills=(make_skill(learned_level=60),))
        result = calculate_pal_damage(pal, level=1, matchups=MATCHUPS)
        assert result.equipped_skills == ()
        assert result.total_dps == 0.0

    def test_boss_target_changes_defense(self):
        pal = make_pal(skills=(make_skill(),))
        boss = TargetSpec(elements=("fire",), defense_stat=93, level=50)
        generic = calculate_pal_damage(pal, level=50, matchups=MATCHUPS)
        vs_boss = calculate_pal_damage(pal, level=50, matchups=MATCHUPS, target=boss)
        assert vs_boss.enemy_defense == pytest.approx(398.75)
        # 對火頭目有 2× 克制,且防禦略低於常數 400 → 輸出必高於通用計算
        assert vs_boss.total_dps > generic.total_dps

    def test_team_buff_raises_output(self):
        pal = make_pal(elements=("fire",), skills=(make_skill(element="fire"),))
        buffed = calculate_pal_damage(
            pal, level=50, matchups=MATCHUPS,
            team_buffs=[TeamBuff("pal_attack", "fire", 0.10)],
        )
        plain = calculate_pal_damage(pal, level=50, matchups=MATCHUPS)
        assert buffed.attack_buff_rate == pytest.approx(0.10)
        assert buffed.total_dps == pytest.approx(plain.total_dps * 1.10)
