#!/usr/bin/env python3
"""中文文案机械体检：只报告可疑处，不自动改写（改写是判断题，交给人）。

用法：
    python3 check_zh.py <file.md> [file2.md ...]

检查项：
    - 中英文 / 中数之间缺空格
    - 中文语境里混用的半角标点 , ; : ? !
    - 破折号 —— 串句
    - emoji 密度过高的标题 / 段落
    - 超长句（>40 个汉字未断句）
    - 常见翻译腔与黑话词
"""
import re
import sys

TRANSLATIONESE = ["进行", "对其进行", "基于", "通过.{0,6}的方式", "实现了", "拥有", "具备",
                  "众所周知", "值得注意的是", "需要指出的是", "该功能", "此功能"]
JARGON = ["赋能", "抓手", "场景化", "闭环", "沉淀", "颗粒度", "心智", "链路", "对齐颗粒"]
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF←-⇿⬀-⯿]"
)
CJK = r"一-鿿"
HEADING = re.compile(r"^#{1,6}\s")
PAREN = re.compile(r"（([^）]*)）")
# 限定范围的括号（端/版本/平台）可保留，不算旁白
SCOPE_HINT = re.compile(r"端|版|PC|Web|手机|电脑|移动|iOS|安卓|Android|平板|网页")


def check_line(ln):
    hits = []
    # 标题含括号旁白（限定范围的括号除外）
    if HEADING.match(ln):
        for inner in PAREN.findall(ln):
            if ("，" in inner or "、" in inner or len(inner) > 8) and not SCOPE_HINT.search(inner):
                hits.append(f"标题含括号旁白「{inner}」，建议删掉、下沉到正文")
    # 中英/中数缺空格（忽略常见量词场景不强报，只报字母与汉字相邻）
    if re.search(rf"[{CJK}][A-Za-z]", ln) or re.search(rf"[A-Za-z][{CJK}]", ln):
        hits.append("中英文之间可能缺空格")
    # 中文语境半角标点
    if re.search(rf"[{CJK}]\s*[,;:?!]\s", ln) or re.search(rf"[{CJK}][,;:?!]$", ln):
        hits.append("中文句里疑似混用半角标点，建议全角，。；：？！")
    # 破折号串句
    if "——" in ln and ln.count("——") >= 1 and len(re.findall(rf"[{CJK}]", ln)) > 12:
        hits.append("破折号串句，建议改句号或冒号")
    # emoji 密度（箭头是约定的路径/流程符号，不计入）
    ARROWS = "→←↑↓↔⇒⇐➔➜➙➛➝⟶"
    n_emoji = len([c for c in EMOJI.findall(ln) if c not in ARROWS])
    if n_emoji >= 2:
        hits.append(f"emoji 偏多（{n_emoji} 个），每节标题建议 ≤1")
    # 超长句：按中文句末标点切分，单句汉字数 >40
    for seg in re.split(r"[。！？!?\n]", ln):
        cjk_n = len(re.findall(rf"[{CJK}]", seg))
        if cjk_n > 40:
            hits.append(f"超长句（约 {cjk_n} 字未断），建议拆分")
            break
    # 翻译腔 / 黑话
    for w in TRANSLATIONESE:
        if re.search(w, ln):
            hits.append(f"疑似翻译腔：{w.replace('.{0,6}', '…')}")
            break
    for w in JARGON:
        if w in ln:
            hits.append(f"疑似黑话：{w}")
            break
    return hits


def main():
    if len(sys.argv) < 2:
        print("用法：python3 check_zh.py <file.md> [...]")
        sys.exit(1)
    total = 0
    for path in sys.argv[1:]:
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            print(f"⚠ 无法读取 {path}: {e}")
            continue
        print(f"\n===== {path} =====")
        file_hits = 0
        for i, ln in enumerate(lines, 1):
            for h in check_line(ln.rstrip("\n")):
                print(f"  L{i}: {h}")
                file_hits += 1
        total += file_hits
        print(f"  —— 小计 {file_hits} 处提示" if file_hits else "  ✓ 未发现机械问题")
    print(f"\n合计 {total} 处提示（仅供参考，需人工判断后修改）")


if __name__ == "__main__":
    main()
