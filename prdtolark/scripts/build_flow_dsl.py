"""构造白板 DSL JSON: 主路径横向 + 上方异常 + 下方详情/弹窗分行

布局原则:
- Row 0: 异常态(对齐主路径节点列)
- Row 1: 主路径(P0 → P1 → P5 → P6 → P6.2)
- Row 2+: 详情/弹窗(按归属挂在主路径节点列下方,过多则分行)
"""
import json
from pathlib import Path

TOKENS = json.loads(Path("tokens.json").read_text())

# (pencil_id, 主标题, PRD 章节号, 列, 行)
SCREENS = [
    # Row 0: 异常态(上方)
    ("MaY1o",  "P1.E 钱包加载失败",      "5.8.1", 1, 0),
    ("VdTSK",  "P5.E 提现提交失败",      "5.8.2", 2, 0),

    # Row 1: 主路径(横向)
    ("cieBT",  "P0 我的",                "5.7",   0, 1),
    ("ngLnv",  "P1 钱包主页",            "5.2",   1, 1),
    ("D6mC1",  "P5 提现申请",            "5.4",   2, 1),
    ("NLgMu",  "P6 收款账户管理",        "5.5",   3, 1),
    ("JzDOu",  "P6.2 绑定支付宝",        "5.6",   4, 1),

    # Row 2: 一级下沉(P1 弹窗 / P5 子状态 / P6 子状态)
    ("F2U7e6", "P3 导出账单弹窗",        "6.1",   1, 2),
    ("yEaZQ",  "P5.1 提现申请·已解绑",   "5.4",   2, 2),
    ("N1nFL0", "P6.1 收款账户·空状态",   "5.5",   3, 2),

    # Row 3: 二级下沉
    ("uC73z",  "P4 选择日期弹窗",        "6.2",   1, 3),
    ("b7Az36", "P2.1 消费详情",          "5.3",   2, 3),
    ("a1FDh0", "P6.3 账户操作菜单",      "6.3",   3, 3),

    # Row 4: 详情堆叠
    ("mC0dH",  "P2.2 收益详情",          "5.3",   2, 4),
    ("WIU2Z",  "P6.4 解绑二次确认",      "6.4",   3, 4),

    # Row 5: 详情末
    ("G1KIr1", "P2.3 提现详情",          "5.3",   2, 5),
]

# (from, to, style, label, fromAnchor, toAnchor)
FLOWS = [
    # 主路径(横向实线)
    ("cieBT",  "ngLnv",  "solid",  "",       "right",  "left"),
    ("ngLnv",  "D6mC1",  "solid",  "提现",   "right",  "left"),
    ("D6mC1",  "NLgMu",  "solid",  "切换",   "right",  "left"),
    ("NLgMu",  "JzDOu",  "solid",  "新增",   "right",  "left"),

    # 异常态(主路径向上,虚线)
    ("ngLnv",  "MaY1o",  "dashed", "",       "top",    "bottom"),
    ("D6mC1",  "VdTSK",  "dashed", "",       "top",    "bottom"),

    # 下沉(主路径向下)
    # P1 → P3 → P4 (导出弹窗链)
    ("ngLnv",  "F2U7e6", "solid",  "",       "bottom", "top"),
    ("F2U7e6", "uC73z",  "solid",  "",       "bottom", "top"),
    # P1 → P2.1/P2.2/P2.3 (交易详情,挂 col 2 下方)
    ("ngLnv",  "b7Az36", "solid",  "详情",   "bottom", "top"),
    ("b7Az36", "mC0dH",  "solid",  "",       "bottom", "top"),
    ("mC0dH",  "G1KIr1", "solid",  "",       "bottom", "top"),
    # P5 → P5.1
    ("D6mC1",  "yEaZQ",  "dashed", "未绑",   "bottom", "top"),
    # P5.1 → P6.2 (跨列添加)
    ("yEaZQ",  "JzDOu",  "solid",  "添加",   "right",  "bottom"),
    # P6 → P6.1 / P6.3
    ("NLgMu",  "N1nFL0", "dashed", "空",     "bottom", "top"),
    ("NLgMu",  "a1FDh0", "solid",  "",       "bottom", "top"),
    # P6.3 → P6.4
    ("a1FDh0", "WIU2Z",  "solid",  "解绑",   "bottom", "top"),
]

IMG_W, IMG_H = 240, 519
LABEL_H = 50
FRAME_H = IMG_H + LABEL_H + 20
COL_GAP = 140
ROW_GAP = 160
COL_X = lambda c: c * (IMG_W + COL_GAP)
ROW_Y = lambda r: r * (FRAME_H + ROW_GAP)

nodes = []

for pid, title, section, col, row in SCREENS:
    nodes.append({
        "type": "frame",
        "id": f"fr_{pid}",
        "x": COL_X(col),
        "y": ROW_Y(row),
        "width": IMG_W,
        "height": FRAME_H,
        "layout": "vertical",
        "gap": 8,
        "padding": 6,
        "alignItems": "center",
        "fillColor": "#FFFFFF",
        "borderColor": "#E5E7EB",
        "borderWidth": 1,
        "borderRadius": 8,
        "children": [
            {
                "type": "text",
                "width": IMG_W - 12,
                "height": LABEL_H,
                "text": f"{title}\nPRD {section}",
                "fontSize": 12,
                "textColor": "#1F2937",
                "textAlign": "center",
                "verticalAlign": "middle",
            },
            {
                "type": "image",
                "width": IMG_W - 12,
                "height": IMG_H,
                "image": {"src": TOKENS[pid]},
            },
        ],
    })

for src, dst, style, label, fa, ta in FLOWS:
    conn = {
        "type": "connector",
        "connector": {
            "from": f"fr_{src}",
            "to": f"fr_{dst}",
            "fromAnchor": fa,
            "toAnchor": ta,
            "lineShape": "rightAngle",
            "lineColor": "#9CA3AF" if style == "dashed" else "#374151",
            "lineWidth": 2,
            "lineStyle": style,
            "endArrow": "arrow",
        },
    }
    if label:
        conn["connector"]["label"] = label
    nodes.append(conn)

doc = {"version": 2, "nodes": nodes}
Path("diagram.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2))
print(f"✅ DSL: {len(SCREENS)} 屏 + {len(FLOWS)} connector → diagram.json")
print(f"画板尺寸约: {COL_X(4)+IMG_W}×{ROW_Y(5)+FRAME_H}")
