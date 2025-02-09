import os, re
from typing import Dict, List, Any

from .base_matcher import BaseMatcher

class RawMatcher(BaseMatcher):
    def __init__(self, video_ext: List[str] = ..., subtitle_ext: List[str] = ..., language_ext: Dict[str, Any] = ..., debug_mode: bool = False):
        super().__init__(video_ext, subtitle_ext, language_ext, debug_mode)
        
    def load_config(self, config: Dict):
        super().load_config(config)
        
        match_pos = config.get("sub_match_pos", -1)
        self.config["sub_match_pos"] = int(match_pos)       

        pattern = config.get("sub_pattern", r"\d+")
        self.config["sub_pattern"] = re.compile(pattern)

        match_pos = config.get("video_match_pos", -1)
        self.config["video_match_pos"] = int(match_pos)
        
        pattern = config.get("video_pattern", r"\d+")
        self.config["video_pattern"] = re.compile(pattern)

    def episode_match(self, raw_title: str, is_video: bool=True) -> int:
        # load config from self.config
        if is_video:
            match_pos = self.config["video_match_pos"]
            pattern = self.config["video_pattern"]
        else:
            match_pos = self.config["video_match_pos"]
            pattern = self.config["video_pattern"]

        matches = re.findall(pattern, raw_title)

        # 选中matches中的数字
        formated_matches = [''.join(re.findall(r'\d+', match)) for match in matches]
        # if self.debug_mode: print(f"Num matched: {formated_matches}")
        
        # 如果匹配到多个数字，则选择按照matched_pos选择
        ep_num = formated_matches[match_pos]

        return ep_num