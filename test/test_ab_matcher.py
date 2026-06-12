"""AbMatcher（"ab" 模式）的单元测试。

集数提取规则来源于 AutoBangumi，覆盖常见动画字幕组命名约定。
预期值均已通过实际 AbMatcher 校准（见 plan 中的 calibration 步骤）。
"""
import pytest

from matcher.ab_matcher import AbMatcher


# 已校准：AbMatcher 能正确提取集数的命名模式
@pytest.mark.parametrize(
    "raw_title, expected",
    [
        ("[DMG&VCB-Studio] BOCCHI THE ROCK! [06][Ma10p_1080p][x265_flac]", 6),
        ("[SubsPlease] Jujutsu Kaisen - 23 [1080p]", 23),
        ("Attack on Titan S04E15", 15),
        ("孤独摇滚！ - S01E01 - 孤独的转机", 1),
        (
            "[Airota&Nekomoe kissaten&LoliHouse] Yagate Kimi ni Naru - 12 "
            "[WebRip 1080p HEVC-yuv420p10 AAC ASSx2]",
            12,
        ),
        ("My Hero Academia - 03 [SubsPlease]", 3),
        ("某动画第12话", 12),
        ("Breaking.Bad.S05E12.HEVC", 12),
        ("某动画", -1),  # 无集数信息
    ],
    ids=[
        "bocchi-bracket",
        "jujutsu-dash",
        "aot-SxxExx",
        "chinese-SxxExx",
        "yagate-dash",
        "myhero-dash",
        "chinese-第话",
        "breaking-SxxExx",
        "no-episode",
    ],
)
def test_ab_episode_match(raw_title, expected, flat_config):
    matcher = AbMatcher()
    matcher.load_config(flat_config)
    assert matcher.episode_match(raw_title) == expected


# 已校准：ab 模式正则的已知局限——纯空格/点分隔的裸集数无法识别，
# 这正是 ai 模式存在的意义。strict=True：若日后正则改进能识别，测试会变为失败以提醒更新。
@pytest.mark.xfail(
    reason="ab 模式正则已知局限：空格/点分隔的裸数字无法识别，建议此类用 ai 模式",
    strict=True,
)
@pytest.mark.parametrize(
    "raw_title, expected",
    [
        (
            "[Nekomoe kissaten] Shoujo Conto All Starlight 20 "
            "[BDRip 1080p HEVC-10bit FLAC]",
            20,
        ),
        ("One.Piece.1065", 1065),
    ],
    ids=["nekomoe-bare-20", "onepiece-dots"],
)
def test_ab_known_limitations(raw_title, expected, flat_config):
    matcher = AbMatcher()
    matcher.load_config(flat_config)
    assert matcher.episode_match(raw_title) == expected
