# 踩坑清单(动手前先扫一遍)

真实调研中踩过的坑,按"症状 → 原因 → 对策"。

## 飞书写入

- **改动把已插入的图/画板弄没了** → 对含图/画板的文档用了 `overwrite`(它清空全文)。→ 增量编辑一律 `str_replace` / `block_insert_after` / `block_replace`,不 overwrite。
- **文档出现两套章节(v1 + v2 叠加)** → 早期 overwrite 只替换了首块,旧内容残留在后面。→ 改完必查 `--scope outline`;发现重复就清旧块或整篇重覆盖后重插图/画板。
- **`media-insert` 报错或不认链接** → 传了 `/wiki/...` URL。→ 用 `/docx/<id>` URL 或纯 `document_id`;wiki 先 fetch 拿底层 doc_id。
- **`@file` 报 "unsafe file path"** → 用了绝对路径。→ 用 cwd 相对路径,或改 `--content -` 走 stdin。
- **`--yes` 报 unknown flag** → `docs +update` 没有 `--yes`;其 overwrite 风险等级只是 write,直接执行即可。
- **`block_replace` 拿 `-q '.ok'` 得到 null** → 返回体结构不同,不代表失败。→ 验"占位符消失 + `<whiteboard>`/目标块数"。
- **命令 `larkcli: command not found`** → 二进制名是 `lark-cli`(带连字符)。先 `which lark-cli` 确认。
- **`media-insert` caption/selection 被拆词** → 用了 `eval` 拼命令,空格/`·`/`+` 被 shell 重新分词。→ 别用 eval,直接原生调用、参数双引号包好。

## Playwright

- **`browser_evaluate` 报 `xxx is not defined`** → 用了中文变量名。→ 变量名一律 ASCII。
- **弹窗协议只抓到开头一段** → 弹窗虚拟滚动,`innerText` 只返回可见部分。→ 取容器 `textContent`。
- **登录点了没反应 / 白耗验证码** → 用 `browser_evaluate` 里的 `.click()` 提交,React 表单不认。→ 用 `browser_click`(可信原生事件)。
- **`browser_click` 报 "Ref not found" / "strict mode violation"** → ref 随重渲染失效,或选择器命中多个(如"立即上传"既是 `<a>` 又是 `<button>`)。→ 重新 `browser_snapshot` 取 ref;或用更精确选择器(`button:has-text(...)` / `:text-is(...)`)。
- **登录后 `/member` 闪回 `/login`** → SPA 鉴权态加载有延迟。→ 多等、再导航确认;看 `localStorage` token / "退出登录"是否出现。
- **账户掩码号和用户给的号对不上** → 浏览器里可能有**旧会话**,不是目标账号;或号码有出入。→ 停下问用户,必要时登出重登。
- **`/upload` 反复跳回账户中心(即便已登录+实名)** → 上传器还有更后置的门槛(完善卖家资料 / 企业认证)。→ 别硬闯;🔒 标注边界,请用户自行完成后截图。
- **浏览器被占用 "Browser is already in use"** → 上个会话锁残留。→ `pkill -f "<profile 路径关键字>"` + 清 `Singleton*` 锁,再重开。

## 内容与纪律

- **把营销宣称当事实写** → 未溯源。→ 每个数字标注出处页 + "营销话术、数据待核实"。
- **臆造登录态 UI 细节** → 没实测就写。→ 取不到就 🔒 标注,等用户登录/截图。
- **"值得借鉴点"和用户已有能力重复** → 没先摸清我方现状。→ 该节开头明确剔除"我方已具备",只留竞品更好的**设计手法**。
- **越界** → 想提交真实身份/证照或真实下单换样张。→ 绝不做;标注需真实前置/交易方可取样。
- **凭直觉画关键流程** → 想当然认定某个时点("下单即完成""支付即到手")。→ 关键机制别猜,登录 / 让用户实测确认。举例:某授权平台实为"付款后、下载前"还有独立一步选授权身份——直觉画的流程是错的。
- **只记"怎么做"、漏掉"谁不参与"** → 记了流程却没记某个关键相关方是否被绕过。→ 专查:某关键动作是否**无需某方(如被授权本人)同意即可完成**;若是,显式标 ⚠️ 风险。
- **展示物 ≠ 交付物** → 把门面 / 封面 / 演示当成真正交付或计费的标的。→ 明确区分"展示用"和"真正交付 / 计费的对象"。
