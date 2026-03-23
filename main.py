from pathlib import Path
import sys

from astrbot.api.star import register

PLUGIN_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT_STR = str(PLUGIN_ROOT)
if PLUGIN_ROOT_STR not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT_STR)

from astrbot_plugin_feishu_skills.plugin import FeishuSkillsPlugin as _FeishuSkillsPlugin


@register(
    "astrbot_plugin_feishu_skills",
    "OpenAI",
    "Lookup local Feishu skill docs and call controlled Feishu OpenAPI with bot credentials.",
    "0.1.6",
)
class Main(_FeishuSkillsPlugin):
    pass


FeishuSkillsPlugin = Main

__all__ = ["Main", "FeishuSkillsPlugin"]
