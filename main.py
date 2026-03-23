from pathlib import Path
import sys

from astrbot.api.event import AstrMessageEvent, filter
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
    "0.1.9",
)
class Main(_FeishuSkillsPlugin):
    @filter.command("feishu_skill")
    async def feishu_skill(self, event: AstrMessageEvent):
        self._stop_event(event)
        yield event.plain_result(await self._handle_feishu_skill(event.message_str))

    @filter.command("feishu_run")
    async def feishu_run(self, event: AstrMessageEvent):
        self._stop_event(event)
        yield event.plain_result(await self._handle_feishu_run(event.message_str))

    @filter.command("feishu_tool_debug")
    async def feishu_tool_debug(self, event: AstrMessageEvent):
        self._stop_event(event)
        tail = self._command_tail(event.message_str, "feishu_tool_debug")
        if tail == "refresh":
            self._register_llm_tools()
            self._debug_tool_registry_state("manual_refresh")
        yield event.plain_result(self._tool_registry_report())


FeishuSkillsPlugin = Main

__all__ = ["Main", "FeishuSkillsPlugin"]
