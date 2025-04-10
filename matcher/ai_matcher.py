from openai import OpenAI
from typing import Dict, List
import json

from .base_matcher import BaseMatcher

class AIMatcher(BaseMatcher):
    def __init__(self, video_ext: List[str] = ..., subtitle_ext: List[str] = ..., language_ext: Dict[str, str] = ..., debug_mode: bool = False):
        super().__init__(video_ext, subtitle_ext, language_ext, debug_mode)
        self.prompt_template = """
        你是一个专业的文件信息提取助手。你的任务是从给定的视频或字幕文件名中准确识别并提取出集数信息。请按照以下步骤操作：

        1. 仔细阅读文件名；
        2. 识别文件名中表示集数的部分，通常集数会以数字形式出现，并且可能被方括号、括号或其他符号包围；
        3. 提取出集数信息，并确保它是一个整数；
        4. 输出提取到的集数信息。
        
        要求：
        1. 确保输出的集数信息是整数，不要输出其他思考过程或其他冗余信息。
        2. 若你认为文件名中不包含集数信息，请输出-1。
        3. 输出应为以下json格式：{{"ep": ep_num}}

        **示例：**

        **输入1：** "Suzumiya Haruhi no Yuuutsu (TV 2009). 25; BD_h264_flac"
        **输出1：** {{"ep": 25}}

        **输入2：** "[Nekomoe kissaten] BanG Dream! It’s MyGO!!!!! [05][BDRip].JPSC"
        **输出2：** {{"ep": 5}}

        **输入3：** "One Piece - "ep"isode 123 [1080p]"
        **输出3：** {{"ep": 123}}

        **输入4：** "Attack on Titan S04E15.mkv"
        **输出4：** {{"ep": 15}}

        **输入5：** "Naruto Shippuden - 456.avi"
        **输出5：** {{"ep": 456}}

        **输入6：** "My Hero Academia - 03 [SubsPlease].mkv"
        **输出6：** {{"ep": 3}}

        **输入7：** "Demon Slayer - Kimetsu no Yaiba - 26 [1080p]"
        **输出7：** {{"ep": 26}}

        **输入8：** "[Airota&Nekomoe kissaten&LoliHouse] Yagate Kimi ni Naru - 12 [WebRip 1080p HEVC-yuv420p10 AAC ASSx2].TC"
        **输出8：** {{"ep": 12}}

        **输入9：** "Friends - Season 10 "ep"isode 17"
        **输出9：** {{"ep": 17}}

        **输入10：** "Breaking Bad - 05x12.mkv"
        **输出10：** {{"ep": 12}}

        ## 现在，请处理以下输入：

        **输入：** {}
        **输出：** 
        """
 
        
    def load_config(self, config: Dict):
        super().load_config(config)
        try:
            self.client = OpenAI(api_key=self.config['api_key'], base_url=self.config['base_url'])
            print(self.client.models.list())
            return f"Successfully generated the OpenAI client. Available models: {self.client.models.list()}"
        except:
            err_msg = f"Failed to generate the OpenAI client. Possible reasons could be invalid API key or unreachable API URL."
            print(err_msg)
            return err_msg
        
    def episode_match(self, raw_title: str) -> int:
        prompt = self.prompt_template.format(raw_title)
        
        try:
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                response_format={"type": "json_object"}
            )
            episode_json = json.loads(response.choices[0].message.content)
            episode = int(episode_json['ep'])
            
        except Exception as e:
            # 如果API调用失败，返回episode=-1，并打印错误信息
            episode = -1
            print(f"API调用失败: {e}")
        
        return episode