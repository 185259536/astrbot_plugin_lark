# AstrBot Feishu Skills Plugin / AstrBot 飞书技能插件

> Version / 当前版本：`0.1.9`

一个面向 AstrBot 的飞书插件，用于查询本地技能文档，并通过插件配置的飞书应用凭证执行受控 OpenAPI 调用。  
An AstrBot plugin for Feishu/Lark that can look up local skill documents and execute controlled OpenAPI calls with the plugin's configured app credentials.

## Overview / 简介

这个仓库提供一个可打包上传到 AstrBot 的插件，主要能力包括：

- 查询本地 `skills/*/SKILL.md`
- 调用受控 Feishu OpenAPI
- 为模型暴露文档、多维表格等行为工具

This repository contains an AstrBot plugin that can:

- search local `skills/*/SKILL.md` files
- call controlled Feishu OpenAPI endpoints
- expose behavior tools for docs and bitable operations

## Features / 功能特性

- `feishu_skill`：查询、展示、提示本地技能文档
- `feishu_run`：执行预定义 OpenAPI 操作
- `feishu_tool_debug`：查看工具注册状态
- Behavior tools：创建文档、多维表格应用、数据表、记录

- `feishu_skill`: search and inspect local skill docs
- `feishu_run`: execute mapped OpenAPI operations
- `feishu_tool_debug`: inspect tool registration state
- Behavior tools: create docs, bitable apps, tables, and records

## Project Structure / 目录结构

```text
astrbot_plugin_feishu_skills/
├── astrbot_plugin_feishu_skills/   # 插件实现 / plugin package
├── tests/                          # 单元测试 / unit tests
├── main.py                         # AstrBot 注册入口 / plugin entry
├── metadata.yaml                   # 插件元数据 / plugin metadata
├── _conf_schema.json               # 配置定义 / config schema
├── README.astrbot.md               # AstrBot 使用说明 / AstrBot-facing docs
└── README.md                       # 仓库首页说明 / repository README
```

## Quick Start / 快速开始

1. 配置飞书应用凭证：`app_id`、`app_secret`
2. 确认 AstrBot 版本不低于 `4.5.1`
3. 打包插件 zip
4. 上传到 AstrBot 并启用
5. 发送 `/feishu_tool_debug` 验证命令是否生效

1. Configure `app_id` and `app_secret`
2. Make sure AstrBot is `>= 4.5.1`
3. Package the plugin as a zip
4. Upload and enable it in AstrBot
5. Send `/feishu_tool_debug` to verify the command works

## Configuration / 配置项

核心配置项：

- `app_id`
- `app_secret`
- `skills_dir`
- `enable_skill_lookup`
- `enable_doc`
- `enable_bitable`
- `enable_bot_ops`
- `allow_mutation`
- `allow_raw_openapi`

Key config fields:

- `app_id`
- `app_secret`
- `skills_dir`
- `enable_skill_lookup`
- `enable_doc`
- `enable_bitable`
- `enable_bot_ops`
- `allow_mutation`
- `allow_raw_openapi`

完整字段定义见 `_conf_schema.json`。  
See `_conf_schema.json` for the full configuration schema.

## Commands & Tools / 命令与工具

常用命令：

- `/feishu_skill list`
- `/feishu_skill search <keyword>`
- `/feishu_skill show <skill>`
- `/feishu_run help`
- `/feishu_tool_debug`
- `/feishu_tool_debug refresh`

Common commands:

- `/feishu_skill list`
- `/feishu_skill search <keyword>`
- `/feishu_skill show <skill>`
- `/feishu_run help`
- `/feishu_tool_debug`
- `/feishu_tool_debug refresh`

行为工具：

- `feishu_create_doc`
- `feishu_create_bitable_app`
- `feishu_create_bitable_table`
- `feishu_create_bitable_record`

Behavior tools:

- `feishu_create_doc`
- `feishu_create_bitable_app`
- `feishu_create_bitable_table`
- `feishu_create_bitable_record`

更详细的命令说明见 `README.astrbot.md`。  
For detailed command docs, see `README.astrbot.md`.

## Packaging / 打包发布

打包时请直接压缩插件内容本身，不要额外包一层父目录：

```bash
zip -r astrbot_plugin_feishu_skills.zip \
  metadata.yaml \
  main.py \
  _conf_schema.json \
  README.md \
  README.astrbot.md \
  requirements.txt \
  astrbot_plugin_feishu_skills
```

Package the plugin contents directly instead of zipping the parent folder:

```bash
zip -r astrbot_plugin_feishu_skills.zip \
  metadata.yaml \
  main.py \
  _conf_schema.json \
  README.md \
  README.astrbot.md \
  requirements.txt \
  astrbot_plugin_feishu_skills
```

## Troubleshooting / 排障建议

- 上传后先确认版本号是否已更新
- 命令无效时优先检查是否加载了新包
- 工具不出现时先看 `/feishu_tool_debug`
- `registered_tools` 为空时尝试 `/feishu_tool_debug refresh`
- 必要时完整重启 AstrBot，而不是只热重载
- 若依赖本地技能查询，确认 `skills/` 目录已一并打包

- Verify the plugin version after every re-upload
- If commands do not work, first confirm the new package is actually loaded
- If tools are missing, check `/feishu_tool_debug`
- If `registered_tools` is empty, try `/feishu_tool_debug refresh`
- Fully restart AstrBot when hot reload is not enough
- If local skill lookup matters, make sure `skills/` is included in the package

## Development / 开发与测试

运行测试：

```bash
python -m unittest
```

Run tests:

```bash
python -m unittest
```

## License / 许可证

MIT
