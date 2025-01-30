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
        
    def __call__(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        # 获取无后缀视频名
        content_video_names = [os.path.splitext(video_name)[0] for video_name in video_names]
        
        new_sub_name_dict = {}
        for sub_name in sub_names:
            if self.debug_mode: print(f"Org filename: {sub_name}")
            
            matches = re.findall(self.config["sub_pattern"], sub_name)
            
            # 选中matches中的数字
            formated_matches = [''.join(re.findall(r'\d', match)) for match in matches]
            if self.debug_mode: print(f"Num matched: {formated_matches}")
            
            # 格式化一位数字
            ep_num = ['0{}'.format(match) if len(match) == 1 else match for match in formated_matches]
            
            # 如果匹配到多个数字，则选择按照matched_pos选择，默认-1
            num_pos = self.config["sub_match_pos"] if self.config["sub_match_pos"] is not None else -1
            ep_num = ep_num[num_pos]
            if self.debug_mode: print(f"Num selected: {ep_num}")
                
            # 找到video names中的对应video name
            try:
                video_name = [name for name in content_video_names if f"E{ep_num}" in name][0]   
            except:
                print(f"{sub_name} not found in video names")
                continue
                            
            new_sub_name = self.get_new_sub_name(video_name, sub_name)
            if self.debug_mode: print(f"New filename: {new_sub_name}\n")
            new_sub_name_dict[sub_name] = new_sub_name
        
        return new_sub_name_dict