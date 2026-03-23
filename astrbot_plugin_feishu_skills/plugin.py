from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .execution import OperationRouter, pretty_json
from .feishu_client import FeishuAPIError, FeishuOpenAPIClient
from .llm_tools import build_tools
from .models import PluginConfig
from .parsing import split_head_tail
from .skill_registry import SkillRegistry

LOGGER = logging.getLogger(__name__)


def upsert_tools_by_name(existing_tools: list[Any], new_tools: list[Any]) -> None:
    index_by_name: dict[str, int] = {}
    for index, tool in enumerate(existing_tools):
        name = getattr(tool, "name", None)
        if isinstance(name, str) and name:
            index_by_name[name] = index

    for tool in new_tools:
        name = getattr(tool, "name", None)
        if not isinstance(name, str) or not name:
            existing_tools.append(tool)
            continue
        current_index = index_by_name.get(name)
        if current_index is None:
            index_by_name[name] = len(existing_tools)
            existing_tools.append(tool)
            continue
        existing_tools[current_index] = tool


class FeishuSkillsPlugin(Star):
    def __init__(self, context: Context, config: dict[str, Any] | None = None):
        super().__init__(context)
        self.config = PluginConfig.from_mapping(config)
        self.skills_dir = self._resolve_skills_dir(self.config.skills_dir)
        self.registry = SkillRegistry(self.skills_dir)
        self.client = FeishuOpenAPIClient(self.config)
        self.router = OperationRouter(self.config, self.registry, self.client)
        self._debug_tool_registry_state("before_register")
        self._register_llm_tools()
        self._debug_tool_registry_state("after_register")

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

    async def _handle_feishu_skill(self, message: str) -> str:
        if not self.config.enable_skill_lookup:
            return "Skill lookup is disabled by config."

        tail = self._command_tail(message, "feishu_skill")
        action, rest = split_head_tail(tail)
        if not action or action == "help":
            return self._skill_help()

        if action == "list":
            query = rest.strip()
            skills = self.registry.search(query, limit=self.config.max_search_results) if query else self.registry.all()
            skills = skills[: self.config.max_search_results]
            if not skills:
                return f"No skills found under {self.skills_dir}."
            lines = ["Available skills:"]
            for skill in skills:
                desc = (skill.description or skill.title).replace("\n", " ")
                lines.append(f"- {skill.slug}: {desc[:120]}")
            return "\n".join(lines)

        if action == "search":
            if not rest:
                return "Usage: /feishu_skill search <keyword>"
            skills = self.registry.search(rest, limit=self.config.max_search_results)
            if not skills:
                return f"No skill matched {rest}."
            lines = [f"Search results for {rest}:"]
            for skill in skills:
                desc = (skill.description or skill.title).replace("\n", " ")
                lines.append(f"- {skill.slug}: {desc[:120]}")
            return "\n".join(lines)

        if action in {"show", "tips", "zip", "support"}:
            if not rest:
                return f"Usage: /feishu_skill {action} <skill>"
            skill = self.registry.get(rest)
            if not skill:
                suggestions = ", ".join(self.registry.suggest(rest))
                return f"Skill not found: {rest}. Suggestions: {suggestions or 'none'}"
            if action == "show":
                support_text = self.router.skill_support_summary(skill.slug)
                text = self.registry.summarize(skill, max_chars=self.config.max_reply_chars)
                return self._truncate(f"{text}\n\n[support]\n{support_text}")
            if action == "tips":
                return self._truncate(self.registry.tips(skill, max_chars=self.config.max_reply_chars))
            if action == "zip":
                if not skill.zip_path:
                    return f"{skill.slug} has no sibling zip package."
                if self.config.show_zip_path:
                    return f"{skill.slug} zip: {skill.zip_path}"
                return f"{skill.slug} zip exists: {skill.zip_path.name}"
            return self.router.skill_support_summary(skill.slug)

        if action == "call":
            head, json_tail = split_head_tail(rest)
            skill_name = head
            op_name, payload_text = split_head_tail(json_tail)
            if not skill_name or not op_name:
                return "Usage: /feishu_skill call <skill> <action> <json>"
            payload = self._parse_json_payload(payload_text)
            try:
                result = await self.router.execute_skill(skill_name, op_name, payload)
            except (ValueError, FeishuAPIError) as exc:
                return f"Skill call failed: {exc}"
            return self._truncate(pretty_json(result, limit=self.config.max_reply_chars))

        return self._skill_help()

    async def _handle_feishu_run(self, message: str) -> str:
        tail = self._command_tail(message, "feishu_run")
        action, rest = split_head_tail(tail)
        if not action or action == "help":
            return self._run_help()

        if action == "raw":
            payload = self._parse_json_payload(rest)
            try:
                result = await self.router.execute_raw(payload)
            except (ValueError, FeishuAPIError) as exc:
                return f"raw failed: {exc}"
            return self._truncate(pretty_json(result, limit=self.config.max_reply_chars))

        payload = self._parse_json_payload(rest)
        try:
            result = await self.router.execute_operation(action, payload)
        except (ValueError, FeishuAPIError) as exc:
            return f"Operation failed: {exc}"
        return self._truncate(pretty_json(result, limit=self.config.max_reply_chars))

    def _register_llm_tools(self) -> None:
        tools = build_tools(self)
        tool_names = [tool.name for tool in tools]
        add_tools = getattr(self.context, "add_llm_tools", None)
        print(
            "[astrbot_plugin_feishu_skills] register attempt:",
            {
                "tool_names": tool_names,
                "context_type": type(self.context).__name__,
                "has_add_llm_tools": callable(add_tools),
                "has_provider_manager": hasattr(self.context, "provider_manager"),
            },
        )
        if callable(add_tools):
            add_tools(*tools)
            LOGGER.info("Registered Feishu LLM tools via context.add_llm_tools: %s", ", ".join(tool_names))
            print("[astrbot_plugin_feishu_skills] registered via context.add_llm_tools", tool_names)
            return

        provider_manager = getattr(self.context, "provider_manager", None)
        llm_tools = getattr(provider_manager, "llm_tools", None)
        func_list = getattr(llm_tools, "func_list", None)
        if isinstance(func_list, list):
            upsert_tools_by_name(func_list, tools)
            LOGGER.info("Registered Feishu LLM tools via provider_manager.llm_tools: %s", ", ".join(tool_names))
            print("[astrbot_plugin_feishu_skills] registered via provider_manager.llm_tools", tool_names)
            return

        LOGGER.warning("Feishu LLM tools were not registered because no supported AstrBot tool registry was found.")
        print("[astrbot_plugin_feishu_skills] no supported tool registry found")

    def _debug_tool_registry_state(self, stage: str) -> None:
        provider_manager = getattr(self.context, "provider_manager", None)
        llm_tools = getattr(provider_manager, "llm_tools", None)
        func_list = getattr(llm_tools, "func_list", None)
        registered_names: list[str] = []
        if isinstance(func_list, list):
            registered_names = [getattr(tool, "name", "<unnamed>") for tool in func_list]
        debug_info = {
            "stage": stage,
            "context_type": type(self.context).__name__,
            "context_attrs": sorted(name for name in dir(self.context) if not name.startswith("_"))[:80],
            "has_add_llm_tools": callable(getattr(self.context, "add_llm_tools", None)),
            "provider_manager_type": type(provider_manager).__name__ if provider_manager is not None else None,
            "has_llm_tools": llm_tools is not None,
            "func_list_type": type(func_list).__name__ if func_list is not None else None,
            "registered_tool_names": registered_names,
        }
        LOGGER.info("Feishu tool registry debug %s: %s", stage, debug_info)
        print(f"[astrbot_plugin_feishu_skills] debug {stage}: {debug_info}")

    def _tool_registry_report(self) -> str:
        provider_manager = getattr(self.context, "provider_manager", None)
        llm_tools = getattr(provider_manager, "llm_tools", None)
        func_list = getattr(llm_tools, "func_list", None)
        registered_names: list[str] = []
        if isinstance(func_list, list):
            registered_names = [getattr(tool, "name", "<unnamed>") for tool in func_list]
        expected_names = [tool.name for tool in build_tools(self)]
        lines = [
            "Feishu tool registry report:",
            f"- plugin_version: 0.1.9",
            f"- context_type: {type(self.context).__name__}",
            f"- has_add_llm_tools: {callable(getattr(self.context, 'add_llm_tools', None))}",
            f"- provider_manager_type: {type(provider_manager).__name__ if provider_manager is not None else 'None'}",
            f"- has_llm_tools: {llm_tools is not None}",
            f"- func_list_type: {type(func_list).__name__ if func_list is not None else 'None'}",
            f"- expected_tools: {', '.join(expected_names)}",
            f"- registered_tools: {', '.join(registered_names) if registered_names else '(empty)'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _stop_event(event: AstrMessageEvent) -> None:
        stop_event = getattr(event, "stop_event", None)
        if callable(stop_event):
            stop_event()

    async def _run_llm_tool(self, operation: str, payload: dict[str, Any], label: str) -> str:
        try:
            result = await self.router.execute_operation(operation, payload)
        except (ValueError, FeishuAPIError) as exc:
            return f"{label} failed: {exc}"
        return self._tool_result_text(label, result)

    def _resolve_skills_dir(self, configured_path: str) -> Path:
        candidate = Path(configured_path)
        if candidate.is_absolute():
            return candidate
        plugin_root = Path(__file__).resolve().parent.parent
        direct = plugin_root / candidate
        if direct.exists():
            return direct
        fallback = Path.cwd() / candidate
        return fallback

    @staticmethod
    def _command_tail(message: str, command_name: str) -> str:
        message = message.strip()
        prefixes = [f"/{command_name}", command_name]
        for prefix in prefixes:
            if message.startswith(prefix):
                return message[len(prefix) :].strip()
        return message

    @staticmethod
    def _parse_json_payload(text: str) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            return {}
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Expected JSON object payload: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object.")
        return data

    def _truncate(self, text: str) -> str:
        return text[: self.config.max_reply_chars].rstrip()

    def _tool_result_text(self, label: str, result: dict[str, Any]) -> str:
        data = result.get("data") or {}
        important = {
            "document_id": self._pick_first(data, ("data.document.document_id", "data.document_id")),
            "document_url": self._pick_first(data, ("data.document.url", "data.url")),
            "app_token": self._pick_first(data, ("data.app.app_token", "data.app_token")),
            "app_url": self._pick_first(data, ("data.app.url", "data.url")),
            "table_id": self._pick_first(data, ("data.table.table_id", "data.table_id")),
            "table_name": self._pick_first(data, ("data.table.name", "data.table_name")),
            "record_id": self._pick_first(data, ("data.record.record_id", "data.record_id")),
        }
        lines = [f"{label} created successfully.", f"operation: {result.get('operation', '')}"]
        for key, value in important.items():
            if value not in (None, "", []):
                lines.append(f"{key}: {value}")
        lines.append("raw:")
        lines.append(pretty_json(data, limit=max(400, self.config.max_reply_chars - 200)))
        return self._truncate("\n".join(lines))

    @staticmethod
    def _pick_first(data: dict[str, Any], paths: tuple[str, ...]) -> Any:
        for path in paths:
            current: Any = data
            found = True
            for part in path.split("."):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    found = False
                    break
            if found:
                return current
        return None

    def _skill_help(self) -> str:
        return (
            "feishu_skill commands:\n"
            "- /feishu_skill list\n"
            "- /feishu_skill search <keyword>\n"
            "- /feishu_skill show <skill>\n"
            "- /feishu_skill tips <skill>\n"
            "- /feishu_skill zip <skill>\n"
            "- /feishu_skill support <skill>\n"
            "- /feishu_skill call <skill> <action> <json>"
        )

    def _run_help(self) -> str:
        ops = ", ".join(self.router.list_operations())
        return (
            "feishu_run commands:\n"
            f"- mapped ops: {ops}\n"
            "- /feishu_run raw <json>\n"
            "Examples:\n"
            "- /feishu_run doc_create {\"title\":\"Demo doc\"}\n"
            "- /feishu_run bitable_app_create {\"name\":\"Demo app\"}\n"
            "- /feishu_run bitable_table_create {\"app_token\":\"app_xxx\",\"table\":{\"name\":\"Tasks\"}}\n"
            "- /feishu_run bitable_record_create {\"app_token\":\"app_xxx\",\"table_id\":\"tbl_xxx\",\"fields\":{\"Name\":\"hello\"}}"
        )
