"""SubtitleMatcher 门面类的单元测试：模式注册表、模式切换、get_matcher 分发。"""
import pytest

# 导入 matcher 包即触发 matcher/__init__.py 中的模式注册
from matcher import SubtitleMatcher
from matcher.ab_matcher import AbMatcher
from matcher.ai_matcher import AIMatcher
from matcher.raw_matcher import RawMatcher


def test_registry_has_all_modes():
    assert set(SubtitleMatcher._mode_classes.keys()) == {"raw", "ab", "ai"}


def test_registered_classes_inherit_basematcher():
    from matcher.base_matcher import BaseMatcher

    for cls in SubtitleMatcher._mode_classes.values():
        assert issubclass(cls, BaseMatcher)


def test_set_mode_valid():
    sm = SubtitleMatcher(match_method="ab")
    assert sm.match_method == "ab"
    sm.set_mode("raw")
    assert sm.match_method == "raw"


def test_set_mode_invalid_raises():
    sm = SubtitleMatcher(match_method="ab")
    with pytest.raises(ValueError):
        sm.set_mode("does-not-exist")


def test_get_matcher_returns_correct_type(flat_config):
    sm = SubtitleMatcher(match_method="ab", config=flat_config)
    assert isinstance(sm.get_matcher(), AbMatcher)

    sm.set_mode("raw")
    assert isinstance(sm.get_matcher(), RawMatcher)

    sm.set_mode("ai")
    assert isinstance(sm.get_matcher(), AIMatcher)


def test_load_config_switches_match_method(flat_config):
    sm = SubtitleMatcher(match_method="ab")
    cfg = dict(flat_config)
    cfg["match_method"] = "raw"
    sm.load_config(cfg)

    assert sm.match_method == "raw"
    assert isinstance(sm.get_matcher(), RawMatcher)
