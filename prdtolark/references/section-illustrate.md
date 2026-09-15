# Step 3: 章节配图

把 N 张原型 PNG 按章节插入 PRD,作为顶级 block 在章节标题之后。

## 适用场景

- 用户的 PRD 5.x / 6.x 每个功能模块章节希望"开头放一张原型截图"
- 参考飞书文档的分栏(左图右文)— **注意**: 飞书 docx 目前**无法**把图放进 grid column,只能顺序结构

## 关键限制 (必读)

| 尝试方案 | 结果 |
|---|---|
| `<img src="<已上传 file_token>"/>` 直接写入 | ❌ src 被忽略,飞书会建空图 |
| `block_move_after / block_copy_insert_after` 把图移进 grid column | ❌ lark-cli 1.0.46 仍 broken,`src_block_ids` 字段被服务器视为空 |
| `docs +media-insert --selection-with-ellipsis "grid column 内文字"` | ❌ 图被插在 grid **外面**(顶级 block) |
| `docs +create` 含 grid + img src=token | ❌ create 时 src 同样被忽略 |

**结论**: 当前唯一可行方案是**顺序结构**(图在上、说明在下),通过 `+media-insert --selection-with-ellipsis "章节标题"` 把图作为顶级 block 插在章节标题之后。

## 完整流程

```bash
DOC="<docx_token>"

# 每张图一次调用,主图后插(后插的会显示在前面)
insert() {
  local file="$1" caption="$2" sel="$3"
  lark-cli docs +media-insert --doc "$DOC" \
    --file "./$file" \
    --width 280 \
    --caption "$caption" \
    --selection-with-ellipsis "$sel" \
    --as user 2>&1 \
  | python3 -c "import sys,json,re; \
      m=re.search(r'\"ok\":\\s*(true|false)', sys.stdin.read()); \
      print('  $caption →', m.group(1) if m else '?')"
}

# 单屏章节(只插 1 张)
insert "ngLnv.png" "P1 钱包主页" "5.2 钱包主页"

# 多屏章节(同一章节插多张,主图最后插)
insert "G1KIr1.png" "P2.3 提现详情" "5.3 交易详情(消费/收益/提现)"
insert "mC0dH.png"  "P2.2 收益详情" "5.3 交易详情(消费/收益/提现)"
insert "b7Az36.png" "P2.1 消费详情" "5.3 交易详情(消费/收益/提现)"   # 最后插 → 显示在最前
```

## 顺序原则

`--selection-with-ellipsis` 把新 image block 插在选定文本所在 block 的**正后方**。同 selection 多次插入时:
- 先插的在更后面 (下方)
- **后插的在更前面 (上方)**

要让 P2.1 在 P2.2 上方,顺序: 先 G1KIr1 (P2.3) → 后 b7Az36 (P2.1)。

## 章节标题作 selection 的注意

- selection 必须能在文档里**唯一匹配**
- 飞书的 selection-with-ellipsis 用的是渲染后文本,`<h3>5.2 钱包主页</h3>` 在 markdown 里就是 "5.2 钱包主页"
- 如果章节标题在多处出现(比如 mermaid 白板里有"5.2 钱包主页"这种节点 label),会冲突 — 改用更长的标题片段

## 命令参数对照

| 参数 | 推荐值 | 说明 |
|---|---|---|
| `--width` | 280 (手机屏) / 600 (网页屏) | 控制 docx 中显示宽度;高度自动按 PNG 宽高比 |
| `--align` | `center` (默认) | 不必传 |
| `--caption` | 必传 | 飞书在 img 下方显示这段文字 |

## 验证

```bash
lark-cli docs +fetch --api-version v2 --doc $DOC --as user \
  | grep -oE '<img name="[^"]+"' | head -20
# 应该看到所有 16 张图的文件名
```
