#!/usr/bin/env python3
"""SessionStart hook：会话目录为空（项目刚开始）时，提示 Claude 调用 pm-project-init。"""

import json
import sys
from pathlib import Path

# 新项目里常见的非内容条目，不影响"空目录"判断
IGNORED = {".DS_Store", ".claude", ".git", ".gitignore", ".idea", ".vscode"}
# resume / compact 是继续已有会话，不提示
TRIGGER_SOURCES = {"startup", "clear"}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if payload.get("source", "startup") not in TRIGGER_SOURCES:
        return
    cwd = Path(payload.get("cwd") or Path.cwd())
    if not cwd.is_dir() or cwd == Path.home():
        return
    if any(entry.name not in IGNORED for entry in cwd.iterdir()):
        return

    print(json.dumps({
        # 模型无法主动发言，用 systemMessage 让用户在界面上直接看到提示
        "systemMessage": "检测到空目录：发送任意消息（如「初始化项目」）即可开始产品项目规范化",
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"当前会话目录 {cwd} 是空目录，视为新项目开始。"
                "在处理用户第一个与项目相关的请求前，先调用 pm-project-init skill，"
                "向用户确认产品名称和状态集（6 状态/10 状态）后再初始化项目规范目录。"
                "如果用户明确表示这不是产品项目，则跳过。"
            ),
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
