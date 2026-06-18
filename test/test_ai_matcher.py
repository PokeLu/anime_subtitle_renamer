"""AIMatcher（"ai" 模式）的单元测试 + 能力边界探针。

分两部分：

1. mock 单测（默认运行、离线）
   用 unittest.mock 打桩 OpenAI client，覆盖正常 / retry / 异常 / client 构造路径，
   不依赖网络与额度。

2. @pytest.mark.ai 能力边界探针（opt-in，需 python -m pytest -m ai）
   不是“全部必须通过”的硬性冒烟测试，而是用一组 simple→complex 的真实文件名，
   探测 **当前 config.yaml 所配模型** 的能力边界在哪里：
     - 硬性 assert 的 case：当前模型“稳定答对”的可靠区（3 次探测均正确）。
     - 标记 xfail 的 case：当前模型“稳定答错”的区域，reason 记录具体失败模式，
       xfail 集合本身就是能力边界。日后换更强模型（如 Qwen3-30B）后重跑，
       xfail→xpassed 会提示边界已扩张，需据实更新本文件。

   注意：LLM 输出非确定（默认温度），故“可靠区”只取多次稳定正确的 case；
   其余即便偶发答对也保持 xfail(non-strict)，避免单次抖动让套件变红。
   下面 reason 中标注的失败模式于 2026-06 在免费 Qwen2.5-7B-Instruct 上 3 次稳定复现。
"""
from unittest.mock import MagicMock

import pytest

import matcher.ai_matcher as ai_mod
from matcher.ai_matcher import AIMatcher


def _resp(content: str):
    """构造一个形如 openai ChatCompletion 响应的 mock 对象。"""
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def _make_matcher(model: str = "test-model"):
    """构造一个 AIMatcher，config 与 client 均为可控的 mock（绕过真实联网的 load_config）。"""
    matcher = AIMatcher()
    matcher.config = {"model": model}
    matcher.client = MagicMock()
    return matcher


# ---------------------------------------------------------------------------
# mock 单元测试（默认运行）
# ---------------------------------------------------------------------------
def test_ai_happy_path():
    """一次调用即返回正确集数，不触发 retry。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.return_value = _resp('{"ep": 23}')

    assert matcher.episode_match("[SubsPlease] Jujutsu Kaisen - 23 [1080p]") == 23
    assert matcher.client.chat.completions.create.call_count == 1


def test_ai_returns_minus_one_without_retry():
    """模型返回 -1（无集数）时直接返回 -1，只调用一次（已测得 retry 零收益并移除）。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.return_value = _resp('{"ep": -1}')

    assert matcher.episode_match("Anime - 05 [1080p]") == -1
    assert matcher.client.chat.completions.create.call_count == 1


def test_ai_returns_minus_one_on_api_exception():
    """API 调用抛异常时，episode_match 应吞掉异常并返回 -1。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.side_effect = RuntimeError("API down")

    assert matcher.episode_match("Anime 05") == -1


def test_ai_prompt_contains_filename():
    """发送给模型的 prompt 应包含待匹配的文件名。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.return_value = _resp('{"ep": 7}')

    matcher.episode_match("MyShow - 07")
    sent_messages = matcher.client.chat.completions.create.call_args.kwargs["messages"]
    user_content = " ".join(m["content"] for m in sent_messages if m["role"] == "user")
    assert "MyShow - 07" in user_content


def test_ai_load_config_builds_client(monkeypatch):
    """load_config 用配置中的凭据构造 OpenAI client（mock 掉真实的 OpenAI 构造与 models.list）。"""
    fake = MagicMock()
    monkeypatch.setattr(ai_mod, "OpenAI", lambda **kwargs: fake)

    matcher = AIMatcher()
    matcher.load_config({"api_key": "k", "base_url": "u", "model": "m"})

    assert matcher.client is fake
    assert matcher.config["model"] == "m"
    # load_config 会调用 models.list()（print 一次 + 返回的 f-string 一次），至少被调用过即可
    fake.models.list.assert_called()


# ---------------------------------------------------------------------------
# thinking model 输出归一化：自定义解析（_strip_reasoning / _extract_episode）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("content,expected", [
    ('{"ep": 23}', 23),                                       # 干净 JSON
    ('<think>分析一下...</think>\n{"ep": 23}', 23),           # 配对 <think>...</think>
    ('推理：23 才是集数</think>\n{"ep": 23}', 23),             # 初代 DeepSeek-R1：只有结束标记
    ('只有思考没有答案</think>', None),                         # 只有结束标记、无答案
    ('<think>推理</think>', None),                            # 配对但闭合后无答案
    ('```json\n{"ep": 5}\n```', 5),                            # markdown 代码块
    ('集数应为 12：{"ep": 12}', 12),                            # 前置散文 + JSON
    ('{"reasoning": "...", "ep": 3}', 3),                      # 多余键
    ('{"ep": -1}', -1),                                       # 显式 -1
    ('没有集数信息', None),                                     # 无 JSON
    ('<think>未闭合的思考', None),                              # 只有开始标记（思考被截断）
    (None, None),                                              # content 为 None
])
def test_extract_episode_handles_thinking_noise(content, expected):
    """_extract_episode 应吞掉 thinking 痕迹/包裹/散文，稳健取出 ep（失败转 None）。"""
    assert ai_mod._extract_episode(content) == expected


