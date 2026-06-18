from openai import OpenAI
from typing import Dict, List, Optional
import json
import re

from .base_matcher import BaseMatcher

# markdown 代码块包裹（```json / ```）
_CODE_FENCE_RE = re.compile(r"```(?:json)?", re.IGNORECASE)
# 本场景 schema 扁平（{"ep": int}），无需处理嵌套大括号
_JSON_OBJ_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _strip_reasoning(text: Optional[str]) -> str:
    """剥离 thinking model 的推理痕迹，保留最终答案。

    供解析与回填对话历史使用——回填给重试轮的 assistant 内容若带推理会污染上下文。
    兼容三类 thinking 输出：
      - 配对的 <think>...</think>
      - 初代 DeepSeek-R1：只有 </think> 结束标记、无 <think> 开始标记
      - 思考被截断：只有 <think>、无 </think>（整段都是推理）
    """
    text = text or ""
    if "</think>" in text:
        # 有结束标记（无论是否有配对的开始标记）：取最后一个 </think> 之后的内容
        text = text.rsplit("</think>", 1)[1]
    elif "<think>" in text:
        # 只有开始标记、无结束标记：思考被截断，整段都是推理，清空
        text = ""
    text = _CODE_FENCE_RE.sub("", text)   # 去掉 markdown 代码块包裹
    return text.strip()


def _extract_episode(content: Optional[str]) -> Optional[int]:
    """从模型回复中稳健抽取 {"ep": int}。解析失败返回 None（由调用方转 -1）。

    依次尝试：清洗后整体解析 → 原始整体解析 → 兜底取最后一个 {...} 块。
    可吞掉 thinking model 的推理链、markdown 代码块与前置散文，
    不依赖服务端任何 json_object / json_schema 约束。
    """
    if content is None:
        return None
    cleaned = _strip_reasoning(content)
    for candidate in (cleaned, content):           # 先试清洗后，再试原始
        try:
            return int(json.loads(candidate)["ep"])
        except (ValueError, TypeError, KeyError):
            continue
    for match in reversed(_JSON_OBJ_RE.findall(cleaned)):  # 兜底：取最后一个 {...}
        try:
            obj = json.loads(match)
            if "ep" in obj:
                return int(obj["ep"])
        except (ValueError, TypeError):
            continue
    return None


class AIMatcher(BaseMatcher):
    def __init__(self, video_ext: List[str] = ..., subtitle_ext: List[str] = ..., language_ext: Dict[str, str] = ..., debug_mode: bool = False):
        super().__init__(video_ext, subtitle_ext, language_ext, debug_mode)
        # self.prompt_template = """
        # 你是一个专业的文件信息提取助手。你的任务是从给定的视频或字幕文件名中准确识别并提取出集数信息。请按照以下步骤操作：

        # 1. 仔细阅读文件名；
        # 2. 识别文件名中表示集数的部分，通常集数会以数字形式出现，并且可能被方括号、括号或其他符号包围；
        # 3. 提取出集数信息，并确保它是一个整数；
        # 4. 输出提取到的集数信息。
        
        # 要求：
        # 1. 确保输出的集数信息是整数，不要输出其他思考过程或其他冗余信息。
        # 2. 若你认为文件名中不包含集数信息，请输出-1。
        # 3. 输出应为以下json格式：{{"ep": ep_num}}

        # **示例：**

        # **输入1：** "Suzumiya Haruhi no Yuuutsu (TV 2009). 25; BD_h264_flac"
        # **输出1：** {{"ep": 25}}

        # **输入2：** "[Nekomoe kissaten] BanG Dream! It’s MyGO!!!!! [05][BDRip].JPSC"
        # **输出2：** {{"ep": 5}}

        # **输入3：** "One Piece - "ep"isode 123 [1080p]"
        # **输出3：** {{"ep": 123}}

        # **输入4：** "Attack on Titan S04E15.mkv"
        # **输出4：** {{"ep": 15}}

        # **输入5：** "Naruto Shippuden - 456.avi"
        # **输出5：** {{"ep": 456}}

        # **输入6：** "My Hero Academia - 03 [SubsPlease].mkv"
        # **输出6：** {{"ep": 3}}

        # **输入7：** "Demon Slayer - Kimetsu no Yaiba - 26 [1080p]"
        # **输出7：** {{"ep": 26}}

        # **输入8：** "[Airota&Nekomoe kissaten&LoliHouse] Yagate Kimi ni Naru - 12 [WebRip 1080p HEVC-yuv420p10 AAC ASSx2].TC"
        # **输出8：** {{"ep": 12}}

        # **输入9：** "Friends - Season 10 "ep"isode 17"
        # **输出9：** {{"ep": 17}}

        # **输入10：** "Breaking Bad - 05x12.mkv"
        # **输出10：** {{"ep": 12}}

        # ## 现在，请处理以下输入：

        # **输入：** {}
        # **输出：** 
        # """
        self.prompt_template = \
