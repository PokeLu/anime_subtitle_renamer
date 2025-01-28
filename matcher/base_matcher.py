from typing import List, Dict
from abc import ABC, abstractmethod

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
    def __call__(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        return {"", ""}