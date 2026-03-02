#!/usr/bin/env python3
"""飞书消息发送 CLI — nanobot feishu-messenger skill

通过飞书 Open API 发送文本、图片、文件消息。
从 ~/.nanobot/config.json 自动加载飞书应用凭证。

用法:
  python3 feishu_messenger.py send-text --to ou_xxx --text "消息内容" [--app lab]
  python3 feishu_messenger.py send-image --to ou_xxx --file /path/to/image.png [--app lab]
  python3 feishu_messenger.py send-file --to ou_xxx --file /path/to/file.docx [--app lab]
  python3 feishu_messenger.py send-card --to ou_xxx --content "Markdown内容" [--app lab]

--to 参数: open_id (ou_xxx) 或 chat_id (oc_xxx)

安全说明:
  - appSecret 仅在此脚本进程内使用，不输出到 stdout
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add script dir to path for feishu_common
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feishu_common import create_client, LARK_AVAILABLE

if LARK_AVAILABLE:
    from lark_oapi.api.im.v1 import (
        CreateFileRequest,
        CreateFileRequestBody,
        CreateImageRequest,
        CreateImageRequestBody,
        CreateMessageRequest,
        CreateMessageRequestBody,
    )

# ── Constants ─────────────────────────────────────────────────────────

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".flac"}
FILE_TYPE_MAP = {
    ".opus": "opus", ".mp4": "mp4", ".pdf": "pdf",
    ".doc": "doc", ".docx": "doc", ".xls": "xls",
    ".xlsx": "xls", ".ppt": "ppt", ".pptx": "ppt",
}


# ── Upload functions ─────────────────────────────────────────────────

def upload_image(client, file_path: str) -> str | None:
    """Upload an image to Feishu and return the image_key."""
    try:
        with open(file_path, "rb") as f:
            request = CreateImageRequest.builder() \
                .request_body(
                    CreateImageRequestBody.builder()
                    .image_type("message")
                    .image(f)
                    .build()
                ).build()
            response = client.im.v1.image.create(request)
            if response.success():
                return response.data.image_key
            else:
                print(f"ERROR: Failed to upload image: code={response.code}, msg={response.msg}",
                      file=sys.stderr)
                return None
    except Exception as e:
        print(f"ERROR: Exception uploading image: {e}", file=sys.stderr)
        return None


def upload_file(client, file_path: str) -> str | None:
    """Upload a file to Feishu and return the file_key."""
    ext = os.path.splitext(file_path)[1].lower()
    file_type = FILE_TYPE_MAP.get(ext, "stream")
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            request = CreateFileRequest.builder() \
                .request_body(
                    CreateFileRequestBody.builder()
                    .file_type(file_type)
                    .file_name(file_name)
                    .file(f)
                    .build()
                ).build()
            response = client.im.v1.file.create(request)
            if response.success():
                return response.data.file_key
            else:
                print(f"ERROR: Failed to upload file: code={response.code}, msg={response.msg}",
                      file=sys.stderr)
                return None
    except Exception as e:
        print(f"ERROR: Exception uploading file: {e}", file=sys.stderr)
        return None


# ── Send functions ───────────────────────────────────────────────────

def send_message(client, receive_id: str, msg_type: str, content: str) -> bool:
    """Send a single message (text/image/file/interactive)."""
    receive_id_type = "chat_id" if receive_id.startswith("oc_") else "open_id"
    try:
        request = CreateMessageRequest.builder() \
            .receive_id_type(receive_id_type) \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(receive_id)
                .msg_type(msg_type)
                .content(content)
                .build()
            ).build()
        response = client.im.v1.message.create(request)
        if response.success():
            return True
        else:
            print(f"ERROR: Failed to send message: code={response.code}, msg={response.msg}",
                  file=sys.stderr)
            return False
    except Exception as e:
        print(f"ERROR: Exception sending message: {e}", file=sys.stderr)
        return False


def build_card_elements(text: str) -> list[dict]:
    """Build interactive card elements from markdown text.

    Splits text into chunks of ~4000 chars (card element limit) and creates
    markdown elements for each chunk.
    """
    MAX_ELEMENT_LEN = 4000
    elements = []

    if len(text) <= MAX_ELEMENT_LEN:
        elements.append({"tag": "markdown", "content": text})
    else:
        # Split on paragraph boundaries
        paragraphs = text.split("\n\n")
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 > MAX_ELEMENT_LEN:
                if current_chunk:
                    elements.append({"tag": "markdown", "content": current_chunk.strip()})
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        if current_chunk:
            elements.append({"tag": "markdown", "content": current_chunk.strip()})

    return elements


# ── CLI commands ─────────────────────────────────────────────────────

def cmd_send_text(args):
    """Send a text message."""
    client = create_client(args.app)
    content = json.dumps({"text": args.text}, ensure_ascii=False)
    ok = send_message(client, args.to, "text", content)
    if ok:
        print(json.dumps({"status": "ok", "type": "text"}))
    else:
        sys.exit(1)


def cmd_send_image(args):
    """Send an image."""
    client = create_client(args.app)

    if not os.path.isfile(args.file):
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    image_key = upload_image(client, args.file)
    if not image_key:
        sys.exit(1)

    content = json.dumps({"image_key": image_key}, ensure_ascii=False)
    ok = send_message(client, args.to, "image", content)
    if ok:
        print(json.dumps({"status": "ok", "type": "image", "image_key": image_key}))
    else:
        sys.exit(1)


def cmd_send_file(args):
    """Send a file."""
    client = create_client(args.app)

    if not os.path.isfile(args.file):
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(args.file)[1].lower()
    if ext in IMAGE_EXTS:
        # Use image API for image files
        return cmd_send_image(args)

    file_key = upload_file(client, args.file)
    if not file_key:
        sys.exit(1)

    media_type = "audio" if ext in AUDIO_EXTS else "file"
    content = json.dumps({"file_key": file_key}, ensure_ascii=False)
    ok = send_message(client, args.to, media_type, content)
    if ok:
        print(json.dumps({"status": "ok", "type": media_type, "file_key": file_key}))
    else:
        sys.exit(1)


def cmd_send_card(args):
    """Send an interactive card (markdown)."""
    client = create_client(args.app)

    text = args.content
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            text = f.read()

    if not text:
        print("ERROR: No content provided", file=sys.stderr)
        sys.exit(1)

    card = {
        "config": {"wide_screen_mode": True},
        "elements": build_card_elements(text),
    }
    content = json.dumps(card, ensure_ascii=False)
    ok = send_message(client, args.to, "interactive", content)
    if ok:
        print(json.dumps({"status": "ok", "type": "interactive"}))
    else:
        sys.exit(1)


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Feishu message sender")
    parser.add_argument("--app", default="lab", help="Feishu app name in config (default: lab)")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # send-text
    p_text = subparsers.add_parser("send-text", help="Send a text message")
    p_text.add_argument("--to", required=True, help="Recipient open_id or chat_id")
    p_text.add_argument("--text", required=True, help="Message text")

    # send-image
    p_img = subparsers.add_parser("send-image", help="Send an image")
    p_img.add_argument("--to", required=True, help="Recipient open_id or chat_id")
    p_img.add_argument("--file", required=True, help="Image file path")

    # send-file
    p_file = subparsers.add_parser("send-file", help="Send a file")
    p_file.add_argument("--to", required=True, help="Recipient open_id or chat_id")
    p_file.add_argument("--file", required=True, help="File path")

    # send-card
    p_card = subparsers.add_parser("send-card", help="Send an interactive card (markdown)")
    p_card.add_argument("--to", required=True, help="Recipient open_id or chat_id")
    p_card.add_argument("--content", default="", help="Markdown content")
    p_card.add_argument("--content-file", help="Read content from file")

    args = parser.parse_args()

    if args.command == "send-text":
        cmd_send_text(args)
    elif args.command == "send-image":
        cmd_send_image(args)
    elif args.command == "send-file":
        cmd_send_file(args)
    elif args.command == "send-card":
        cmd_send_card(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
