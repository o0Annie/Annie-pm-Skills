---
name: pm-project-init
description: 产品项目初始化脚手架（来源：@runmaotui《产品项目初始化 Prompt：让 Agent 参与产品全流程》）。为产品项目生成 00-rules ~ 99-archive 编号目录、规则文件（命名、唯一事实源、需求状态门槛、工作流）、AGENTS.md/CLAUDE.md、输入来源登记表和需求池表，让后续市场分析、调研、需求、原型、PRD、评审、验收、复盘都在同一项目上下文中进行。触发场景：(1) 新建/开始一个产品项目、在 ~/Desktop/极榕 下新建项目目录，(2) 会话目录为空且 SessionStart hook 提示初始化，(3) 用户说"初始化项目""规范化项目""项目脚手架""建项目目录""pm init"，(4) 需要把已有项目改造为规范结构（只补缺，迁移需确认）。
---

# 产品项目初始化

把一个空目录（或已有项目）初始化为规范的产品工作空间。生成的结构同时是后续"产品经理工作台"的数据契约，**需求池表格式不要改动**。

## 生成内容

```text
00-rules/              # 规则和模板（naming-and-structure / source-of-truth / status-and-gates / product-workflow）
01-inputs/             # 原始输入 + source-register.md
02-product/            # 稳定产品事实
03-planning/           # 跨需求规划
04-requirement-pool/   # 需求池 + requirement-pool.md
05-requirements/       # 单需求工作包
06-versions/           # 版本管理
07-reviews/            # 评审、验收、复盘
90-assets/             # 共享资产
99-archive/            # 归档
README.md  AGENTS.md  CLAUDE.md（@AGENTS.md 引用）  .gitignore
```

模板在 `templates/`，状态集变体在 `variants/`。不要手写这些文件，统一用脚本生成。

## 工作流程

### 1. 确认目标目录

- 默认是当前会话目录；用户在会话中新建项目时，目标是新项目目录（如 `~/Desktop/极榕/<项目名>`）
- 脚本拒绝在 `/`、`~`、`~/Desktop` 直接初始化
- `~/Desktop/极榕` 本身是多项目容器，**不能**直接初始化它，必须指定子目录

### 2. 向用户确认两个参数（一次问完）

- **产品名称**：替换模板中的 `[产品名称]`
- **状态集**：`lite`（6 状态，默认推荐起步用）或 `full`（10 状态）

### 3. 预演

```bash
python3 ~/.claude/skills/pm-project-init/scripts/init_project.py \
  --target "<目录>" --name "<产品名称>" --states lite --dry-run
```

- `skipped_existing` 为空：目录是新项目，直接进入第 4 步
- `skipped_existing` 非空：说明已有同名文件，向用户列出将新建和将跳过的文件，确认后再执行

### 4. 执行

去掉 `--dry-run` 再运行一次。脚本**只新建，绝不覆盖或移动**已有文件。

### 5. 已有项目的额外处理（目录非空时）

脚本只补齐缺失的规范文件，不处理已有内容。需要额外做的：

- **已有 CLAUDE.md**：脚本会跳过。征得同意后在其末尾追加一行 `@AGENTS.md`，不要改动原内容
- **已有散落文件**：列出"文件 → 建议归属目录"的迁移清单（原始材料进 `01-inputs/` 并登记到 `source-register.md`，调研/规划进 `03-planning/`，截图进 `90-assets/`）。**必须等用户确认后才移动**，代码类目录（`src/`、`node_modules/`、`package.json` 等）保持原位不动

### 6. 验证并汇报

```bash
find "<目录>" -maxdepth 2 -not -path '*/.git*' | sort
```

确认 10 个编号目录和 4 个规则文件都存在，`[产品名称]` 已被替换（`grep -r "\[产品名称\]" "<目录>"` 应无输出）。向用户汇报新建/跳过的文件，并提示下一步：先在 `01-inputs/source-register.md` 登记第一份输入材料。

## 约束

- 初始化之后，项目内的协作规则以项目的 `AGENTS.md` 为准（改文件前先说明并确认、结论标注 `已观察/推断/待确认/未覆盖`、不擅自推进需求状态）
- 需求状态只在 `04-requirement-pool/requirement-pool.md` 维护，保持表头列顺序不变，工作台会解析这张表
- 不自动执行 `git init`，用户要求时再做
