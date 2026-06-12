"""front_end/utils.py 配置读写层的单元测试：flatten/unflatten、读写往返、api_key 环境变量回退。"""
import os

import pytest
import yaml

from front_end.utils import (
    flatten_config,
    read_config,
    unflatten_config,
    write_config,
)

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "config.yaml.example")


def _load_example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_flatten_unflatten_roundtrip():
    nested = _load_example()
    flat = flatten_config(nested)
    back = unflatten_config(flat)

    for section in ("matching", "files", "ai"):
        assert section in back
    assert back["matching"]["method"] == nested["matching"]["method"]
    assert back["ai"]["base_url"] == nested["ai"]["base_url"]
    assert back["files"]["video_ext"] == nested["files"]["video_ext"]


def test_flatten_produces_expected_flat_keys():
    nested = _load_example()
    flat = flatten_config(nested)

    # 分段 key 被映射为扁平 key
    assert flat["match_method"] == "ab"
    assert flat["video_ext"] == [".mp4", ".mkv"]
    assert flat["base_url"] == nested["ai"]["base_url"]
    # 顶层简单值直接透传
    assert flat["debug_mode"] is True
    assert flat["clear_files"] is False


def test_api_key_env_fallback(monkeypatch):
    """api_key 为空时，回退到 ANIME_AI_API_KEY 环境变量。"""
    nested = {"ai": {"base_url": "u", "api_key": "", "model": "m"}}
    monkeypatch.setenv("ANIME_AI_API_KEY", "env-key")
    flat = flatten_config(nested)
    assert flat["api_key"] == "env-key"


def test_api_key_config_takes_precedence_over_env(monkeypatch):
    """config 中已有 api_key 时，不使用环境变量。"""
    nested = {"ai": {"base_url": "u", "api_key": "from-config", "model": "m"}}
    monkeypatch.setenv("ANIME_AI_API_KEY", "env-key")
    flat = flatten_config(nested)
    assert flat["api_key"] == "from-config"


def test_write_read_roundtrip(tmp_path):
    """write_config 写出的 YAML 能被 read_config 正确读回（扁平结构）。"""
    cfg_file = tmp_path / "roundtrip.yaml"
    flat = {
        "match_method": "raw",
        "video_ext": [".mp4"],
        "base_url": "u",
        "api_key": "k",
        "model": "m",
        "debug_mode": False,
    }
    write_config(str(cfg_file), flat)
    read_back = read_config(str(cfg_file))

    assert read_back["match_method"] == "raw"
    assert read_back["video_ext"] == [".mp4"]
    assert read_back["base_url"] == "u"
    assert read_back["model"] == "m"


def test_read_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_config(str(tmp_path / "nope.yaml"))
