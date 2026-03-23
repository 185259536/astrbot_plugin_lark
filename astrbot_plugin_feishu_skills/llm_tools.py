from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class _BaseFeishuTool(FunctionTool[AstrAgentContext]):
    plugin: Any

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    async def _run(self, operation: str, payload: dict[str, Any], label: str) -> str:
        return await self.plugin._run_llm_tool(operation, payload, label)


@dataclass
class FeishuCreateDocTool(_BaseFeishuTool):
    name: str = "feishu_create_doc"
    description: str = "Create a Feishu docx document with the plugin tenant credentials."
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Document title.",
                },
                "folder_token": {
                    "type": "string",
                    "description": "Optional parent folder token.",
                },
            },
            "required": ["title"],
        }
    )

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {"title": kwargs["title"]}
        folder_token = str(kwargs.get("folder_token", "") or "").strip()
        if folder_token:
            payload["folder_token"] = folder_token
        return await self._run("doc_create", payload, "document")


@dataclass
class FeishuCreateBitableAppTool(_BaseFeishuTool):
    name: str = "feishu_create_bitable_app"
    description: str = "Create a Feishu bitable app with the plugin tenant credentials."
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Bitable app name.",
                },
                "folder_token": {
                    "type": "string",
                    "description": "Optional parent folder token.",
                },
            },
            "required": ["name"],
        }
    )

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {"name": kwargs["name"]}
        folder_token = str(kwargs.get("folder_token", "") or "").strip()
        if folder_token:
            payload["folder_token"] = folder_token
        return await self._run("bitable_app_create", payload, "bitable_app")


@dataclass
class FeishuCreateBitableTableTool(_BaseFeishuTool):
    name: str = "feishu_create_bitable_table"
    description: str = "Create a table inside an existing Feishu bitable app."
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "app_token": {
                    "type": "string",
                    "description": "Target bitable app token.",
                },
                "table_name": {
                    "type": "string",
                    "description": "New table name.",
                },
                "fields": {
                    "type": "array",
                    "description": "Optional list of field definitions in Feishu OpenAPI format.",
                },
                "default_view_name": {
                    "type": "string",
                    "description": "Optional default view name.",
                },
            },
            "required": ["app_token", "table_name"],
        }
    )

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        table: dict[str, Any] = {"name": kwargs["table_name"]}
        fields = kwargs.get("fields")
        if fields:
            table["fields"] = fields
        default_view_name = str(kwargs.get("default_view_name", "") or "").strip()
        if default_view_name:
            table["default_view_name"] = default_view_name
        payload = {"app_token": kwargs["app_token"], "table": table}
        return await self._run("bitable_table_create", payload, "bitable_table")


@dataclass
class FeishuCreateBitableRecordTool(_BaseFeishuTool):
    name: str = "feishu_create_bitable_record"
    description: str = "Create a record inside an existing Feishu bitable table."
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "app_token": {
                    "type": "string",
                    "description": "Target bitable app token.",
                },
                "table_id": {
                    "type": "string",
                    "description": "Target table id.",
                },
                "fields": {
                    "type": "object",
                    "description": "Record fields keyed by field name.",
                },
            },
            "required": ["app_token", "table_id", "fields"],
        }
    )

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {
            "app_token": kwargs["app_token"],
            "table_id": kwargs["table_id"],
            "fields": kwargs["fields"],
        }
        return await self._run("bitable_record_create", payload, "bitable_record")


def build_tools(plugin: Any) -> list[FunctionTool[AstrAgentContext]]:
    return [
        FeishuCreateDocTool(plugin=plugin),
        FeishuCreateBitableAppTool(plugin=plugin),
        FeishuCreateBitableTableTool(plugin=plugin),
        FeishuCreateBitableRecordTool(plugin=plugin),
    ]
