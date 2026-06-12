"""AIMatcher（"ai" 模式）的单元测试。

- 默认（不联网）的用例：用 unittest.mock 打桩 OpenAI client，覆盖正常/retry/异常路径。
- @pytest.mark.ai 标记的用例：真实调用 config.yaml 中配置的大模型 API（联网、慢、消耗额度），
  默认运行（python -m pytest）会被跳过，需 python -m pytest -m ai 显式开启。
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
# 以下为真实调用大模型 API 的集成测试，默认跳过。运行：python -m pytest -m ai
# ---------------------------------------------------------------------------
@pytest.mark.ai
def test_ai_integration_real_api(ai_config):
    """对 config.yaml 中配置的模型做端到端冒烟测试：配置加载、client 构造、
    API 可达、JSON 解析、集数正确返回。

    说明：免费 7B 基准模型较弱，且 AIMatcher 的 retry 会在首次返回 -1 时放宽规则，
    容易把文件名里的任意数字（年份等）甚至凭空幻觉成集数，导致 -1 几乎不可达。
    因此本冒烟测试只断言“首次调用即命中”的正向提取用例（不触发 retry，最稳定）；
    -1 / retry / 异常等路径由上面的 mock 单元测试充分覆盖。
    """
    matcher = AIMatcher()
    matcher.load_config(ai_config)

    assert matcher.episode_match("[SubsPlease] Jujutsu Kaisen - 23 [1080p]") == 23
