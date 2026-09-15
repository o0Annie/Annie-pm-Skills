# Step 4: 字段规格表 5→3 列

把 PRD 各章节的字段规格表(常见 5/6 列:字段名/类型/必填/校验规则/默认值/视觉层级)精简为参考飞书 PRD 模板的 3 列(字段/来源/说明)。

## 适用场景

- 用户要求"字段表精简为 3 列"
- 用户参考某飞书 PRD 的字段表(如演员中心 MP-0 的字段/来源/说明)
- 想统一 PRD 的字段表格式

## 转换规则

**3 列定义**:
- **字段** = 原"字段名"(直接保留)
- **来源** = 启发式推断 → 该字段值的产生方:
  - `用户输入` (输入框、上传)
  - `用户操作` (点击/切换/筛选/选择器/开关)
  - `UI 交互` (按钮、操作元素)
  - `业务计算` (余额、金额聚合、计算字段)
  - `业务统计` (收入/支出/次数等统计)
  - `服务端下发` (列表数据、配置项、状态、ID、时间戳 — 默认值)
  - `后端返回` (失败原因、错误文案)
  - `客户端计算` (前端按 UI 状态计算的字段)
  - `系统固定` (本期硬编码、不展示选项)
- **说明** = 把原"类型 + 必填 + 校验规则 + 默认值"等列合并精简成一段:
  - "必填" 是默认期望,无需复述
  - 类型(数字/字符串/枚举/日期) → 与校验合并: `字符串 · 长度 18-20`
  - 默认值用 `默认 xxx` 前缀
  - 视觉层级用 `主信息 / 副信息 / 主操作` 等词

## 完整流程

### 4.1 提取所有"字段规格"段

```python
import json, re
from pathlib import Path

raw = Path("/tmp/prd.json").read_text()
content = json.loads(raw)["data"]["document"]["content"]

# 每章节"字段规格" h4 到下一个 h4 之间的所有 table
for h3 in re.finditer(r"<h3[^>]*>([^<]+)</h3>", content):
    title = h3.group(1)
    # 找该章节的字段规格段,解析 table headers / rows
    # ...
```

(完整脚本见 `scripts/convert_tables.py`。它会输出每章节的 3 列 markdown 表,人工微调"来源"后再批量替换。)

### 4.2 设计每章节的 markdown 文件

```markdown
| 字段 | 来源 | 说明 |
| --- | --- | --- |
| 可提现余额 | 业务计算 | 金额 · 非负 2 位小数 · 主信息(最大字号) |
| 本月收入 | 业务统计 | 金额 · 带 + 号 · 副信息 |
```

**多表合并**:章节有多个分组小表时,用 `**xxx**` 副标分组,合并成一份大 markdown:

```markdown
**资金总览卡**

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| ...|

**筛选条**

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| ...|
```

### 4.3 批量 markdown str_replace 替换

> ⚠️ pattern 必须**唯一**。`#### 字段规格` 在每个章节都有,不能直接用。**用每章节字段表的第一行 + 最后一行内容**作为独特锚点。

```bash
DOC="<docx_token>"

# pattern 用每章节表内独特首尾行
# prefix = "| <第一字段名> | <第一列原值> | <第二列原值> | ..."
# suffix = "<最后行最后一列结尾片段>"

lark-cli docs +update --api-version v2 --doc $DOC \
  --command str_replace \
  --doc-format markdown \
  --pattern "| 支付宝账号 | 字符串 | 必填...2-20 个汉字,与平台实名一致" \
  --content "@./replace_5_6.md" \
  --as user
```

**markdown 模式跨块替换**:
- `prefix...suffix` 省略号语法,匹配从 prefix 第一次出现到 suffix 第一次出现的所有内容(含前缀后缀本身),全部替换为 content
- pattern **必须在全文唯一**;`docs +update` 报 `str_replace pattern matched multiple locations` 时,加长 prefix 让它独特

### 4.4 验证

```bash
lark-cli docs +fetch --api-version v2 --doc $DOC --as user \
  | python3 -c "import sys, json, re; \
      c = json.loads(sys.stdin.read())['data']['document']['content']; \
      tables = re.findall(r'<table[^>]*>(.*?)</table>', c, re.S); \
      for t in tables: \
        cols = len(re.findall(r'<th', t)); \
        print(f'cols={cols}')"
# 字段规格表的 cols 应该都是 3 (区域结构表等非字段表保持原列数)
```

## 文件路径限制

`--content @./xxx.md` 的路径**必须在当前 cwd**。`/tmp/xxx.md` 会报 `--file must be a relative path within the current directory`。先 `cp /tmp/xxx.md ./xxx.md`。

## 实战示例: 16 字段表 → 11 章节合并大表

某项目 PRD 有 14 个字段规格 table,用本方案 4.3:
- 简单章节 (单表 1-3 字段): 一次 str_replace 搞定
- 复杂章节 (4 表合并,如 5.2 钱包主页): 一次 str_replace 包含所有 4 表的新 markdown
- 特殊章节 (5.8.x 错误恢复): 原 table 已是 3 列,只改语义和表头(失败原因/后端返回/文案处理)

## 启发式不准的字段(手工修)

脚本启发式偶尔出错,常见案例:
- "提现金额" → 启发式判 `业务计算`,但其实是 `用户输入`
- "支付宝账号" / "真实姓名" → 启发式判 `服务端下发`,实际是 `用户输入`
- "是否默认" → 启发式判 `服务端下发`,实际是 `业务计算` (有且仅有一个为默认)

转换后人工 review markdown 文件,改"来源"列。
