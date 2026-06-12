"""BaseMatcher 的单元测试：语言后缀拼接 get_new_sub_name，以及 __call__ 的整体编排。"""
import re

import pytest

from matcher.base_matcher import BaseMatcher


class _StubMatcher(BaseMatcher):
    """BaseMatcher 的具体子类桩，用于测试基类逻辑（绕过 ABC 不能实例化的限制）。"""

    def episode_match(self, raw_title: str) -> int:  # noqa: D401
        return -1


class _FixedNumMatcher(BaseMatcher):
    """集数取文件名中最后一个数字串（确定性），用于测试 __call__ 编排。"""

    def episode_match(self, raw_title: str) -> int:
        nums = re.findall(r"\d+", raw_title)
        return int(nums[-1]) if nums else -1


# 已校准：get_new_sub_name 的语言后缀拼接逻辑
@pytest.mark.parametrize(
    "sub_name, video_name, expected",
    [
        ("A[01].tc.ass", "A[01]", "A[01].繁體中文.chi.ass"),
        ("A[01].sc.ass", "A[01]", "A[01].简体中文.chi.ass"),
        ("A[01].ass", "A[01]", "A[01].ass"),  # 无语言标识
    ],
    ids=["tc", "sc", "no-language"],
)
def test_get_new_sub_name(sub_name, video_name, expected, default_language_ext):
    matcher = _StubMatcher(language_ext=default_language_ext)
    assert matcher.get_new_sub_name(video_name, sub_name) == expected


def test_call_orchestration(default_language_ext):
    """__call__：按集数把字幕映射到对应视频名（含多线程、splitext、集数→视频名查表）。"""
    matcher = _FixedNumMatcher(language_ext=default_language_ext)
    videos = ["Show [01].mkv", "Show [02].mkv"]
    subs = ["Show [01].tc.ass", "Show [02].sc.ass"]

    result = matcher(videos, subs)

    assert result["Show [01].tc.ass"] == "Show [01].繁體中文.chi.ass"
    assert result["Show [02].sc.ass"] == "Show [02].简体中文.chi.ass"


def test_call_episode_not_found_returns_none(default_language_ext):
    """字幕集数在视频中找不到时，新文件名应为 None。"""
    matcher = _FixedNumMatcher(language_ext=default_language_ext)
    videos = ["Show [01].mkv"]
    subs = ["Other [99].tc.ass"]  # 集数 99 没有对应视频

    result = matcher(videos, subs)
    assert result["Other [99].tc.ass"] is None
