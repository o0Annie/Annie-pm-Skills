# Step 1: 流转白板 (DSL + image 节点)

把 N 张原型屏排版成飞书白板的页面流转图,屏与屏之间用 connector 连接。

## 适用场景

- 用户的 PRD 4.4 章节有空白板,要画"页面流转图"
- 用户希望用**真实原型截图**而非文字标签作为流程节点

## 前置准备

```bash
# 1. 拿到目标白板 token
#    - 若 PRD 中已嵌入空白板: lark-cli docs +fetch --api-version v2 --doc $DOC
#      grep "<whiteboard token=" 提取
#    - 若没有: lark-cli docs +update --command append --content '<whiteboard type="blank"></whiteboard>'
WB_TOKEN="<whiteboard_token>"

# 2. 准备 N 张原型 PNG (Pencil export_nodes scale=1,375×812 已足够清晰)
#    放到 prototype_screens/
```

## 完整流程(5 子步骤)

### 1.1 上传所有 PNG 到白板域

```bash
# 关键: --parent-type 必须是 whiteboard (不是 docx),--parent-node 是 whiteboard_token
echo '{' > tokens.json && first=1
for f in 屏1 屏2 屏3 ... 屏N; do
  tok=$(lark-cli docs +media-upload \
    --file ./${f}.png \
    --parent-type whiteboard \
    --parent-node $WB_TOKEN \
    --as user 2>&1 | python3 -c "import sys,json,re; \
      m=re.search(r'\"file_token\":\\s*\"([^\"]+)\"', sys.stdin.read()); \
      print(m.group(1) if m else 'ERR')")
  [ "$first" = "1" ] && first=0 || echo "," >> tokens.json
  printf '  "%s": "%s"' "$f" "$tok" >> tokens.json
  echo "  $f → $tok"
done
echo '' >> tokens.json && echo '}' >> tokens.json
```

> ⚠️ 如果 `--parent-node` 传 docx_token 会报 `params error (1061002)`。必须是 whiteboard_token。

### 1.2 构造 DSL JSON (image 节点网格 + connector)

复制 `scripts/build_flow_dsl.py` 到本地工作目录,**修改**以下两组数据:

```python
# 屏映射 (Pencil_id, 主标题, PRD 章节号, 列, 行)
SCREENS = [
    ("cieBT",  "P0 我的",          "5.7", 0, 0),
    ("ngLnv",  "P1 钱包主页",      "5.2", 1, 0),
    # ...
]

# 流转关系 (from, to, style, label, fromAnchor, toAnchor)
FLOWS = [
    ("cieBT",  "ngLnv",  "solid",  "",       "right",  "left"),    # 同行
    ("ngLnv",  "b7Az36", "solid",  "",       "bottom", "top"),     # 跨行
    ("WIU2Z",  "NLgMu",  "dashed", "",       "top",    "bottom"),  # 回指
    # ...
]
```

**布局参数**(经过实战验证的好默认):

```python
IMG_W, IMG_H = 240, 519
LABEL_H = 50
COL_GAP = 140
ROW_GAP = 160        # ≥ 160 才能给跨行连线足够路径空间
FRAME_H = IMG_H + LABEL_H + 20

# Frame children 顺序: text 在前 (label 顶部), image 在后 (image 底部)
# 这样 fromAnchor='bottom' 出口在 image 底,不经过 label 文字
```

**网格布局策略 — "主路径 + 异常上方 + 详情下方分行"**(推荐):

```
列:     0     1      2      3      4
Row 0:        P1.E          P5.E              ← 异常态对齐主路径列
Row 1: P0  →  P1   →  P5  →  P6  →  P6.2      ← 主路径横向(实线)
Row 2:        P3     P5.1   P6.1               ← 一级下沉
Row 3:        P4     P2.1   P6.3               ← 二级下沉
Row 4:               P2.2   P6.4               ← 详情堆叠(过多分行)
Row 5:               P2.3                       ← 详情末
```

**布局原则**(用户审美需求,务必遵守):
1. **主路径横向**(Row 1):用户完成核心任务的 happy path,从左到右排列(典型 5 屏)
2. **异常态上方**(Row 0):错误/失败态对齐主路径节点的列号,用 `top→bottom` 虚线
3. **详情/弹窗下方**(Row 2+):按归属挂在主路径节点列下方,用 `bottom→top` 实线
4. **过多则分行**:同一主路径节点下沉屏数 > 2 时,在该列下方分多行垂直堆叠
5. **跨列下沉**:多详情屏(如交易详情 P2.x)可挂在相邻列下方,避免单列堆 5 屏

**主路径节点选择启发式**:
- 入口屏 → 主页 → 主要动作页 → 关键子页 → 完成态
- 避免选"详情型""弹窗型"作主路径
- 选 5 屏左右,横向延伸不超过 1800px(2K 屏可视)

**Connector 锚点规则**:

| 相对位置 | fromAnchor | toAnchor |
|---|---|---|
| 同行右进 | right | left |
| 同行左回 | left | right |
| 跨行向下 (任意斜向) | bottom | top |
| 回指向上 | top | bottom |

> 引擎自动绕线 (省略锚点) 经常乱跳,**必须**显式声明 anchor。

**lineShape 选择**:
- `polyline` (默认圆角折线): 一般场景
- `rightAngle` (直角折线): 标签密集时更整齐,推荐用于这个 skill
- `straight` (直线): 不用于流转图

**Connector label 策略**:
- 保留**有信息量**的关键流转: `切换` / `未绑定` / `新增` / `解绑`
- 删除**冗余**: `异常` / `失败` / `完成` / `成功`(虚线本身已暗示)
- **同一节点 3+ 出线**时,label 互相挤压,优先全部去掉

### 1.3 生成 DSL → OpenAPI

```bash
python3 build_dsl.py     # 生成 diagram.json
npx -y @larksuite/whiteboard-cli@^0.2.11 \
  -i ./diagram.json --to openapi --format json -o ./openapi.json
```

### 1.4 写白板

```bash
# ⚠️ --overwrite 会清空白板;清空后 image token 失效。
# 如果是更新现有图,必须先回到 1.1 重新上传所有 PNG 拿新 token,重新生成 diagram.json。

lark-cli whiteboard +update \
  --whiteboard-token $WB_TOKEN \
  --source @./openapi.json \
  --input_format raw \
  --idempotent-token "<unique-10+chars>" \
  --overwrite --as user
```

成功返回 `ok: true, created N nodes`。

### 1.5 验证

```bash
lark-cli whiteboard +query --whiteboard-token $WB_TOKEN \
  --output_as image --output ./wb_final.png --as user
sips -Z 1500 wb_final.png --out wb_check.png   # 缩到 1500px 避开 Read 2000px 限制
# 用 Read 工具读 wb_check.png 视觉验证
```

## 失败排查

| 错误码 | 原因 | 解决 |
|---|---|---|
| `invalid arg (2890002)` | image token 已失效(--overwrite 清空过) | 回 1.1 重新上传所有 PNG |
| `params error (1061002)` | media-upload `--parent-type docx` 或 `--parent-node` 是 block_id 而非 whiteboard_token | 改用 `--parent-type whiteboard --parent-node $WB_TOKEN` |
| dry-run 显示 OK 但实际写入失败 | 同上,服务端校验不在 dry-run 里 | 检查 token 时效 |

## 经验值

- 16 屏 5 行布局 (5 列 × 5 行) 适合手机原型 (375×812 比例)
- ROW_GAP < 160 → 跨行连线挤进 label 文字
- LABEL_H < 50 → 标题 + PRD 章节双行装不下
