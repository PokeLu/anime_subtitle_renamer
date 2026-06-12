import os
import json
import yaml

DEFAULT_CONFIG_FILE = "config.yaml"
LEGACY_CONFIG_FILE = "config.json"
LEGACY_AI_CONFIG_FILE = "ai_config.json"

# 扁平 key -> (YAML 分段, 子 key) 的映射表
SECTION_MAP = {
    # matching 分段
    "match_method":    ("matching", "method"),
    "video_pattern":   ("matching", "video_pattern"),
    "video_match_pos": ("matching", "video_match_pos"),
    "sub_pattern":     ("matching", "sub_pattern"),
    "sub_match_pos":   ("matching", "sub_match_pos"),
    # files 分段
    "video_ext":       ("files", "video_ext"),
    "subtitle_ext":    ("files", "subtitle_ext"),
    "language_ext":    ("files", "language_ext"),
    "video_dir":       ("files", "video_dir"),
    "sub_src_dir":     ("files", "sub_src_dir"),
    "sub_tar_dir":     ("files", "sub_tar_dir"),
    # ai 分段
    "base_url":        ("ai", "base_url"),
    "api_key":         ("ai", "api_key"),
    "model":           ("ai", "model"),
}


def _reverse_lookup(section: str, sub_key: str) -> str:
    """根据 (section, sub_key) 反查扁平 key"""
    for flat_key, (s, k) in SECTION_MAP.items():
        if s == section and k == sub_key:
            return flat_key
    return sub_key


def flatten_config(nested: dict) -> dict:
    """
    将嵌套的 YAML 配置 dict 展平为扁平 dict，兼容所有 matcher 接口。

    输入:  {"matching": {"method": "ab", ...}, "files": {...}, "ai": {...}, "debug_mode": true}
    输出:  {"match_method": "ab", "video_ext": [...], ..., "debug_mode": true}
    """
    flat = {}
    for section_key, section_dict in nested.items():
        if isinstance(section_dict, dict) and section_key in ("matching", "files", "ai"):
            for sub_key, value in section_dict.items():
                flat_key = _reverse_lookup(section_key, sub_key)
                flat[flat_key] = value
        else:
            # 顶层简单值（debug_mode, clear_files）直接透传
            flat[section_key] = section_dict

    # api_key 环境变量回退
    if not flat.get("api_key"):
        flat["api_key"] = os.environ.get("ANIME_AI_API_KEY", "")

    return flat


def unflatten_config(flat: dict) -> dict:
    """
    将扁平 dict 转换回嵌套的 YAML 结构。
    flatten_config 的逆操作。
    """
    nested = {}
    for flat_key, value in flat.items():
        if flat_key in SECTION_MAP:
            section, sub_key = SECTION_MAP[flat_key]
            if section not in nested:
                nested[section] = {}
            nested[section][sub_key] = value
        else:
            nested[flat_key] = value
    return nested


def _migrate_json_to_yaml(target_file: str = DEFAULT_CONFIG_FILE):
    """
    一次性迁移：读取旧的 config.json + ai_config.json，
    合并后写为单个 config.yaml。
    """
    with open(LEGACY_CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)

    flat = dict(config)

    if os.path.exists(LEGACY_AI_CONFIG_FILE):
        with open(LEGACY_AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
            ai_config = json.load(f)
        flat.update(ai_config)

    write_config(target_file, flat)
    print(f"已将旧 JSON 配置迁移至 {target_file}")


# 读取配置文件
def read_config(config_file: str = DEFAULT_CONFIG_FILE) -> dict:
    """
    读取 YAML 配置文件并返回扁平 dict（兼容现有 matcher 接口）。
    若 YAML 文件不存在但旧 JSON 文件存在，则自动迁移。
    """
    if not os.path.exists(config_file):
        if os.path.exists(LEGACY_CONFIG_FILE):
            _migrate_json_to_yaml(config_file)
        else:
            raise FileNotFoundError(f"配置文件未找到: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as file:
        nested = yaml.safe_load(file)

    if nested is None:
        nested = {}

    return flatten_config(nested)


# 写入配置文件
def write_config(config_file: str, config: dict):
    """
    将扁平 dict 转换为嵌套结构后写入 YAML 文件。
    """
    nested = unflatten_config(config)
    with open(config_file, 'w', encoding='utf-8') as file:
        yaml.dump(nested, file, default_flow_style=False, allow_unicode=True, sort_keys=False)


# 更新配置文件
def update_config(config_file: str, **kwargs):
    """
    动态更新配置文件中的参数。

    读取配置文件，用传入的参数更新后写回。

    参数:
        config_file (str): 配置文件的路径。
        **kwargs: 需要更新的配置项及其新值。
    """
    config = read_config(config_file)
    config.update(kwargs)
    write_config(config_file, config)


# 获取更新后的配置
def get_updated_config(config: dict, **kwargs):
    """
    在内存中更新配置 dict，不进行文件 I/O。

    参数:
        config: 配置字典。
        **kwargs: 需要更新的配置项。

    返回:
        更新后的配置字典。
    """
    config.update(kwargs)
    return config
