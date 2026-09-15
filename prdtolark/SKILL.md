---
name: prdtolark
description: "把 Pencil 原型 + 本地 PRD 内容写入飞书 docx 的端到端 skill。提供 4 步工作流: (1) 把 16+ 原型屏排版成飞书白板页面流转图(image + connector DSL); (2) 把 PRD 文字流程改造成 mermaid 白板; (3) 把原型截图按章节插入 PRD; (4) 把 PRD 字段规格表从多列(字段名/类型/必填/校验/默认)精简为 3 列(字段/来源/说明)。当用户提到 PRD 原型联动、给 PRD 配图、把原型截图嵌入 PRD 章节、画页面流转白板、字段表精简为 3 列、或 PRD + Pencil + 飞书联合输出时使用。"
metadata:
  requires:
    bins: ["lark-cli", "npx", "sips", "python3"]
  cliHelp: "lark-cli docs +update --api-version v2 --help; lark-cli whiteboard +update --help"
---

# prdtolark — Pencil 原型 + PRD → 飞书 docx 端到端

> **CRITICAL — 执行任何步骤前先读 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)**(认证、权限、`--as` 身份)。

本 skill 把 Pencil 原型的多个屏、PRD 文字流程、字段规格表"四合一"地灌入飞书 docx。流程是**纯写入**操作,执行前必须向用户确认 docx token + 目标章节边界。

## 触发条件

任一条满足即可启用本 skill:
- 用户给出 PRD docx URL/token + Pencil `.pen` 文件,要求"把原型嵌入 PRD"或"画页面流转图"
- 用户要求"按章节配图"或"在 PRD 5.x 章节插入原型截图"
- 用户要求"PRD 字段规格表改 3 列"或"参考 XX 文档的字段表格式"(字段/来源/说明)
- 用户要求"把 5.1 核心流程画成白板"或"PRD 文字流程改 mermaid"

## 4 步主工作流

```
Step 1: 流转白板 (4.4 页面流转图)
  → 用 Pencil 导出 N 屏 PNG → 上传到目标白板 → DSL 排版 → 写白板
  → 详见 [references/flow-board.md](references/flow-board.md)

Step 2: 文字流程 → mermaid 白板 (5.1 核心流程)
  → 提取 PRD 文字步骤 → 写 mermaid flowchart → markdown str_replace 替换
  → 详见 [references/mermaid-board.md](references/mermaid-board.md)

Step 3: 章节配图 (5.x / 6.x 各功能模块)
  → 16 张 PNG 依次 docs +media-insert --selection-with-ellipsis "章节标题"
  → 主图后插(后插的在前面)
  → 详见 [references/section-illustrate.md](references/section-illustrate.md)

Step 4: 字段规格表 5→3 列
  → 解析多列原表 → 启发式推断"来源" → markdown str_replace 替换
  → 详见 [references/table-3col.md](references/table-3col.md)
```

## 公共前置 (Step 0)

```bash
# 1. 获取 docx token (从 URL 解析)
DOC="<docx_token>"   # 如 FVNkd2o1Noh...

# 2. 创建工作目录
mkdir -p prototype_screens && cd prototype_screens

# 3. 用 Pencil MCP export_nodes 导出每屏 PNG(scale=1, ≤2000px)
#    → 文件名建议用 Pencil 节点 ID (如 ngLnv.png)

# 4. 列出 PRD 章节,确认每屏对应哪个章节
lark-cli docs +fetch --api-version v2 --doc $DOC --as user > /tmp/prd.json
```

## ⚠️ 11 个关键约束 (必读)

详细排查见 [references/pitfalls.md](references/pitfalls.md)。**核心 4 条**:

1. **白板 image token 在 `--overwrite` 后失效**:每次 `whiteboard +update --overwrite` 前必须重新上传所有 PNG,否则报 `invalid arg (2890002)`,且 dry-run **不会**提示这个错。
2. **docx 中 `<img src="<token>"/>` src 被忽略**:写入时飞书会建空图。**只能用 `docs +media-insert` 一步到位**(自动建 block + 上传 + 关联)。
3. **`block_move_after` / `block_copy_insert_after` 在 lark-cli 1.0.46 broken**:`src_block_ids` 被服务器视为空。**不要走 move/copy 路径**,改用 `+media-insert` 直接定位。
4. **`+media-insert --selection-with-ellipsis` 只插顶级 block**:不会进入 grid column 内部。**飞书 docx 目前无法把图作为 grid column 子节点**,左图右文分栏不可达,改用顺序结构(图在上、说明在下)。

## 沉淀工件

每次跑完本 skill,在工作目录留下:

```
prototype_screens/
├── *.png                 ← 各屏原型
├── tokens.json           ← 白板域 image token 映射(--overwrite 后失效)
├── build_dsl.py          ← 复制自 scripts/build_flow_dsl.py 后修改
├── diagram.json          ← 白板 DSL 源
├── openapi.json          ← whiteboard-cli 转换后
└── wb_final.png          ← 白板预览
```

## 各步骤决策

| 用户需求 | 跳到 |
|---|---|
| 只画 4.4 流转图 | [Step 1](references/flow-board.md) |
| 只把 5.1 文字流程改 mermaid | [Step 2](references/mermaid-board.md) |
| 只插章节图 | [Step 3](references/section-illustrate.md) |
| 只改字段表 | [Step 4](references/table-3col.md) |
| 全套(典型场景) | 1 → 2 → 3 → 4 顺序执行 |

## 完成验证

- 4.4 白板: `lark-cli whiteboard +query --output_as image --output ./wb.png` + `sips -Z 1500` + Read
- 5.1 白板: 同上,token 在 `<whiteboard token="...">` 标签里
- PRD 整体: `lark-cli docs +fetch` 取 outline 看章节结构
- 不允许"声称完成"而未验证 — 必须看到预览图或 fetch 结果。
