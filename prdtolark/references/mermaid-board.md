# Step 2: 文字流程 → mermaid 白板

把 PRD 中"主流程一/二/三/四"这种 ol 文字步骤改成 mermaid 流程图嵌入到 docx。

## 适用场景

- 5.1 核心流程章节有 4 个 ol(主流程一/二/三/四),想合并成一张可视化流程图
- 想把"判断分支""跳转关系"做成 flowchart

## 完整流程

### 2.1 设计 mermaid 流程图

**推荐结构**:`flowchart LR` + N 个 `subgraph` 分组(每个 subgraph 一个主流程)。

```
flowchart LR
    Start([入口]) --> Wallet[共同 hub]

    subgraph A[流程一·查看流水]
        direction TB
        A1[...] --> A2{...}
        A2 -->|是| A3[...]
    end

    subgraph B[流程二·申请提现]
        direction TB
        B1[...] --> B2{...}
    end

    Wallet --> A1
    Wallet --> B1
```

**注意**:
- `subgraph` 内 `direction TB`(自上而下)避免子图过宽
- 节点文字用 `<br/>` 换行 — 但飞书 markdown 解析会把 `<br/>` 转为换行符(\n),mermaid 渲染时仍当 br 处理
- 节点标签里**避免**双引号、方括号等特殊字符;中文 / `·` / `→` 都可用

### 2.2 写入 PRD (两段法)

> ⚠️ **关键坑**: `docs +update --doc-format markdown` 的 content 里 `<whiteboard>` **不会**被识别,会变成 `<pre><code>` 代码块。

**正确做法 — 两步走**:

```bash
# Step 2a: markdown str_replace 替换原 ol 段为新 whiteboard XML
#   - 因为 markdown 模式跨块支持(prefix...suffix),所以可以一次性替换多块 ol
#   - 但 <whiteboard> 会被当 <pre> — 这是已知问题,先这样写
#   - content 文件保存为 ./replace.md

# 准备文件
cat > replace.md << 'EOF'
<whiteboard type="mermaid">flowchart LR
    Start([...]) --> ...
</whiteboard>
EOF

# 替换
lark-cli docs +update --api-version v2 --doc $DOC \
  --command str_replace \
  --doc-format markdown \
  --pattern "主流程一:查看交易流水...完成后通过消息中心通知用户下载" \
  --content "@./replace.md" \
  --as user

# 此时会产生:
#   - 一个空 h4(从 mermaid 的 # 标题被解析)
#   - 一个 pre 代码块(包含 mermaid 代码 + </whiteboard> 文本)

# Step 2b: fetch 拿到这两个 block_id,然后修复
lark-cli docs +fetch --api-version v2 --doc $DOC --detail with-ids > /tmp/fetch.txt
# grep 找空 <h4 id="..."></h4> + <pre id="...">

# 删空 h4
lark-cli docs +update --api-version v2 --doc $DOC \
  --command block_delete --block-id "<empty_h4_id>" --as user

# block_replace pre 为真正的 whiteboard (XML 模式默认即可)
cat > replace.md << 'EOF'
<whiteboard type="mermaid">flowchart LR
    ...真正的 mermaid 代码...
</whiteboard>
EOF
lark-cli docs +update --api-version v2 --doc $DOC \
  --command block_replace --block-id "<pre_id>" \
  --content "@./replace.md" --doc-format xml --as user
```

### 2.3 验证

```bash
# 1. fetch 看到 <whiteboard token="..." type="mermaid"> 标签
# 2. 提取 token 后导出预览
lark-cli whiteboard +query --whiteboard-token "<wb_token_from_fetch>" \
  --output_as image --output ./wb_5_1.png --as user
sips -Z 1500 wb_5_1.png --out wb_check.png
# Read wb_check.png
```

## 失败排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 警告 `Whiteboard content parse failed` | markdown 模式 content 里 `<whiteboard>` 没被识别 | 走 2b 修复 |
| 写入后看到 `<pre><code>` 代码块 | 同上 | 同上 |
| pattern matched multiple locations | pattern 不够独特 | 用更长的 prefix / suffix |
| mermaid 在白板里渲染异常 | 节点标签有特殊字符 / subgraph 名字带方括号 | 简化字符,subgraph 名只用中文+`·` |
