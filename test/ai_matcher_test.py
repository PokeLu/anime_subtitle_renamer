import sys
import os

# 将项目根目录添加到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from matcher.ai_matcher import AIMatcher
from front_end.utils import read_config

config = read_config("config.json")
ai_config = read_config("ai_config.json")
config.update(ai_config)
# test_name = "Suzumiya Haruhi no Yuuutsu (TV 2009). 25; BD_h264_flac"
test_name = "[Nekomoe kissaten] Shoujo Conto All Starlight 20 [BDRip 1080p HEVC-10bit FLAC].TC.ass"

matcher = AIMatcher()
matcher.load_config(config)

print(matcher.episode_match(test_name))