import asyncio
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path


def install_astrbot_stubs() -> None:
    modules = {
        "astrbot": types.ModuleType("astrbot"),
        "astrbot.api": types.ModuleType("astrbot.api"),
        "astrbot.api.event": types.ModuleType("astrbot.api.event"),
        "astrbot.api.star": types.ModuleType("astrbot.api.star"),
        "astrbot.core": types.ModuleType("astrbot.core"),
        "astrbot.core.agent": types.ModuleType("astrbot.core.agent"),
        "astrbot.core.agent.run_context": types.ModuleType("astrbot.core.agent.run_context"),
        "astrbot.core.agent.tool": types.ModuleType("astrbot.core.agent.tool"),
        "astrbot.core.astr_agent_context": types.ModuleType("astrbot.core.astr_agent_context"),
    }

    class AstrMessageEvent:
        pass

    class _Filter:
        @staticmethod
        def command(_name):
            def decorator(func):
                return func

            return decorator

    class Context:
        def __init__(self):
            self.registered_tools = []

        def add_llm_tools(self, *tools):
            self.registered_tools.extend(tools)

    class Star:
        def __init__(self, context):
            self.context = context

    class ContextWrapper:
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    class FunctionTool:
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    class AstrAgentContext:
        pass

    modules["astrbot.api.event"].AstrMessageEvent = AstrMessageEvent
    modules["astrbot.api.event"].filter = _Filter()
    modules["astrbot.api.star"].Context = Context
    modules["astrbot.api.star"].Star = Star
    modules["astrbot.core.agent.run_context"].ContextWrapper = ContextWrapper
    modules["astrbot.core.agent.tool"].FunctionTool = FunctionTool
    modules["astrbot.core.agent.tool"].ToolExecResult = str
    modules["astrbot.core.astr_agent_context"].AstrAgentContext = AstrAgentContext

    for name, module in modules.items():
        sys.modules[name] = module


class FakeEvent:
    def __init__(self, message: str):
        self.message_str = message
        self.stopped = False

    def plain_result(self, text: str) -> str:
        return text

    def stop_event(self) -> None:
        self.stopped = True


class PluginCommandStopTest(unittest.TestCase):
    def setUp(self) -> None:
        install_astrbot_stubs()
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        skill_dir = root / "skills" / "feishu-bitable"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# feishu-bitable\n", encoding="utf-8")

        plugin_module = importlib.import_module("astrbot_plugin_feishu_skills.plugin")
        self.plugin_module = importlib.reload(plugin_module)
        context = sys.modules["astrbot.api.star"].Context()
        self.plugin = self.plugin_module.FeishuSkillsPlugin(context, {"skills_dir": str(root / "skills")})

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_feishu_tool_debug_stops_event_propagation(self) -> None:
        event = FakeEvent("/feishu_tool_debug")

        async def run():
            results = []
            async for item in self.plugin.feishu_tool_debug(event):
                results.append(item)
            return results

        results = asyncio.run(run())
        self.assertTrue(event.stopped)
        self.assertEqual(len(results), 1)
        self.assertIn("Feishu tool registry report:", results[0])


if __name__ == "__main__":
    unittest.main()
