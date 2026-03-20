from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT_STR = str(PLUGIN_ROOT)
if PLUGIN_ROOT_STR not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT_STR)

from astrbot_plugin_feishu_skills.plugin import FeishuSkillsPlugin

__all__ = ["FeishuSkillsPlugin"]
