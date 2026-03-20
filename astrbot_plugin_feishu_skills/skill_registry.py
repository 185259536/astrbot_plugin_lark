from __future__ import annotations

from pathlib import Path

from .models import SkillDoc
from .parsing import extract_sections, extract_title, parse_front_matter_and_body


class SkillRegistry:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skills: dict[str, SkillDoc] = {}
        self.reload()

    def reload(self) -> None:
        skills: dict[str, SkillDoc] = {}
        if not self.skills_dir.exists():
            self._skills = {}
            return

        for skill_md in sorted(self.skills_dir.glob("*/SKILL.md")):
            slug = skill_md.parent.name
            raw = skill_md.read_text(encoding="utf-8")
            front_matter, body = parse_front_matter_and_body(raw)
            name = front_matter.get("name", slug).strip() or slug
            description = front_matter.get("description", "").strip()
            title = extract_title(body, name)
            zip_path = self.skills_dir / f"{slug}.zip"
            skills[slug] = SkillDoc(
                slug=slug,
                name=name,
                title=title,
                description=description,
                body=body.strip(),
                skill_md_path=skill_md,
                zip_path=zip_path if zip_path.exists() else None,
                sections=extract_sections(body),
            )
        self._skills = skills

    def all(self) -> list[SkillDoc]:
        return list(self._skills.values())

    def get(self, key: str) -> SkillDoc | None:
        normalized = key.strip().lower()
        if normalized in self._skills:
            return self._skills[normalized]
        for skill in self._skills.values():
            if normalized in {skill.name.lower(), skill.slug.lower(), skill.title.lower()}:
                return skill
        return None

    def search(self, query: str, limit: int = 6) -> list[SkillDoc]:
        query = query.strip().lower()
        if not query:
            return self.all()[:limit]

        scored: list[tuple[int, SkillDoc]] = []
        for skill in self._skills.values():
            score = 0
            if query == skill.slug.lower() or query == skill.name.lower():
                score += 100
            if query in skill.slug.lower() or query in skill.name.lower():
                score += 50
            if query in skill.title.lower():
                score += 30
            if query in skill.description.lower():
                score += 20
            if query in skill.body.lower():
                score += 5
            if score:
                scored.append((score, skill))

        scored.sort(key=lambda item: (-item[0], item[1].slug))
        return [skill for _, skill in scored[:limit]]

    def suggest(self, query: str, limit: int = 3) -> list[str]:
        query = query.strip().lower()
        if not query:
            return [skill.slug for skill in self.all()[:limit]]
        matches = self.search(query, limit=limit)
        return [skill.slug for skill in matches]

    def summarize(self, skill: SkillDoc, max_chars: int = 1600) -> str:
        parts = [f"{skill.title} ({skill.slug})"]
        if skill.description:
            parts.append(skill.description)
        for key in ("执行前必读", "快速索引:意图→工具→必填参数", "快速索引：意图→工具→必填参数", "核心约束", "常见错误与排查", "常见错误与排查", "常见问题（faq）"):
            section = self.section_by_hint(skill, key)
            if section:
                parts.append(f"[{key}]\n{section}")
        text = "\n\n".join(parts).strip()
        return text[:max_chars].rstrip()

    def tips(self, skill: SkillDoc, max_chars: int = 1400) -> str:
        parts: list[str] = []
        for hint in ("执行前必读", "核心约束", "常见错误", "faq"):
            section = self.section_by_hint(skill, hint)
            if section:
                parts.append(f"[{hint}]\n{section}")
        if not parts:
            parts.append(skill.description or skill.body[:max_chars])
        return "\n\n".join(parts)[:max_chars].rstrip()

    @staticmethod
    def section_by_hint(skill: SkillDoc, hint: str) -> str:
        normalized_hint = hint.replace(" ", "").replace("：", ":").lower()
        for section_key, section_value in skill.sections.items():
            if normalized_hint in section_key:
                return section_value.strip()
        return ""
