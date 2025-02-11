import os
from typing import List, Dict, Any

from .utils import *
from .base_matcher import BaseMatcher

class SubtitleMatcher:
    _mode_classes = {} # 储存子类映射
    def __init__(self, video_ext:List[str]=[], subtitle_ext:List[str]=[], language_ext:Dict[str, str]={}, 
                 match_method:str="ab", config:Dict[str, Any]={}, debug_mode:bool=False):
        self.video_ext = video_ext
        self.subtitle_ext = subtitle_ext
        self.language_ext = language_ext
        self.config = config
        self.debug_mode = debug_mode
        self.set_mode(match_method)
        
    @classmethod
    def register_mode(cls, mode:str, mode_class:BaseMatcher):
        # 注册子类
        if not issubclass(mode_class, BaseMatcher):
            raise TypeError(f"{mode_class.__name__} must inherit from BaseMatcher.")
        cls._mode_classes[mode] = mode_class
        
    def load_config(self, config: Dict):
        self.config = config
        self.video_ext = config.get("video_ext", self.video_ext)
        self.subtitle_ext = config.get("subtitle_ext", self.subtitle_ext)
        self.language_ext = config.get("language_ext", self.language_ext)
        self.debug_mode = config.get("debug_mode", self.debug_mode)
        match_method = config.get("match_method", self.match_method)
        self.set_mode(match_method)
    
    def set_mode(self, match_mode: str):
        if match_mode not in self._mode_classes: 
            raise ValueError(f"Invalid mode. Please select a mode in {self._mode_classes.keys()}.")        
        self.match_method = match_mode
        
    def get_matcher(self) -> BaseMatcher:
        matcher = self._mode_classes[self.match_method](self.video_ext, self.subtitle_ext, self.language_ext, self.debug_mode)
        matcher.load_config(self.config)
        return matcher
        
    def clear_files(self, tar_dir):
        """
        遍历指定目录，查找具有指定扩展名的文件并删除。

        :param directory: 要搜索的根目录。
        :return: None。
        """
        print("Clear previous subtitles files...")
        # 若tar_dir不存在，则提前返回
        if not os.path.exists(tar_dir): 
            print("Target dir not found. Clear process aborted.")
            return 
        for filename in os.listdir(tar_dir):
            if all(ext not in filename for ext in self.subtitle_ext): continue
            try:
                os.remove(os.path.join(tar_dir, filename))
                if self.debug_mode: print(f"Deleted: {filename}")
            except OSError as e:
                print(f"Error: {filename} : {e.strerror}")
        print("Clear process finished.\n")

    def __call__(self, video_dir: str, sub_src_dir: str, sub_tar_dir: str):
        print("Matching subtitles...")    
        
        # 获取路径下的所有视频文件名
        video_names = [filename for filename in os.listdir(video_dir) if os.path.splitext(filename)[1] in self.video_ext]
        
        # 获取路径下的所有字幕文件名和字幕文件路径
        sub_path_dict = {filename:filepath for filename, filepath in find_files(sub_src_dir, self.subtitle_ext) if os.path.splitext(filename)[1] in self.subtitle_ext}
        
        # 获取匹配的新字幕文件名
        new_sub_name_dict = self.get_matcher()(video_names, list(sub_path_dict.keys()))
        
        # 执行重命名操作
        if not self.debug_mode:
            for sub_name in new_sub_name_dict.keys():
                copy_and_rename_file(sub_path_dict[sub_name], sub_tar_dir, new_sub_name_dict[sub_name])
            
        print("Renaming process finished.")
        
        return new_sub_name_dict    
