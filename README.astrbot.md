# AstrBot Feishu Skills Plugin

This AstrBot plugin is built from the current repository's `skills/` content.

It provides three groups of capabilities:

- skill lookup over local `SKILL.md` files
- controlled Feishu OpenAPI calls using the plugin's own bot credentials
- AstrBot behavior tools for creating docs and bitable resources

## Commands

- `/feishu_skill list`
- `/feishu_skill search <keyword>`
- `/feishu_skill show <skill>`
- `/feishu_skill tips <skill>`
- `/feishu_skill zip <skill>`
- `/feishu_skill call <skill> <action> <json>`
- `/feishu_run help`
- `/feishu_run <operation> <json>`
- `/feishu_tool_debug`
- `/feishu_tool_debug refresh`

## Behavior Tools

After the plugin is enabled and the AstrBot model supports tool calling, the plugin exposes these behavior tools:

- `feishu_create_doc`
- `feishu_create_bitable_app`
- `feishu_create_bitable_table`
- `feishu_create_bitable_record`

These tools let the model create a doc, create a bitable app, create a table, and insert a record with the plugin's configured tenant credentials.

## Behavior Tool Inputs

- `feishu_create_doc(title, folder_token="")`
- `feishu_create_bitable_app(name, folder_token="")`
- `feishu_create_bitable_table(app_token, table_name, fields=[], default_view_name="")`
- `feishu_create_bitable_record(app_token, table_id, fields={})`

## Examples

```text
/feishu_skill list
/feishu_skill search 多维表格
/feishu_skill show feishu-bitable
/feishu_skill tips feishu-task
/feishu_skill call feishu-bitable records.list {"app_token":"app_xxx","table_id":"tbl_xxx"}
/feishu_run bot_info {}
/feishu_run doc_create {"title":"hello doc"}
/feishu_run bitable_app_create {"name":"hello app"}
/feishu_run bitable_table_create {"app_token":"app_xxx","table":{"name":"Tasks"}}
/feishu_run bitable_record_create {"app_token":"app_xxx","table_id":"tbl_xxx","fields":{"Name":"hello"}}
/feishu_run message_send {"receive_id_type":"chat_id","receive_id":"oc_xxx","msg_type":"text","content":{"text":"hello"}}
/feishu_run raw {"method":"GET","path":"/open-apis/im/v1/chats","query":{"page_size":"20"}}
```

## Notes

- The plugin defaults to tenant access token generated from `app_id` and `app_secret`.
- Behavior tools require AstrBot `>=4.5.1`. The `add_llm_tools` registration API is only available from that version onward.
- Not every skill in this repository can be executed with bot credentials alone.
- Skills such as calendar, task, and user-scoped IM read commonly require user authorization in addition to app authorization.
- `raw` mode is disabled by default.
- The four create actions are mutation operations and require `allow_mutation=true`.
- The LLM behavior tools only appear when AstrBot tool calling is enabled and the selected model supports tool calling.
- Feishu create actions also require the app to have the corresponding document or bitable permissions.

## Troubleshooting Behavior Tools

If the plugin loads successfully but you still cannot see or use the behavior tools, check these items:

- Confirm the plugin version was updated after re-upload. AstrBot may still be using an older cached package if the version did not change.
- Run `/tool ls` in AstrBot and verify these tools appear:
  - `feishu_create_doc`
  - `feishu_create_bitable_app`
  - `feishu_create_bitable_table`
  - `feishu_create_bitable_record`
- Run `/feishu_tool_debug` and confirm `registered_tools` contains the same 4 names.
- If `registered_tools` is empty, run `/feishu_tool_debug refresh` once and then retry `/tool ls`.
- If the tools exist but are disabled, enable them:

```text
/tool on feishu_create_doc
/tool on feishu_create_bitable_app
/tool on feishu_create_bitable_table
/tool on feishu_create_bitable_record
```

- Check the current persona or tool configuration. If the persona's `tools` field is an empty list, AstrBot will not expose any tools to the model.
- Check the current model. The selected model must support tool calling or function calling, otherwise AstrBot cannot invoke the behavior tools automatically.
- Check plugin config values:
  - `enable_doc=true`
  - `enable_bitable=true`
  - `allow_mutation=true`
- If behavior tools still do not appear, restart AstrBot after re-upload instead of only reloading the plugin.

## Packaging for AstrBot

- Zip the plugin contents directly. The zip root must contain `metadata.yaml`, `main.py`, `_conf_schema.json`, `README.astrbot.md`, `requirements.txt`, and `astrbot_plugin_feishu_skills/`.
- Do not zip the parent folder itself, or AstrBot may unpack an extra directory level and fail to find the plugin package.
- Example:

```bash
zip -r astrbot_plugin_feishu_skills.zip \
  metadata.yaml \
  main.py \
  _conf_schema.json \
  README.astrbot.md \
  requirements.txt \
  astrbot_plugin_feishu_skills
```

## Skills Directory

- The default `skills_dir` is `skills`.
- If you want `/feishu_skill` lookup to work inside AstrBot, include a `skills/` directory in the plugin zip or change the plugin config to a path that exists in the AstrBot runtime.
