# feishu-messenger 需求文档

## 概述

为 nanobot agent 提供飞书消息发送能力。通过 CLI 接口调用飞书 Open API，支持发送文本、图片、文件、Markdown 卡片消息。

## 背景

nanobot core Phase 22（飞书 SDK 操作 Skill 化）将原 gateway 中的飞书消息发送逻辑提取为独立 skill。agent 通过 `python3 feishu_messenger.py <command>` 调用，标准输出返回 JSON 结果，标准错误输出错误信息。

## 功能需求

### F1: send-text — 发送文本消息

- 参数：`--to`（接收者 ID）、`--text`（消息内容）、`--app`（应用名，可选）
- 根据 `--to` 前缀自动判断 `open_id`（`ou_`）或 `chat_id`（`oc_`）

### F2: send-image — 发送图片

- 参数：`--to`、`--file`（图片路径）、`--app`
- 先上传图片获取 `image_key`，再发送图片消息

### F3: send-file — 发送文件

- 参数：`--to`、`--file`（文件路径）、`--app`
- 图片格式（jpg/png/gif 等）自动走图片 API
- 音频格式（mp3/wav/opus 等）以 `audio` 类型发送
- 其他格式以 `file` 类型发送
- 支持 doc/xls/ppt/pdf/mp4/opus 等类型映射

### F4: send-card — 发送 Markdown 卡片

- 参数：`--to`、`--content`（直接传内容）或 `--content-file`（从文件读取）、`--app`
- 使用 interactive card 格式，支持飞书 Markdown 语法
- 内容超过 4000 字符时自动按段落分块

## 技术约束

| 约束 | 说明 |
|------|------|
| Python 依赖 | `lark-oapi`（飞书官方 Python SDK） |
| 凭证来源 | `~/.nanobot/config.json` → `channels.feishu[]` |
| 应用选择 | `--app` 参数，默认 `lab`，可选 `ST` |
| 输出格式 | 成功 → stdout JSON；失败 → stderr + 非零退出码 |

## 安全要求

- `appSecret` 仅在进程内使用，**不输出到 stdout**
- 凭证文件路径硬编码为 `~/.nanobot/config.json`，不接受外部传入
