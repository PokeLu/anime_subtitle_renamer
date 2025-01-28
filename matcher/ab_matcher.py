import os, re
from typing import Dict, List

from .base_matcher import BaseMatcher

class AbMatcher(BaseMatcher):
    def __init__(self, video_ext: List[str] = ..., subtitle_ext: List[str] = ..., language_ext: Dict[str, str] = ..., debug_mode: bool = False):
        super().__init__(video_ext, subtitle_ext, language_ext, debug_mode) 
        
    @staticmethod
    def ab_episode_match(raw_title: str) -> int:
        EPISODE_RE = re.compile(r"\d+")
        TITLE_RE = re.compile(
            r"(.*|\[.*])( -? \d+|\[\d+]|\[\d+.?[vV]\d]|第\d+[话話集]|\[第?\d+[话話集]]|\[\d+.?END]|[Ee][Pp]?\d+)(.*)"
        )
        
        raw_title = raw_title.strip().replace("\n", " ")
        content_title = raw_title.replace("【", "[").replace("】", "]")
        # 翻译组的名字
        match_obj = TITLE_RE.match(content_title)
        # 处理标题
        season_info, episode_info, other = list(
            map(lambda x: x.strip(), match_obj.groups())
        )
        # 处理集数
        raw_episode = EPISODE_RE.search(episode_info)
        episode = 0
        if raw_episode is not None:
            episode = int(raw_episode.group())
        
        return episode
    
    def __call__(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        new_sub_name_dict = {}
        
        # 获取无后缀视频名
        content_video_names = [os.path.splitext(video_name)[0] for video_name in video_names]
        # 获取视频集数
        video_name_dict = {self.ab_episode_match(content_video_name):content_video_name for content_video_name in content_video_names}
        
        for sub_name in sub_names:
            if self.debug_mode: print(f"Org filename: {sub_name}")
            
            # 获取字幕集数
            sub_episode = self.ab_episode_match(sub_name)
            if self.debug_mode: print(f"Num selected: {sub_episode}")
            
            # 找到对应集数的视频名
            try:
                content_video_name = video_name_dict[sub_episode]   
            except: 
                print(f"{sub_name} not found in video names")
                continue
                            
            new_sub_name = self.get_new_sub_name(content_video_name, sub_name)
            if self.debug_mode: print(f"New filename: {new_sub_name}\n")
            new_sub_name_dict[sub_name] = new_sub_name
            
        return new_sub_name_dict