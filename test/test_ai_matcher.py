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


def test_ai_retry_when_first_returns_minus_one():
    """首次返回 -1 时，会用放宽规则的 prompt 重试一次。"""
    matcher = _make_matcher()
    matcher.client.chat.completions.create.side_effect = [
        _resp('{"ep": -1}'),
        _resp('{"ep": 5}'),
    ]

    assert matcher.episode_match("Anime - 05 [1080p]") == 5
    assert matcher.client.chat.completions.create.call_count == 2


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
