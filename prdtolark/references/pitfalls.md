# 11 个关键坑

按重要性排序。每个坑都有"现象 / 原因 / 修复"三段。

## 1. `--overwrite` 让白板 media token 失效

**现象**: 第一次 `whiteboard +update --overwrite` 成功创建 N 节点;第二次再 `--overwrite` 写入(用同样 token)返回 `invalid arg (2890002)`。**dry-run 完全通过、错误码没明说 token 失效**。

**原因**: `--overwrite` 删掉所有白板节点 → 节点引用的 image token 失去依附 → token 失效。

**修复**: 每次写入前必须重新跑 1.1(批量 `docs +media-upload --parent-type whiteboard`)。维护 `tokens.json` 复用是行不通的,因为 token 会失效。

---

## 2. docx 中 `<img src="<token>"/>` src 被忽略

**现象**: 写入 `<img name="x.png" src="<已上传 file_token>" width=240/>`,fetch 出来 src 变成了别的 token,实际渲染是 1x1 空图。

**原因**: 飞书的 docx OpenAPI 在 `update` / `create` / `block_replace` 时,img 的 src **只在内部上传链路中产生**,不接受外部传入的现有 token。

**修复**: 不要走"先上传再写 src"路径,改用 `docs +media-insert`(自动建 block + 上传 + 关联)。

---

## 3. `block_move_after / block_copy_insert_after` 在 lark-cli 1.0.46 仍 broken

**现象**: 
```
"src_block_ids": "doxlgVVDkFGn2Wq4qFaU6YeQurc"
```
在 dry-run body 里能看到,但实际请求被服务器拒绝: `requires content or src_block_ids but both were empty`。

**原因**: 服务器期望数组,客户端传字符串;直接调原生 API 传 `["xxx"]` 数组也同样失败 — 可能服务器有自己的限制或字段命名不同。

**修复**: 不要走 move / copy 路径。把图放在 grid column 内的需求,**目前**无解;改顺序结构(图作为顶级 block)。

---

## 4. `+media-insert --selection-with-ellipsis` 只插顶级 block

**现象**: selection 选中 grid column 内的某段文字 "abc",`+media-insert` 看似成功,但 fetch 出来图被放在 `</grid>` 之后,不在 column 内。

**原因**: `+media-insert` 的实现固定在文档顶级 block 树插入,不会下沉到容器(grid/column/callout)内。

**修复**: 接受现实 — PRD 章节用顺序结构(图在上、说明在下),不强求左图右文分栏。

---

## 5. `docs +media-upload --parent-type docx` 报 params error

**现象**: 上传时传 `--parent-type docx --parent-node <docx_token>`,报 `upload media failed: [1061002] params error`。

**原因**: `--parent-type` 的合法枚举是 `docx_image | docx_file | whiteboard`(不含 `docx`); 且 docx 类型的 `--parent-node` 是 **block_id**,不是 docx_token。

**修复**: 
- 想直接拿 docx 域 token: 需要先有目标 image block_id — 但通常不会这么做
- 实际场景: 直接用 `docs +media-insert` 一步到位

---

## 6. markdown 模式 content 里 `<whiteboard>` 不被解析

**现象**: `docs +update --doc-format markdown --content '...<whiteboard type="mermaid">code</whiteboard>...'` 写入后,fetch 看到 `<pre><code>` 代码块包含整个 whiteboard XML 文本。

**原因**: markdown 模式只解析 markdown 语法,XML 容器标签被当字面量处理。

**修复**: 两段法:
1. markdown str_replace 占位写入(允许出现 `<pre>`)
2. block_replace 把 `<pre>` 替换为真正的 `<whiteboard>` XML(默认 doc-format=xml)

---

## 7. `--content @path` 必须相对路径

**现象**: `--content @/tmp/replace.md` 报错: 
> --content: invalid file path "/tmp/replace.md": --file must be a relative path within the current directory

**原因**: lark-cli 安全限制。

**修复**: `cp /tmp/xxx.md ./xxx.md` 后用 `@./xxx.md`。

---

## 8. `block_delete --block-id` 逗号批量删 → field validation failed

**现象**: `--block-id "id1,id2,id3"` 报 `HTTP 400: field validation failed`。

**原因**: lark-cli 1.0.46 把字符串当单个 id 解析,逗号被视为 id 的一部分(然后服务器拒绝)。

**修复**: 循环逐个删:
```bash
for bid in id1 id2 id3; do
  lark-cli docs +update --command block_delete --block-id "$bid" ...
done
```

---

## 9. str_replace pattern 跨块匹配,XML 模式不行

**现象**: `--command str_replace --doc-format xml --pattern "标题...结尾"` 报 multiple locations 或不匹配。

**原因**: XML 模式 `--pattern` 仅支持**行内匹配**,不能跨 block / 跨段落。

**修复**: 跨块替换用 `--doc-format markdown`(支持 `prefix...suffix` 省略号语法跨多块匹配);或单块用 `block_replace`。

---

## 10. PNG > 2000px 不能用 Read

**现象**: Read 一张 2560×2560 的预览图,报 `image dimension limit (2000px)`。

**原因**: Claude Read 对 many-image requests 有 2000px 上限。

**修复**: `sips -Z 1500 wb_final.png --out wb_check.png`,再 Read `wb_check.png`。

---

## 11. lark-cli `_notice.update` 提示

每次响应里出现 `"_notice": { "update": { "current": "1.0.42", "latest": "1.0.46" } }` 即提示用户跑 `lark-cli update`。但要注意 1.0.46 仍有上面坑 #3 的 bug,**升级不能修复 block_move_after**。
