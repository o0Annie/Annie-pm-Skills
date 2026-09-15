# Annie-pm-Skills

记录一些自己在产品经理工作中提炼的 skill，覆盖从竞品调研、产品决策，到 PRD 写作与交付的完整链路。

## 使用方式

克隆本仓库后，把需要的 skill 目录软链到 Claude Code 的 skill 目录：

```bash
git clone https://github.com/o0Annie/Annie-pm-Skills.git
ln -s "$(pwd)/Annie-pm-Skills/writing-prds" ~/.claude/skills/writing-prds
```

也可以整体软链，一次启用全部：

```bash
for d in Annie-pm-Skills/*/; do ln -s "$(pwd)/$d" ~/.claude/skills/; done
```

---

## 一、调研与决策

写 PRD 之前，先把「要不要做」「做成什么样」想清楚。

- [**competitor-research**](./competitor-research/) — 通用竞品调研：实测竞品（公开页 + 必要时登录态）、提炼关键洞察（核心做法 / 值得借鉴的设计 / 风险与短板），而非罗列功能或照搬文案；可选把结论以图文混排 + 流程图输出到飞书。核心纪律：重提炼轻罗列、结论基于实测、宣称必溯源、登录态需用户配合、绝不提交真实身份或发起真实交易。
  - `SKILL.md` 主工作流（四阶段）+ `references/`（实测技巧 / 飞书同步配方 / 踩坑清单）

- [**internet-product-strategy**](./internet-product-strategy/) — 基于王慧文《互联网产品管理课》的战略决策框架：市场切入策略、规模效应类型判断、STP 定位、4P 策略、供需关系与入场时机。适用于新产品立项前的方向判断。
  - `SKILL.md` + `references/course-knowledge-base.md`（课程知识库）

- [**value-realization**](./value-realization/) — 评估用户是否能清晰感知产品价值。核心命题：用户说不出自己为什么在用，就不会持续用。适用于功能价值存疑、留存不佳、方向不明时的诊断。
  - `SKILL.md` + `references/real-cases.md`（真实案例库）

- [**product-guide**](./product-guide/) — 已有功能逻辑与用户流程的 ROI 审计，回答「这个功能值得它消耗的用户注意力和工程维护成本吗」。适合做功能裁剪与优先级复盘。

- [**behavioral-product-design**](./behavioral-product-design/) — 把行为科学用到产品设计上：习惯养成、摩擦削减、留存机制、助推（nudge）设计。
  - `SKILL.md` + `references/guest-insights.md`（行为经济学家与产品负责人洞察）

## 二、结构与写作

把想清楚的东西，落成工程可执行的文档。

- [**ui-blueprint**](./ui-blueprint/) — 在动手设计或写代码之前，先产出纯结构的 Markdown 线框草图：布局骨架、组件类型、内容文案、层级关系，不含色彩字体间距。用作 PRD 界面章节的底稿，也用于和设计对齐结构意图。
  - `SKILL.md` + `references/examples.md`（多屏 / 多步骤示例）

- [**writing-prds**](./writing-prds/) — PRD 编写规范：基于设计稿或产品构想，写出工程能直接开工的需求文档。
  - `SKILL.md` + `references/guest-insights.md`（产品负责人实践）

- [**writing-plans**](./writing-plans/) — 把 PRD 拆成实现计划：假定执行者不熟悉代码库，逐任务写清改哪些文件、怎么测、要读哪些文档。PRD 的下游产物。

- [**chinese-copy-polish**](./chinese-copy-polish/) — 中文文案润色：去翻译腔、拆长句、结论先行、克制 emoji 与加粗、规范中英文间距与全角标点。只改表达不改事实，不新增未确认信息。用于 PRD 定稿前的最后一遍打磨。
  - `SKILL.md` + `references/rules.md`（规则清单）+ `scripts/check_zh.py`（排版自检脚本）

- [**brand-storytelling**](./brand-storytelling/) — 品牌叙事与定位表达：写公司定位、pitch 叙事、messaging 框架。用于 PRD 的背景章节与对外材料。
  - `SKILL.md` + `references/guest-insights.md`

## 三、交付

- [**prdtolark**](./prdtolark/) — Pencil 原型 + 本地 PRD → 飞书 docx 的端到端交付。四步工作流：原型屏排版成飞书白板页面流转图、PRD 文字流程转 mermaid 白板、原型截图按章节插入 PRD、字段规格表从多列精简为 3 列。
  - `SKILL.md` + `references/`（流转图 / mermaid 白板 / 章节配图 / 3 列表格 / 踩坑清单）+ `scripts/build_flow_dsl.py`

---

## 外部依赖说明

多数 skill 开箱即用，以下两个有额外依赖：

- **prdtolark** — 需要 `lark-cli`、`npx`、`sips`、`python3`。`SKILL.md` 中引用的 `../lark-shared/SKILL.md` 属于飞书官方 skill 套件（认证与权限约定），不在本仓库内，需另行安装。
- **competitor-research** — 需要 `lark-cli`、`sips`、`python3`，以及 Playwright MCP（用于实测竞品页面）。
