from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PluginConfig:
    app_id: str = ""
    app_secret: str = ""
    brand: str = "feishu"
    skills_dir: str = "skills"
    max_search_results: int = 6
    max_reply_chars: int = 2200
    request_timeout_seconds: float = 20.0
    enable_skill_lookup: bool = True
    enable_doc: bool = True
    enable_bitable: bool = True
    enable_bot_ops: bool = True
    allow_mutation: bool = True
    allow_dangerous_actions: bool = False
    allow_raw_openapi: bool = False
    show_zip_path: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "PluginConfig":
        data = data or {}
        return cls(
            app_id=str(data.get("app_id", "") or "").strip(),
            app_secret=str(data.get("app_secret", "") or "").strip(),
            brand=str(data.get("brand", "feishu") or "feishu").strip(),
            skills_dir=str(data.get("skills_dir", "skills") or "skills").strip(),
            max_search_results=max(1, min(20, int(data.get("max_search_results", 6) or 6))),
            max_reply_chars=max(400, min(8000, int(data.get("max_reply_chars", 2200) or 2200))),
            request_timeout_seconds=float(data.get("request_timeout_seconds", 20) or 20),
            enable_skill_lookup=bool(data.get("enable_skill_lookup", True)),
            enable_doc=bool(data.get("enable_doc", True)),
            enable_bitable=bool(data.get("enable_bitable", True)),
            enable_bot_ops=bool(data.get("enable_bot_ops", True)),
            allow_mutation=bool(data.get("allow_mutation", True)),
            allow_dangerous_actions=bool(data.get("allow_dangerous_actions", False)),
            allow_raw_openapi=bool(data.get("allow_raw_openapi", False)),
            show_zip_path=bool(data.get("show_zip_path", True)),
        )


@dataclass(slots=True)
class SkillDoc:
    slug: str
    name: str
    title: str
    description: str
    body: str
    skill_md_path: Path
    zip_path: Path | None = None
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def searchable_text(self) -> str:
        return "\n".join([
            self.slug,
            self.name,
            self.title,
            self.description,
            self.body,
        ]).lower()


@dataclass(slots=True)
class OperationSpec:
    name: str
    method: str
    path_template: str
    required_fields: tuple[str, ...] = ()
    query_fields: tuple[str, ...] = ()
    mutation: bool = False
    feature_flag: str | None = None
    dangerous: bool = False
    note: str = ""


@dataclass(slots=True)
class SkillExecutionSupport:
    mode: str
    actions: dict[str, str] = field(default_factory=dict)
    note: str = ""
