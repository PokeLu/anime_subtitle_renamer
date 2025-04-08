import re
from typing import Dict, List

from .base_matcher import BaseMatcher

class AbMatcher(BaseMatcher):
    def __init__(self, video_ext: List[str] = ..., subtitle_ext: List[str] = ..., language_ext: Dict[str, str] = ..., debug_mode: bool = False):
        super().__init__(video_ext, subtitle_ext, language_ext, debug_mode) 
        self.EPISODE_RE = re.compile(r"\d+")
        self.TITLE_RE = re.compile(
            r"(.*|\[.*])( -? \d+|\[\d+]|\[\d+.?[vV]\d]|第\d+[话話集]|\[第?\d+[话話集]]|\[\d+.?END]|[Ee][Pp]?\d+)(.*)"
        )
        # self.TITLE_RE = re.compile(
        #     r"(.*|\[.*])(\s*(?:EP?\d+|\[\d+\]|\d+|第\d+[话話集]|\[\d+[vV]\d+\]|\[\d+\.?END\]))(.*)$"
        # )
        
    def episode_match(self, raw_title: str) -> int:
        episode = -1
                
        raw_title = raw_title.strip().replace("\n", " ")
        content_title = raw_title.replace("【", "[").replace("】", "]")
        # 翻译组的名字
        match_obj = self.TITLE_RE.match(content_title)
        
        if match_obj is None: return episode
        
        # 处理标题
        season_info, episode_info, other = list(
            map(lambda x: x.strip(), match_obj.groups())
        )
        # 处理集数
        raw_episode = self.EPISODE_RE.search(episode_info)
        if raw_episode is not None:
            episode = int(raw_episode.group())
        
        return episode
