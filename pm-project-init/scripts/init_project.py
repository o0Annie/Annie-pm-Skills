#!/usr/bin/env python3
"""产品项目脚手架：按模板生成规范目录。只新建，绝不覆盖或移动已有文件。"""

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"
VARIANTS = SKILL_DIR / "variants"
PLACEHOLDER = "[产品名称]"
STATES_FILE = Path("00-rules/status-and-gates.md")
# 模板里用 gitignore 存放，避免被技能目录自身的 git 规则吞掉
RENAMES = {Path("gitignore"): Path(".gitignore")}
# 极榕 是多项目容器，只能初始化其子目录
FORBIDDEN_TARGETS = {Path("/"), Path.home(), Path.home() / "Desktop", Path.home() / "Desktop" / "极榕"}


def plan(states: str) -> list[tuple[Path, Path]]:
    """返回 (模板源文件, 目标相对路径) 列表。"""
    pairs = []
    for src in sorted(TEMPLATES.rglob("*")):
        if src.is_file() and src.name != ".DS_Store":
            rel = src.relative_to(TEMPLATES)
            pairs.append((src, RENAMES.get(rel, rel)))
    pairs.append((VARIANTS / f"status-and-gates.{states}.md", STATES_FILE))
    return pairs


def validate_name(name: str) -> str:
    name = name.strip()
    if not name or len(name) > 60 or any(c in name for c in "\n\r/\\"):
        sys.exit("错误：产品名称不能为空、不能超过 60 字，且不能包含换行或斜杠")
    return name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="项目根目录，不存在则创建")
    parser.add_argument("--name", required=True, help="产品名称，替换模板中的 [产品名称]")
    parser.add_argument("--states", choices=["lite", "full"], default="lite",
                        help="lite=6 状态，full=10 状态")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不写文件")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if target in FORBIDDEN_TARGETS:
        sys.exit(f"错误：拒绝在 {target} 直接初始化，请指定具体项目目录")
    if target.exists() and not target.is_dir():
        sys.exit(f"错误：{target} 不是目录")
    name = validate_name(args.name)

    created, skipped = [], []
    for src, rel in plan(args.states):
        dest = target / rel
        if dest.exists():
            skipped.append(str(rel))
            continue
        created.append(str(rel))
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src.read_text(encoding="utf-8").replace(PLACEHOLDER, name),
                            encoding="utf-8")

    print(json.dumps({
        "target": str(target),
        "dry_run": args.dry_run,
        "states": args.states,
        "created": created,
        "skipped_existing": skipped,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
