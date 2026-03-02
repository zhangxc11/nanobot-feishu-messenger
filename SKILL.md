---
name: feishu-messenger
description: "飞书消息发送：发送文本、图片、文件、卡片消息到飞书用户或群组。当需要通过飞书发送文件、图片或格式化消息时使用。"
---

# 飞书消息发送 Skill

通过飞书开放平台 API 发送消息。支持文本、图片、文件、Markdown 卡片消息。

## 脚本位置

```
skills/feishu-messenger/scripts/feishu_messenger.py
```

## 命令

### 发送文本消息

```bash
python3 skills/feishu-messenger/scripts/feishu_messenger.py send-text --to ou_xxx --text "消息内容" [--app lab]
```

### 发送图片

```bash
python3 skills/feishu-messenger/scripts/feishu_messenger.py send-image --to ou_xxx --file /path/to/image.png [--app lab]
```

### 发送文件

```bash
python3 skills/feishu-messenger/scripts/feishu_messenger.py send-file --to ou_xxx --file /path/to/file.docx [--app lab]
```

注意：如果文件是图片格式（jpg/png/gif 等），会自动使用图片 API 发送。

### 发送 Markdown 卡片

```bash
# 直接传内容
python3 skills/feishu-messenger/scripts/feishu_messenger.py send-card --to ou_xxx --content "**标题**\n内容" [--app lab]

# 从文件读取
python3 skills/feishu-messenger/scripts/feishu_messenger.py send-card --to ou_xxx --content-file /path/to/content.md [--app lab]
```

## 参数说明

- `--to`: 接收者 ID
  - `ou_xxx`: 用户 open_id（发私聊消息）
  - `oc_xxx`: 群组 chat_id（发群消息）
- `--app`: 飞书应用名（默认 `lab`，可选 `ST`）

## 常用 ID

> 常用收件人 ID 保存在 `~/.nanobot/workspace/memory/MEMORY.md` 中，请从 MEMORY 中查找，不要硬编码在代码或文档中。

## 输出格式

成功时输出 JSON 到 stdout：

```json
{"status": "ok", "type": "file", "file_key": "xxx"}
```

失败时输出错误到 stderr 并以非零状态码退出。

## 鉴权

自动从 `~/.nanobot/config.json` 读取飞书应用凭证。

## 权限要求

飞书应用需开通以下权限：
- `im:message` — 获取与发送单聊、群组消息
- `im:resource` — 上传图片/文件资源

## 依赖

- `lark-oapi` (已安装)
