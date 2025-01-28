import re, os
from typing import List, Dict

from .utils import *

class SubtitleMatcher:
    def __init__(self, video_ext:List[str]=[], subtitle_ext:List[str]=[], language_ext:Dict[str, str]={}, 
                 match_method:str="ab", match_pos:int=-1, pattern:str=r"\d+", debug_mode:bool=False):
        self.video_ext = video_ext
        self.subtitle_ext = subtitle_ext
        self.language_ext = language_ext
        self.match_pos = match_pos
        self.pattern = re.compile(pattern)
        self.debug_mode = debug_mode
        self.set_mode(match_method)
    
    def set_mode(self, mode: str):
        # 允许的mode：raw, ab, ai
        if mode not in ["raw", "ab", "ai"]: 
            raise ValueError("Invalid mode. Please use 'raw', 'ab', or 'ai'.")
        self.match_method = mode
        
    def load_config(self, config: Dict):
        self.video_ext = config.get("video_ext", self.video_ext)
        self.subtitle_ext = config.get("subtitle_ext", self.subtitle_ext)
        self.language_ext = config.get("language_ext", self.language_ext)
        self.match_pos = config.get("matched_pos", self.match_pos)
        pattern = config.get("pattern", None)
        if pattern is not None: self.pattern = re.compile(pattern)
        self.debug_mode = config.get("debug_mode", self.debug_mode)
        match_method = config.get("match_method", self.match_method)
        self.set_mode(match_method)
        
    def clear_files(self, tar_dir, extensions):
        """
        遍历指定目录，查找具有指定扩展名的文件并删除。

        :param directory: 要搜索的根目录。
        :param extensions: 一个包含所需文件扩展名的列表或元组。
        :return: None。
        """
        print("Clear previous subtitles files...")
        # 若tar_dir不存在，则提前返回
        if not os.path.exists(tar_dir): 
            print("Target dir not found. Clear process aborted.")
            return 
        for filename in os.listdir(tar_dir):
            if all(ext not in filename for ext in extensions): continue
            try:
                os.remove(os.path.join(tar_dir, filename))
                if self.debug_mode: print(f"Deleted: {filename}")
            except OSError as e:
                print(f"Error: {filename} : {e.strerror}")
        print("Clear process finished.\n")
        
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

    def raw_title_match(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
        # 获取无后缀视频名
        content_video_names = [os.path.splitext(video_name)[0] for video_name in video_names]
        
        new_sub_name_dict = {}
        for sub_name in sub_names:
            if self.debug_mode: print(f"Org filename: {sub_name}")
            
            matches = re.findall(self.pattern, sub_name)
            
            # 选中matches中的数字
            formated_matches = [''.join(re.findall(r'\d', match)) for match in matches]
            if self.debug_mode: print(f"Num matched: {formated_matches}")
            
            # 格式化一位数字
            ep_num = ['0{}'.format(match) if len(match) == 1 else match for match in formated_matches]
            
            # 如果匹配到多个数字，则选择按照matched_pos选择，默认-1
            num_pos = self.match_pos if self.match_pos is not None else -1
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

    def title_match(self, video_names: List[str], sub_names: List[str]) -> Dict[str, str]:
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

    def __call__(self, video_dir: str, sub_src_dir: str, sub_tar_dir: str):
        print("Matching subtitles...")    
        
        # 获取路径下的所有视频文件名
        video_names = [filename for filename in os.listdir(video_dir) if os.path.splitext(filename)[1] in self.video_ext]
        
        # 获取路径下的所有字幕文件名和字幕文件路径
        sub_path_dict = {filename:filepath for filename, filepath in find_files(sub_src_dir, self.subtitle_ext) if os.path.splitext(filename)[1] in self.subtitle_ext}
        
        # 获取匹配的新字幕文件名，仅维护有更改的字幕文件
        if self.match_method == "raw":
            new_sub_name_dict = self.raw_title_match(video_names, list(sub_path_dict.keys()))
        else:
            new_sub_name_dict = self.title_match(video_names, list(sub_path_dict.keys()))
        
        # 执行重命名操作
        if not self.debug_mode:
            for sub_name in new_sub_name_dict.keys():
                copy_and_rename_file(sub_path_dict[sub_name], sub_tar_dir, new_sub_name_dict[sub_name])
            
        print("Renaming process finished.")
        
        return new_sub_name_dict    
