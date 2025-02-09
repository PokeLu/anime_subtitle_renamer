from typing import List, Dict
from abc import ABC, abstractmethod
import os

class BaseMatcher(ABC):
    def __init__(self, video_ext:List[str]=[], subtitle_ext:List[str]=[], language_ext:Dict[str, str]={}, 
                 debug_mode:bool=False):
        self.video_ext = video_ext
        self.subtitle_ext = subtitle_ext
        self.language_ext = language_ext
        self.debug_mode = debug_mode
        self.config = {}
        
    def load_config(self, config: Dict):
        self.config = config
    
    def get_new_sub_name(self, content_video_name: str, sub_name: str) -> str:
        # 找到当前filename的扩展名
        ext = sub_name.split(".")[-1]
        
        # 查看是否存在字体信息
        for code in self.language_ext.keys():
            if code.lower() in sub_name.lower().split("."):
                ext_language = self.language_ext[code]
                ext = f"{ext_language}.{ext}"
        if self.debug_mode: print(f"Language Ext to be added: {ext}")
                        
        new_sub_name = f"{content_video_name}.{ext}"
        return new_sub_name
    
    @abstractmethod
    def episode_match(self, raw_title: str) -> int:
        return 0
    
    def __call__(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        new_sub_name_dict = {}
        
        # 获取无后缀视频名
        content_video_names = [os.path.splitext(video_name)[0] for video_name in video_names]
        # 获取视频集数
        video_name_dict = {self.episode_match(content_video_name):content_video_name for content_video_name in content_video_names}
        
        for sub_name in sub_names:
            if self.debug_mode: print(f"Org filename: {sub_name}")
            
            # 获取字幕集数
            sub_episode = self.episode_match(sub_name)
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