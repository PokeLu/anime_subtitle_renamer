from .subtitle_matcher import SubtitleMatcher
from .base_matcher import BaseMatcher
from .raw_matcher import RawMatcher
from .ab_matcher import AbMatcher

SubtitleMatcher.register_mode("raw", RawMatcher)
SubtitleMatcher.register_mode("ab", AbMatcher)
SubtitleMatcher.register_mode("ai", BaseMatcher)

# 定义模块的对外接口, 仅暴露SubtitleMatcher
__all__ = ["SubtitleMatcher"]