"""
你是一个专业的文件信息提取助手，专门从视频/字幕文件名中提取集数(episode number)。请严格遵循以下规则：

1. 集数通常是连续的数字，可能出现在以下模式中：
   - "[数字]" 如 [05]
   - "ep数字" 如 ep12
   - "E数字" 如 E15
   - "数字" 如 03
   - "第数字集" 如 第12集
   - "数字话" 如 12话
   - "SxEy"格式中的y部分 如 S01E03 → 3
   - "x数字"中的数字部分 如 05x12 → 12

2. 提取规则优先级：
   a) 首先查找明确的集数标识符(如"ep","E","集","话")
   b) 然后查找方括号中的数字 [数字]
   c) 最后查找独立的连续数字(长于2位优先)

3. 处理要求：
   - 只返回整数(去掉前导零)
   - 无集数信息时返回-1
   - 只输出JSON格式：{{"ep": 数字或-1}}

4. 特别注意：
   - 忽略分辨率(如1080p)、音视频编码等信息
   - 忽略年份等长数字
   - 当文件名中有多个数字时，选择最可能代表集数的那个
   - 数字通常为1-3位数
   - 仅有季号而无集数信息时返回-1
   - 合集/区间是多集合并、无单一集数信息，返回-1

示例：
"[SubsPlease] Jujutsu Kaisen - 23 [1080p]" → {{"ep": 23}}
"One.Piece.1065.mkv" → {{"ep": 1065}}
"Breaking.Bad.S05E12.HEVC" → {{"ep": 12}}
"Movie.Title.2023" → {{"ep": -1}}
"Best.Anime.Ever.S03.1080p" → {{"ep": -1}}
"A E01-04" → {{"ep": -1}}

现在处理以下输入(只输出JSON):

输入：{}
输出：

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
        
    def _parse_response(self, response) -> int:
        """把一次 OpenAI 响应解析成集数；解析失败/截断统一返回 -1。

        不依赖服务端的 json_object / json_schema 约束，全部由 _extract_episode
        自行解析，兼容 thinking model 的推理链泄漏、markdown 包裹、前置散文，
        以及把答案放进 reasoning_content 字段的 provider。
        """
        choice = response.choices[0]
        # thinking 撑爆 max_tokens 时 content 不完整，无法可靠解析
        if choice.finish_reason == "length":
            return -1
        message = choice.message
        episode = _extract_episode(message.content)
        if episode is None:
            # 极少数 provider（DeepSeek/SiliconFlow 协议）把答案塞进 reasoning_content
            reasoning = getattr(message, "reasoning_content", None)
            if isinstance(reasoning, str):
                episode = _extract_episode(reasoning)
        return -1 if episode is None else episode

    def episode_match(self, raw_title: str) -> int:
        prompt = self.prompt_template.format(raw_title)

        try:
            msg = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
                ]
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=msg,
                stream=False,
            )
            episode = self._parse_response(response)

        except Exception as e:
            # 如果API调用失败，返回episode=-1，并打印错误信息
            episode = -1
            print(f"API调用失败: {e}")

        return episode