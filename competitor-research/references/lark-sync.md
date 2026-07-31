# 飞书图文混排同步配方

> 二进制名是 **`lark-cli`**(不是 `larkcli`)。静默去噪:`export LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1`。
> `--doc` 传 **docx URL 或 doc_id**;`wiki` 链接要先转 docx(fetch wiki 拿底层 `document_id`)。`media-insert` **不支持 /wiki**。
> `@file` 只接受 **cwd 相对路径**(绝对路径报 "unsafe file path");长内容用 `--content -` 走 stdin。

## 决策:整篇覆盖 vs 增量编辑

| 场景 | 命令 | 注意 |
|---|---|---|
| 首次写入 / 大改重排 | `overwrite` | ⚠️ **清空全文含图片、画板**。覆盖后必须重新插回所有图与画板 |
| 改已含图/画板的文档 | `str_replace` / `block_insert_after` / `block_replace` | **严禁 overwrite**,否则毁掉已插入的图和画板 |

**铁律**:文档一旦插了截图或画板,后续所有改动走增量,不要再 overwrite。

## 1. 整篇覆盖(纯文本 + 占位符)

图片行与 mermaid 块不能直接进 markdown 覆盖——先抽出、留占位:

```bash
python3 - "$TMP" <<'PY'
import sys,re,os; tmp=sys.argv[1]
src=open("调研.md",encoding="utf-8").read()
mms=re.findall(r"```mermaid\n(.*?)```",src,flags=re.S)      # 抽 mermaid
i=[0]
text=re.sub(r"```mermaid\n.*?```",lambda m:(i.__setitem__(0,i[0]+1) or f"WBMARK{i[0]}"),src,flags=re.S)
text="\n".join(l for l in text.split("\n") if not l.startswith("!["))  # 去图片行
open(os.path.join(tmp,"feishu.md"),"w",encoding="utf-8").write(text)
for n,m in enumerate(mms,1): open(os.path.join(tmp,f"wb{n}.mmd"),"w",encoding="utf-8").write(m.strip())
PY
lark-cli docs +update --doc "$DOC" --command overwrite --doc-format markdown --content - < "$TMP/feishu.md" -q '.data.result'
```

覆盖后:**先插图(见 §3)→ 再把 WBMARK 占位换成画板(见 §4)**。

## 2. 增量文本编辑

```bash
# 行内替换(markdown 模式支持加粗/跨行;XML 默认仅 inline 单块)
lark-cli docs +update --doc "$DOC" --command str_replace --doc-format markdown \
  --pattern '旧文本' --content - <<'EOF'
新文本(可含 **加粗**、换行)
EOF

# 插新块:先取锚点块 id,再 block_insert_after(XML 内容)
lark-cli docs +fetch --doc "$DOC" --scope keyword --keyword "锚点句" --detail with-ids --doc-format xml -q '.data.document.content'
lark-cli docs +update --doc "$DOC" --command block_insert_after --block-id "<id>" --content - <<'EOF'
<p><b>标题</b></p><ul><li>要点一</li><li>要点二</li></ul>
EOF
```

- `str_replace` 匹配**内层唯一文本**,别带 `> ` / `1. ` 等列表/引用前缀(飞书可能重排编号)。
- 表格单元格改文字:`str_replace` 只匹配该单元格的唯一短语。

## 3. 插入截图 media-insert

按**文本锚点**插(别用易失效 block-id):

```bash
lark-cli docs +media-insert --doc "$DOC" --type image --file "nc-home.png" \
  --selection-with-ellipsis "锚点文本(该块唯一)" --align center --width 720 \
  --caption "图1 · 说明" -q '.ok'
```

- 图落在**锚点块之后**;锚点选各章节末尾的唯一句,图就落章节末。
- 锚点文本别含 shell 会拆词的字符时问题不大,但**别用 `eval` 拼命令**(空格/`·`/`+` 会被重新分词)——直接原生调用、双引号包好。
- 多图串行插(sleep 1),并发会撞版本冲突。

## 4. 插入流程图(Lark 画板 · mermaid)

```bash
# 把 WBMARK 占位块换成画板
lark-cli docs +fetch --doc "$DOC" --scope keyword --keyword "WBMARK1|WBMARK2" --detail with-ids --doc-format xml -q '.data.document.content'  # 取占位 block id
{ echo '<whiteboard type="mermaid">'; cat "$TMP/wb1.mmd"; echo; echo '</whiteboard>'; } > "$TMP/wb1.xml"
lark-cli docs +update --doc "$DOC" --command block_replace --block-id "<占位id>" --content - < "$TMP/wb1.xml"
```

- mermaid `flowchart TD/LR` 即可;节点 id 用 ASCII(A/B/C),标签用引号包中文:`A["注册/登录<br/>手机号+验证码"]`。`<br/>` 会渲染成换行。
- 验证画板非空:`lark-cli whiteboard +query --whiteboard-token "<token>" --output_as raw -q '.data.nodes | length'`(应 >0)。
- `block_replace` 返回体字段可能不含 `.ok`;别只看 `-q '.ok'`(会是 null),改验"占位符是否消失 + `<whiteboard>` 块数"。

## 5. 收尾校验(每次改完必做)

```bash
xml=$(lark-cli docs +fetch --doc "$DOC" --scope full --doc-format xml -q '.data.document.content')
echo "画板:$(echo "$xml"|grep -oE '<whiteboard'|wc -l) 图片:$(echo "$xml"|grep -oE '图[0-9] ·'|wc -l)"
lark-cli docs +fetch --doc "$DOC" --scope outline --doc-format markdown -q '.data.document.content'  # 看章节有无重复
```

- **查重复**:overwrite 若只替换了首块,会残留旧版(v1 + v2 叠加)。看 outline 有没有两套章节;有就说明覆盖没干净,需清掉旧块或重做覆盖。
