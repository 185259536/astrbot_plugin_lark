import importlib
import sys
import types
import unittest


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
        def command(name):
            def decorator(func):
                setattr(func, "_astrbot_command", name)
                return func

            return decorator

    class Context:
        pass

    class Star:
        def __init__(self, context):
            self.context = context

    def register(*args):
        def decorator(cls):
            cls._astrbot_register = args
            return cls

        return decorator

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
    modules["astrbot.api.star"].register = register
    modules["astrbot.core.agent.run_context"].ContextWrapper = ContextWrapper
    modules["astrbot.core.agent.tool"].FunctionTool = FunctionTool
    modules["astrbot.core.agent.tool"].ToolExecResult = str
    modules["astrbot.core.astr_agent_context"].AstrAgentContext = AstrAgentContext

    for name, module in modules.items():
        sys.modules[name] = module


class MainRegistrationTest(unittest.TestCase):
    def test_main_declares_command_handlers(self) -> None:
        install_astrbot_stubs()
        module = importlib.import_module("main")
        module = importlib.reload(module)

        self.assertIn("feishu_skill", module.Main.__dict__)
        self.assertIn("feishu_run", module.Main.__dict__)
        self.assertIn("feishu_tool_debug", module.Main.__dict__)
        self.assertEqual(module.Main.feishu_skill._astrbot_command, "feishu_skill")
        self.assertEqual(module.Main.feishu_run._astrbot_command, "feishu_run")
        self.assertEqual(module.Main.feishu_tool_debug._astrbot_command, "feishu_tool_debug")


if __name__ == "__main__":
    unittest.main()
