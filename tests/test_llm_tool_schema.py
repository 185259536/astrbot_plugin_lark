import importlib
import sys
import types
import unittest


def install_astrbot_stubs() -> None:
    modules = {
        "astrbot": types.ModuleType("astrbot"),
        "astrbot.core": types.ModuleType("astrbot.core"),
        "astrbot.core.agent": types.ModuleType("astrbot.core.agent"),
        "astrbot.core.agent.run_context": types.ModuleType("astrbot.core.agent.run_context"),
        "astrbot.core.agent.tool": types.ModuleType("astrbot.core.agent.tool"),
        "astrbot.core.astr_agent_context": types.ModuleType("astrbot.core.astr_agent_context"),
    }

    class ContextWrapper:
        pass

    class FunctionTool:
        @classmethod
        def __class_getitem__(cls, item):
            return cls

    class AstrAgentContext:
        pass

    modules["astrbot.core.agent.run_context"].ContextWrapper = ContextWrapper
    modules["astrbot.core.agent.tool"].FunctionTool = FunctionTool
    modules["astrbot.core.agent.tool"].ToolExecResult = str
    modules["astrbot.core.astr_agent_context"].AstrAgentContext = AstrAgentContext

    for name, module in modules.items():
        sys.modules.setdefault(name, module)


class LLMToolSchemaTest(unittest.TestCase):
    def test_build_tools_exposes_named_schemas(self) -> None:
        install_astrbot_stubs()
        module = importlib.import_module("astrbot_plugin_feishu_skills.llm_tools")

        class FakePlugin:
            async def _run_llm_tool(self, operation, payload, label):
                return f"{label}:{operation}:{payload}"

        tools = module.build_tools(FakePlugin())
        self.assertEqual(
            [tool.name for tool in tools],
            [
                "feishu_create_doc",
                "feishu_create_bitable_app",
                "feishu_create_bitable_table",
                "feishu_create_bitable_record",
            ],
        )
        self.assertEqual(tools[0].parameters["required"], ["title"])
        self.assertEqual(tools[2].parameters["required"], ["app_token", "table_name"])


if __name__ == "__main__":
    unittest.main()
