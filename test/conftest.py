"""pytest 共享夹具与 sys.path 设置。

替换了旧测试脚本里每个文件都手动 `sys.path.append` 的写法。
"""
import os
import sys

# 将项目根目录加入 sys.path，使 `import matcher` / `from front_end.utils import ...` 可用
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest

# 与 config.yaml.example 中 files.language_ext 保持一致的默认语言映射
DEFAULT_LANGUAGE_EXT = {
    "chs": "简体中文.chi",
    "cht": "繁體中文.chi",
    "dm-chs": "简体中文.chi",
    "dm-cht": "繁體中文.chi",
    "tc": "繁體中文.chi",
    "sc": "简体中文.chi",
    "jptc": "繁日字幕.chi",
    "jpsc": "简日字幕.chi",
}


@pytest.fixture
def default_language_ext():
    """默认的语言后缀映射（深拷贝，避免用例间互相污染）。"""
    return dict(DEFAULT_LANGUAGE_EXT)


@pytest.fixture
def flat_config():
    """内存中的扁平配置 dict（不读写 config.yaml），供纯单元测试隔离使用。"""
    return {
        "match_method": "ab",
        "video_pattern": r"(?:[A-Za-z]{1,2})?\b\d{1,2}\b",
        "video_match_pos": -1,
        "sub_pattern": r"(?:[A-Za-z]{1,2})?\b\d{1,2}\b",
        "sub_match_pos": -1,
        "video_ext": [".mp4", ".mkv"],
        "subtitle_ext": [".ass", ".srt"],
        "language_ext": dict(DEFAULT_LANGUAGE_EXT),
        "video_dir": "",
        "sub_src_dir": "",
        "sub_tar_dir": "",
        "base_url": "",
        "api_key": "",
        "model": "",
        "debug_mode": False,
        "clear_files": False,
    }


@pytest.fixture
def ai_config():
    """读取真实 config.yaml 的配置（仅 @pytest.mark.ai 集成测试使用）。"""
    from front_end.utils import read_config

    return read_config(os.path.join(PROJECT_ROOT, "config.yaml"))
