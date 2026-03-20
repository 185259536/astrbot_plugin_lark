from __future__ import annotations

from typing import Any

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


class _BaseFeishuTool(FunctionTool[AstrAgentContext]):
    name = ""
    description = ""
    parameters: dict[str, Any] = {}

    def __init__(self, plugin: Any):
        self.plugin = plugin

    async def _run(self, operation: str, payload: dict[str, Any], label: str) -> str:
        return await self.plugin._run_llm_tool(operation, payload, label)


class FeishuCreateDocTool(_BaseFeishuTool):
    name = "feishu_create_doc"
    description = "Create a Feishu docx document with the plugin tenant credentials."
    parameters = {
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

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {"title": kwargs["title"]}
        folder_token = str(kwargs.get("folder_token", "") or "").strip()
        if folder_token:
            payload["folder_token"] = folder_token
        return await self._run("doc_create", payload, "document")


class FeishuCreateBitableAppTool(_BaseFeishuTool):
    name = "feishu_create_bitable_app"
    description = "Create a Feishu bitable app with the plugin tenant credentials."
    parameters = {
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

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {"name": kwargs["name"]}
        folder_token = str(kwargs.get("folder_token", "") or "").strip()
        if folder_token:
            payload["folder_token"] = folder_token
        return await self._run("bitable_app_create", payload, "bitable_app")


class FeishuCreateBitableTableTool(_BaseFeishuTool):
    name = "feishu_create_bitable_table"
    description = "Create a table inside an existing Feishu bitable app."
    parameters = {
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


class FeishuCreateBitableRecordTool(_BaseFeishuTool):
    name = "feishu_create_bitable_record"
    description = "Create a record inside an existing Feishu bitable table."
    parameters = {
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

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        payload = {
            "app_token": kwargs["app_token"],
            "table_id": kwargs["table_id"],
            "fields": kwargs["fields"],
        }
        return await self._run("bitable_record_create", payload, "bitable_record")


def build_tools(plugin: Any) -> list[FunctionTool[AstrAgentContext]]:
    return [
        FeishuCreateDocTool(plugin),
        FeishuCreateBitableAppTool(plugin),
        FeishuCreateBitableTableTool(plugin),
        FeishuCreateBitableRecordTool(plugin),
    ]
