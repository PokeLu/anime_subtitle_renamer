"""RawMatcher（"raw" 模式）的单元测试。

测试自定义正则 + 位置匹配的集数提取。
注意：RawMatcher 成功时返回匹配到的数字字符串（如 "23"、"01"，保留前导零），
匹配失败返回 int -1（见 matcher/raw_matcher.py 的实际实现）。
"""
import re

import pytest

from matcher.raw_matcher import RawMatcher


# 已校准：默认 pattern + pos=-1 的行为（video 与 sub 一致）
@pytest.mark.parametrize(
    "raw_title, is_video, expected",
    [
        ("[SubsPlease] Jujutsu Kaisen - 23 [1080p]", True, "23"),
        ("[SubsPlease] Jujutsu Kaisen - 23 [1080p]", False, "23"),
        ("A[01].tc.ass", False, "01"),
        ("A[01].mkv", True, "01"),
        ("Breaking.Bad.S05E12.HEVC", True, -1),  # 默认 pattern 不匹配 S05E12
        ("某动画", True, -1),  # 无数字
    ],
    ids=["jujutsu-video", "jujutsu-sub", "a01-sub", "a01-video", "sxxexx-nomatch", "no-digit"],
)
def test_raw_episode_match_default(raw_title, is_video, expected, flat_config):
    matcher = RawMatcher()
    matcher.load_config(flat_config)
    assert matcher.episode_match(raw_title, is_video=is_video) == expected


# 已校准：多候选数字时按 match_pos 选择
@pytest.mark.parametrize(
    "pos, expected",
    [(0, "05"), (1, "12"), (-1, "12"), (2, -1)],  # pos=2 越界 -> -1
    ids=["pos0", "pos1", "pos-last", "pos-out-of-range"],
)
def test_raw_match_position(pos, expected):
    cfg = {
        "video_pattern": r"\d+",
        "video_match_pos": pos,
        "sub_pattern": r"\d+",
        "sub_match_pos": pos,
    }
    matcher = RawMatcher()
    matcher.load_config(cfg)
    assert matcher.episode_match("Show 05 Episode 12", is_video=True) == expected


def test_raw_no_match_returns_minus_one():
    """无任何数字匹配时返回 -1。"""
    cfg = {
        "video_pattern": r"\d+",
        "video_match_pos": 0,
        "sub_pattern": r"\d+",
        "sub_match_pos": 0,
    }
    matcher = RawMatcher()
    matcher.load_config(cfg)
    assert matcher.episode_match("NoNumbersHere", is_video=True) == -1


def test_raw_load_config_compiles_pattern_and_casts_pos():
    """load_config 将 pattern 编译为正则对象、将位置转为 int。"""
    cfg = {
        "video_pattern": r"\d+",
        "video_match_pos": "0",  # 字符串，应被转为 int
        "sub_pattern": r"[a-z]+",
        "sub_match_pos": "-1",
    }
    matcher = RawMatcher()
    matcher.load_config(cfg)

    assert matcher.config["video_pattern"] == re.compile(r"\d+")
    assert matcher.config["sub_pattern"] == re.compile(r"[a-z]+")
    assert isinstance(matcher.config["video_match_pos"], int)
    assert isinstance(matcher.config["sub_match_pos"], int)
    assert matcher.config["video_match_pos"] == 0
    assert matcher.config["sub_match_pos"] == -1
