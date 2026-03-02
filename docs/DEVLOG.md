# feishu-messenger 开发日志

## Phase 1: 初始实现 ✅

> 来源：nanobot core Phase 22 — 飞书 SDK 操作 Skill 化
> 将 gateway 中的飞书消息发送逻辑提取为独立 skill。

### T1.1: feishu_common.py 公共模块 ✅

- 实现 `load_feishu_credentials()` — 从 config.json 加载应用凭证
- 实现 `create_client()` — 创建 lark_oapi.Client
- 实现 `get_tenant_token()` — 获取 tenant_access_token
- 支持多应用配置，兼容旧版单应用格式

### T1.2: send-text / send-image / send-file 命令 ✅

- `send-text`: 文本消息发送，自动判断 open_id / chat_id
- `send-image`: 上传图片 → 获取 image_key → 发送图片消息
- `send-file`: 上传文件 → 获取 file_key → 发送文件/音频消息
- 文件类型自动识别：图片走 image API，音频标记为 audio，文档映射 file_type

### T1.3: send-card 命令 ✅

- 支持 `--content` 直接传入和 `--content-file` 从文件读取
- 使用 interactive card 格式，支持飞书 Markdown 语法
- 实现 `build_card_elements()` 自动分块（4000 字符限制）

### T1.4: SKILL.md 编写 ✅

- 完成 skill 说明文档，包含所有命令用法、参数说明、常用 ID
- 定义输出格式规范（stdout JSON / stderr 错误）
