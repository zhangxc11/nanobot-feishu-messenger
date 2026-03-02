# feishu-messenger 架构文档

## 整体架构

```
CLI 入口 (main)
  ├── argparse 解析命令和参数
  ├── send-text  → cmd_send_text()  → send_message()
  ├── send-image → cmd_send_image() → upload_image() → send_message()
  ├── send-file  → cmd_send_file()  → upload_file()/upload_image() → send_message()
  └── send-card  → cmd_send_card()  → build_card_elements() → send_message()
                                          ↑
                                    feishu_common.py
                                    (create_client / load_credentials)
```

## 模块说明

### feishu_common.py — 凭证管理与客户端创建

| 函数 | 职责 |
|------|------|
| `load_feishu_credentials(app_name)` | 从 `~/.nanobot/config.json` 读取指定应用的 `appId` / `appSecret` |
| `create_client(app_name)` | 创建 `lark_oapi.Client` 实例 |
| `get_tenant_token(app_name)` | 通过 HTTP 获取 `tenant_access_token`（供 SDK 未覆盖的 API 使用） |

设计要点：
- 支持 config 中多应用配置（数组格式），兼容旧版单应用格式
- `lark_oapi` 可选导入，缺失时给出明确错误提示

### feishu_messenger.py — 业务逻辑

**上传函数：**
- `upload_image(client, file_path)` → 返回 `image_key`
- `upload_file(client, file_path)` → 返回 `file_key`，根据扩展名映射 `file_type`

**发送函数：**
- `send_message(client, receive_id, msg_type, content)` → 统一发送入口，自动判断 `receive_id_type`

**卡片构建：**
- `build_card_elements(text)` → 将 Markdown 文本转为 card elements 数组

**CLI 命令：**
- `cmd_send_text` / `cmd_send_image` / `cmd_send_file` / `cmd_send_card`

## 关键设计

### Upload → Send 两步模式

飞书 API 要求先上传媒体文件获取 key，再用 key 发送消息：

```
本地文件 → upload API → image_key / file_key → send message API → 消息送达
```

### Card 分块（4000 字符限制）

飞书 interactive card 的单个 markdown element 有约 4000 字符限制。`build_card_elements()` 按段落边界（`\n\n`）分割，确保每个 element 不超限：

```python
if len(current_chunk) + len(para) + 2 > MAX_ELEMENT_LEN:
    elements.append({"tag": "markdown", "content": current_chunk})
    current_chunk = para
```

### 文件类型自动识别

`send-file` 根据扩展名自动选择发送策略：

| 扩展名类别 | 处理方式 |
|-----------|---------|
| 图片（jpg/png/gif 等） | 转走 `send-image` 流程 |
| 音频（mp3/wav/opus 等） | `msg_type = "audio"` |
| 文档（doc/xls/ppt/pdf） | 映射对应 `file_type` |
| 其他 | `file_type = "stream"` |

## 依赖关系

```
feishu_messenger.py
  ├── feishu_common.py          (本地模块)
  ├── lark-oapi                 (飞书 Python SDK)
  └── ~/.nanobot/config.json    (运行时凭证)
```
