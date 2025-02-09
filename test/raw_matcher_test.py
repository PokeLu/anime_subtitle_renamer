import sys
import os

# 将项目根目录添加到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from matcher.raw_matcher import RawMatcher
from front_end.utils import read_config

config = read_config("config.json")
test_name = "Suzumiya Haruhi no Yuuutsu (TV 2009). 25; BD_h264_flac"

matcher = RawMatcher()
matcher.load_config(config)

print(matcher.episode_match(test_name))