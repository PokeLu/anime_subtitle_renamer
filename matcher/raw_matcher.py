import os, re
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

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
            match_pos = self.config["sub_match_pos"]
            pattern = self.config["sub_pattern"]

        matches = re.findall(pattern, raw_title)

        # 选中matches中的数字
        formated_matches = [''.join(re.findall(r'\d+', match)) for match in matches]
        # if self.debug_mode: print(f"Num matched: {formated_matches}")
        
        # 若匹配失败，返回-1
        ep_num = -1
        # 如果匹配到多个数字，则选择按照matched_pos选择
        if formated_matches and match_pos in range(-1, len(formated_matches)):
            ep_num = formated_matches[match_pos]

        return ep_num
    
    def __call__(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        new_sub_name_dict = {}
        
        # 获取无后缀视频名
        content_video_names = [os.path.splitext(video_name)[0] for video_name in video_names]
        # 获取视频集数, multi-threading
        with ThreadPoolExecutor(max_workers=32) as executor:
            # 并行生成键值元组列表
            key_value_pairs = executor.map(
                lambda name: (self.episode_match(name), name),
                content_video_names
            )
            video_name_dict = dict(key_value_pairs)

        # video_name_dict = {self.episode_match(content_video_name):content_video_name for content_video_name in content_video_names}
                
        for sub_name in sub_names:
            if self.debug_mode: print(f"Org filename: {sub_name}")
            
            # 获取字幕集数
            sub_episode = self.episode_match(sub_name, is_video=False)
            if self.debug_mode: print(f"Num selected: {sub_episode}")
            
            # sub_episode=-1，未找到集数信息
            if sub_episode==-1:
                print(f"{sub_name} episode match failed\n")
                new_sub_name_dict[sub_name] = None
                continue
            
            # 找到对应集数的视频名，获取新字幕名
            new_sub_name = None
            try:
                content_video_name = video_name_dict[sub_episode]
                new_sub_name = self.get_new_sub_name(content_video_name, sub_name)   
            except: 
                print(f"{sub_name} not found in video names")
                            
            if self.debug_mode: print(f"New filename: {new_sub_name}\n")
            new_sub_name_dict[sub_name] = new_sub_name
            
        return new_sub_name_dict