import asyncio
import tempfile
import unittest
from pathlib import Path

from astrbot_plugin_feishu_skills.execution import OperationRouter
from astrbot_plugin_feishu_skills.models import PluginConfig
from astrbot_plugin_feishu_skills.skill_registry import SkillRegistry


class FakeClient:
    def __init__(self):
        self.calls = []

    async def request(self, method, path, *, query=None, json_body=None, extra_headers=None, retry_on_auth_error=True):
        self.calls.append({
            "method": method,
            "path": path,
            "query": query,
            "json_body": json_body,
        })
        return {"ok": True}


class SkillRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        skill_dir = root / "skills" / "feishu-bitable"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: feishu-bitable\n"
            "description: 多维表格技能\n"
            "---\n"
            "# 多维表格\n\n"
            "支持 records.list 和 records.create\n",
            encoding="utf-8",
        )
        self.registry = SkillRegistry(root / "skills")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_loads_known_skill(self) -> None:
        skill = self.registry.get("feishu-bitable")
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertIn("多维表格", skill.body)

    def test_search(self) -> None:
        results = self.registry.search("多维", limit=5)
        self.assertTrue(any(skill.slug == "feishu-bitable" for skill in results))


class OperationRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        skill_dir = root / "skills" / "feishu-bitable"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# feishu-bitable\n", encoding="utf-8")
        self.registry = SkillRegistry(root / "skills")
        self.client = FakeClient()
        self.router = OperationRouter(PluginConfig(), self.registry, self.client)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_support_summary(self) -> None:
        summary = self.router.skill_support_summary("feishu-bitable")
        self.assertIn("apps.create", summary)
        self.assertIn("tables.create", summary)

    def test_create_bitable_app_operation(self) -> None:
        asyncio.run(self.router.execute_operation("bitable_app_create", {"name": "Demo"}))
        self.assertEqual(self.client.calls[-1]["method"], "POST")
        self.assertEqual(self.client.calls[-1]["path"], "/open-apis/bitable/v1/apps")
        self.assertEqual(self.client.calls[-1]["json_body"], {"name": "Demo"})

    def test_create_bitable_table_operation(self) -> None:
        payload = {
            "app_token": "app_xxx",
            "table": {
                "name": "Tasks",
                "fields": [{"field_name": "Name", "type": 1}],
            },
        }
        asyncio.run(self.router.execute_operation("bitable_table_create", payload))
        self.assertEqual(self.client.calls[-1]["method"], "POST")
        self.assertEqual(self.client.calls[-1]["path"], "/open-apis/bitable/v1/apps/app_xxx/tables")
        self.assertEqual(self.client.calls[-1]["json_body"], {"table": payload["table"]})

    def test_create_bitable_record_operation(self) -> None:
        payload = {
            "app_token": "app_xxx",
            "table_id": "tbl_xxx",
            "fields": {"Name": "hello"},
        }
        asyncio.run(self.router.execute_operation("bitable_record_create", payload))
        self.assertEqual(
            self.client.calls[-1]["path"],
            "/open-apis/bitable/v1/apps/app_xxx/tables/tbl_xxx/records",
        )
        self.assertEqual(self.client.calls[-1]["json_body"], {"fields": {"Name": "hello"}})

    def test_disallow_mutation_blocks_create(self) -> None:
        router = OperationRouter(
            PluginConfig(allow_mutation=False),
            self.registry,
            self.client,
        )
        with self.assertRaises(ValueError):
            asyncio.run(router.execute_operation("doc_create", {"title": "Blocked"}))


if __name__ == "__main__":
    unittest.main()