def test_ai_handles_thinking_model_response():
    """thinking model 把推理链 + markdown 一起塞进 content 时，仍能解析出集数。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.return_value = _resp(
        '<think>文件名里 23 是集数</think>\n```json\n{"ep": 23}\n```'
    )
    assert matcher.episode_match("[SubsPlease] Jujutsu Kaisen - 23 [1080p]") == 23
    assert matcher.client.chat.completions.create.call_count == 1


def test_ai_falls_back_to_reasoning_content():
    """content 为空但 reasoning_content 含答案时，从 reasoning_content 解析。"""
    matcher = _make_matcher()
    resp = MagicMock()
    resp.choices[0].finish_reason = "stop"
    resp.choices[0].message.content = None
    resp.choices[0].message.reasoning_content = '思考后集数是 {"ep": 8}'
    matcher.client.chat.completions.create.return_value = resp

    assert matcher.episode_match("Show - 08") == 8


def test_ai_returns_minus_one_on_length_truncation():
    """finish_reason=length（思考撑爆 max_tokens）时返回 -1，不触发解析异常。"""
    matcher = _make_matcher()
    resp = _resp('<think>思考到一半被截断...')   # content 不完整
    resp.choices[0].finish_reason = "length"
    matcher.client.chat.completions.create.return_value = resp

    assert matcher.episode_match("Show 05") == -1


# ---------------------------------------------------------------------------
# @pytest.mark.ai 能力边界探针（默认跳过；运行：python -m pytest -m ai）
# ---------------------------------------------------------------------------
# (id, 文件名, 正确集数, 难度, 失败原因)
#   失败原因=None  -> 当前模型稳定答对，硬性 assert（可靠区）
#   失败原因非空    -> 当前模型稳定答错，标 xfail 记录边界
_BOUNDARY_CASES = [
    # --- easy：有明确集数标识 ---
    ("jujutsu-dash", "[SubsPlease] Jujutsu Kaisen - 23 [1080p]", 23, "easy", None),
    ("group-bracket", "[Group] Anime Title [05] [1080p]", 5, "easy", None),
    ("anime-dash-bare", "Anime - 12", 12, "easy", "无分辨率括号的裸 dash 集数，retry 误判为 1/-1"),
    ("chinese-episode", "第12话 某标题", 12, "easy", "中文“第N话”标识，模型稳定返回 1"),
    ("ep-marker", "Title EP07 Finale", 7, "easy", "EP 标识，模型输出不稳定（-1/2/22）"),
    # --- medium：季集 / 多括号噪声 ---
    ("aot-SxxExx", "Attack on Titan S04E15 [1080p]", 15, "medium", "SxxExx：模型稳定返回季号 4 而非集号 15"),
    ("breaking-SxxExx-dots", "Breaking.Bad.S05E12.HEVC.x265", 12, "medium", "点分隔 SxxExx，模型误读（1/2/3）"),
    ("bocchi-multi-bracket", "[DMG&VCB-Studio] BOCCHI THE ROCK! [06][Ma10p_1080p][x265_flac]", 6, "medium", None),
    ("word-season-episode", "Show - Season 2 Episode 3", 3, "medium", "单词 Season/Episode，模型稳定返回 33"),
    ("e-marker-noise", "Title E15 [1080p] [HEVC]", 15, "medium", "E 标识，模型稳定返回 1"),
    # --- hard：歧义 / 大集数 / 无集数 / 合集 ---
    ("onepiece-large-dots", "One.Piece.1065.mkv", 1065, "hard", "点分隔大集数：模型稳定截断为 65"),
    ("nekomoe-bare-20", "[Nekomoe kissaten] Shoujo Conto All Starlight 20 [BDRip 1080p HEVC-10bit FLAC]", 20, "hard", "空格裸数字（ab 模式亦失败），AI 模式同样失败"),
    ("movie-year", "Movie.Title.2023", -1, "hard", "年份被 retry 当成集数（2/3）"),
    ("year-and-episode-brackets", "[2024] Some Anime [12] [1080p]", 12, "hard", "年份括号+集数括号并存，模型混淆（22/2）"),
    ("season-only", "Best.Anime.Ever.S03.1080p", -1, "hard", "仅有季号无集数，模型返回 3"),
    ("episode-range", "A E01-04", -1, "hard", "合集区间 E01-04（README 标注不支持），模型返回 4"),
    ("xNN-format", "Friends - 05x12 - The One", 12, "hard", "05x12 格式，模型输出不稳定（22/-1/-2）"),
    ("three-digit-ep", "Naruto Shippuden - 456 [720p]", 456, "hard", "三位集数被稳定截断为 46"),
]


def _boundary_params():
    params = []
    for cid, name, expected, difficulty, reason in _BOUNDARY_CASES:
        marks = (pytest.mark.xfail(reason=f"[{difficulty}] 当前模型能力边界外：{reason}"),) if reason else ()
        params.append(pytest.param(name, expected, marks=marks, id=f"{difficulty}-{cid}"))
    return params


@pytest.mark.ai
@pytest.mark.parametrize("raw_title, expected", _boundary_params())
def test_ai_capability_boundary(raw_title, expected, ai_config):
    """能力边界探针：对 config.yaml 中配置的模型，逐 case 断言“语义正确集数”。

    通过 = 模型可靠区；xfail = 能力边界外（见 reason）；偶发 xpassed = 该 case 有概率答对。
    """
    matcher = AIMatcher()
    matcher.load_config(ai_config)
    assert matcher.episode_match(raw_title) == expected
