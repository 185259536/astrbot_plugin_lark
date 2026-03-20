from __future__ import annotations

import json
from typing import Any

from .feishu_client import FeishuOpenAPIClient
from .models import OperationSpec, PluginConfig, SkillExecutionSupport
from .skill_registry import SkillRegistry


class OperationRouter:
    def __init__(self, config: PluginConfig, registry: SkillRegistry, client: FeishuOpenAPIClient):
        self.config = config
        self.registry = registry
        self.client = client
        self.operations = self._build_operations()
        self.skill_support = self._build_skill_support()

    def _build_operations(self) -> dict[str, OperationSpec]:
        return {
            "bot_info": OperationSpec(
                name="bot_info",
                method="GET",
                path_template="/open-apis/bot/v3/info/",
                feature_flag="enable_bot_ops",
                note="Fetch bot identity using tenant access token.",
            ),
            "chat_list": OperationSpec(
                name="chat_list",
                method="GET",
                path_template="/open-apis/im/v1/chats",
                feature_flag="enable_bot_ops",
                query_fields=("page_size", "page_token", "sort_type", "user_id_type"),
            ),
            "message_send": OperationSpec(
                name="message_send",
                method="POST",
                path_template="/open-apis/im/v1/messages",
                required_fields=("receive_id_type", "receive_id", "msg_type", "content"),
                query_fields=("receive_id_type",),
                mutation=True,
                feature_flag="enable_bot_ops",
                note="Send a message with bot credentials.",
            ),
            "doc_create": OperationSpec(
                name="doc_create",
                method="POST",
                path_template="/open-apis/docx/v1/documents",
                required_fields=("title",),
                mutation=True,
                feature_flag="enable_doc",
                note="Create a docx document. This is a raw OpenAPI call, not the higher-level MCP markdown create-doc tool.",
            ),
            "bitable_app_create": OperationSpec(
                name="bitable_app_create",
                method="POST",
                path_template="/open-apis/bitable/v1/apps",
                required_fields=("name",),
                mutation=True,
                feature_flag="enable_bitable",
                note="Create a new bitable app.",
            ),
            "bitable_table_create": OperationSpec(
                name="bitable_table_create",
                method="POST",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables",
                required_fields=("app_token", "table"),
                mutation=True,
                feature_flag="enable_bitable",
                note="Create a table in a bitable app.",
            ),
            "doc_get": OperationSpec(
                name="doc_get",
                method="GET",
                path_template="/open-apis/docx/v1/documents/{document_id}",
                required_fields=("document_id",),
                feature_flag="enable_doc",
            ),
            "bitable_fields_list": OperationSpec(
                name="bitable_fields_list",
                method="GET",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                required_fields=("app_token", "table_id"),
                feature_flag="enable_bitable",
            ),
            "bitable_records_list": OperationSpec(
                name="bitable_records_list",
                method="GET",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                required_fields=("app_token", "table_id"),
                query_fields=("page_size", "page_token", "view_id", "field_names", "sort", "filter", "automatic_fields"),
                feature_flag="enable_bitable",
            ),
            "bitable_record_create": OperationSpec(
                name="bitable_record_create",
                method="POST",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                required_fields=("app_token", "table_id", "fields"),
                mutation=True,
                feature_flag="enable_bitable",
            ),
            "bitable_records_batch_create": OperationSpec(
                name="bitable_records_batch_create",
                method="POST",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                required_fields=("app_token", "table_id", "records"),
                mutation=True,
                feature_flag="enable_bitable",
            ),
            "bitable_record_update": OperationSpec(
                name="bitable_record_update",
                method="PUT",
                path_template="/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
                required_fields=("app_token", "table_id", "record_id", "fields"),
                mutation=True,
                feature_flag="enable_bitable",
            ),
        }

    def _build_skill_support(self) -> dict[str, SkillExecutionSupport]:
        return {
            "feishu-bitable": SkillExecutionSupport(
                mode="tenant_supported",
                actions={
                    "apps.create": "bitable_app_create",
                    "tables.create": "bitable_table_create",
                    "fields.list": "bitable_fields_list",
                    "records.list": "bitable_records_list",
                    "records.create": "bitable_record_create",
                    "records.batch_create": "bitable_records_batch_create",
                    "records.update": "bitable_record_update",
                },
                note="This skill maps cleanly to tenant-token OpenAPI calls.",
            ),
            "feishu-create-doc": SkillExecutionSupport(
                mode="partial_tenant_supported",
                actions={"create": "doc_create"},
                note="This plugin exposes raw doc create with bot credentials. It does not reproduce MCP markdown rendering.",
            ),
            "feishu-fetch-doc": SkillExecutionSupport(
                mode="partial_tenant_supported",
                actions={"get": "doc_get"},
                note="This plugin fetches raw doc metadata via OpenAPI. It does not expand the full Markdown conversion flow.",
            ),
            "feishu-calendar": SkillExecutionSupport(
                mode="user_token_recommended",
                note="Calendar operations in this repository are documented around user identity. This plugin defaults to bot credentials, so calendar is not mapped in v1.",
            ),
            "feishu-task": SkillExecutionSupport(
                mode="user_token_recommended",
                note="Task operations in this repository commonly depend on user access token semantics. Not mapped in v1.",
            ),
            "feishu-im-read": SkillExecutionSupport(
                mode="user_token_recommended",
                note="The IM read skill here is explicitly user-scoped. Not mapped in v1 tenant mode.",
            ),
            "feishu-update-doc": SkillExecutionSupport(
                mode="unsupported_in_v1",
                note="The update-doc skill in this repo targets MCP semantics rather than a single raw OpenAPI endpoint.",
            ),
            "feishu-troubleshoot": SkillExecutionSupport(
                mode="lookup_only",
                note="Troubleshooting content is available for lookup but has no API execution mapping.",
            ),
            "feishu-channel-rules": SkillExecutionSupport(
                mode="lookup_only",
                note="Channel rules are documentation-only.",
            ),
        }

    def list_operations(self) -> list[str]:
        return sorted(self.operations)

    def skill_support_summary(self, skill_name: str) -> str:
        support = self.skill_support.get(skill_name)
        if not support:
            return "No execution metadata yet. You can still inspect the skill document."
        if not support.actions:
            return f"mode={support.mode}; {support.note}".strip()
        mapped = ", ".join(f"{k}->{v}" for k, v in sorted(support.actions.items()))
        return f"mode={support.mode}; actions: {mapped}. {support.note}".strip()

    async def execute_skill(self, skill_name: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        support = self.skill_support.get(skill_name)
        if not support:
            raise ValueError(f"Skill {skill_name} has no execution metadata.")
        operation_name = support.actions.get(action)
        if not operation_name:
            raise ValueError(f"Skill {skill_name} action {action} is not available in tenant mode. {support.note}")
        return await self.execute_operation(operation_name, payload)

    async def execute_operation(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        spec = self.operations.get(name)
        if not spec:
            raise ValueError(f"Unknown operation: {name}")
        self._assert_enabled(spec)
        self._assert_payload(spec, payload)

        path_values = {field: payload[field] for field in spec.required_fields if f"{{{field}}}" in spec.path_template}
        path = spec.path_template.format(**path_values)
        query = self._extract_query(spec, payload)
        body = self._extract_body(spec, payload)
        data = await self.client.request(spec.method, path, query=query, json_body=body)
        return {
            "operation": name,
            "path": path,
            "query": query,
            "note": spec.note,
            "data": data,
        }

    async def execute_raw(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.allow_raw_openapi:
            raise ValueError("Raw OpenAPI is disabled. Enable allow_raw_openapi in plugin config first.")
        method = str(payload.get("method", "GET") or "GET").upper()
        path = str(payload.get("path", "") or "").strip()
        if not path:
            raise ValueError("raw requires path")
        if not path.startswith("/open-apis/"):
            raise ValueError("raw path must start with /open-apis/")
        query = payload.get("query") or None
        body = payload.get("body") if "body" in payload else payload.get("json")
        data = await self.client.request(method, path, query=query, json_body=body)
        return {"operation": "raw", "path": path, "query": query, "data": data}

    def _assert_enabled(self, spec: OperationSpec) -> None:
        if spec.feature_flag and not getattr(self.config, spec.feature_flag):
            raise ValueError(f"Operation {spec.name} is disabled by config flag {spec.feature_flag}.")
        if spec.mutation and not self.config.allow_mutation:
            raise ValueError(f"Operation {spec.name} is blocked because allow_mutation=false.")
        if spec.dangerous and not self.config.allow_dangerous_actions:
            raise ValueError(f"Operation {spec.name} is blocked because allow_dangerous_actions=false.")

    @staticmethod
    def _assert_payload(spec: OperationSpec, payload: dict[str, Any]) -> None:
        missing = [field for field in spec.required_fields if field not in payload]
        if missing:
            raise ValueError(f"Missing required fields for {spec.name}: {', '.join(missing)}")

    @staticmethod
    def _extract_query(spec: OperationSpec, payload: dict[str, Any]) -> dict[str, Any] | None:
        query: dict[str, Any] = {}
        for field in spec.query_fields:
            if field in payload:
                value = payload[field]
                if isinstance(value, (dict, list)):
                    query[field] = json.dumps(value, ensure_ascii=False)
                else:
                    query[field] = value
        return query or None

    @staticmethod
    def _extract_body(spec: OperationSpec, payload: dict[str, Any]) -> dict[str, Any] | None:
        if spec.method.upper() == "GET":
            return None
        excluded = set(spec.query_fields)
        excluded.update(field for field in spec.required_fields if f"{{{field}}}" in spec.path_template)
        body = {key: value for key, value in payload.items() if key not in excluded}
        return body or None


def pretty_json(data: Any, limit: int = 1800) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n..."
