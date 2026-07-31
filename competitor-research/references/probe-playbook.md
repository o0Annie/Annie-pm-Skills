# 侦察手册 — Playwright 实测竞品

> 目标:高信噪比地抓取竞品公开与登录态内容。**优先 `browser_evaluate` 批量取结构化数据**,而非逐个 `browser_click`(ref 易失效)。SPA 一律先 `setTimeout` 等渲染。

## 1. 公开页结构化抓取

导航后用一次 evaluate 把导航、模块文本、标签、定价、宣称一网打尽:

```js
async () => {
  await new Promise(r => setTimeout(r, 2000)); // 等 SPA 渲染
  const links = [...document.querySelectorAll('a')].map(a => ({t:(a.innerText||'').trim(), u:a.getAttribute('href')})).filter(x=>x.t);
  const t = document.body.innerText;
  return { totalLinks: links.length, links: links.slice(0,60), text: t.replace(/\n{2,}/g,'\n').slice(0,3000) };
}
```

- **变量名用 ASCII**(中文变量名在 `browser_evaluate` 里可能报 `xxx is not defined`)。
- 找"会员/付费/等级"等要证伪的东西:扫全站链接 + 正文关键词,拿"命中为空"作反证(例:`memberish:[]` + `bodyHasMemberTier:false` 证明无会员体系)。

## 2. 宣称溯源(反营销话术)

对每个营销数字,定位出处页,别当事实:

```js
() => {
  const t = document.body.innerText;
  const kw = ['180','国家','百倍','效率','一站式','覆盖'];
  const hits = {};
  kw.forEach(k => { const i=t.indexOf(k); hits[k]= i<0?null:t.slice(Math.max(0,i-30),i+50).replace(/\s+/g,' '); });
  return { url: location.href, hits };
}
```

- 首页没有 ≠ 不存在;常在「关于我们 / 公司简介」的"核心优势"里。文档里写明"来源:XX 页,首页无此表述,营销话术待核实"。

## 3. 弹窗协议提取(合规承诺书类)

注册/登录页的《XX 协议》多为点击弹窗,且**虚拟滚动**——`innerText` 只给可见部分,必须取容器 `textContent`:

```js
async () => {
  // 先点开协议
  const el = [...document.querySelectorAll('a,span,button,div')].find(e => /合规承诺书/.test(e.textContent||'') && (e.textContent||'').length<30);
  if (el) el.click();
  await new Promise(r=>setTimeout(r,1200));
  // 取包含正文的模态容器 textContent(不受可见性影响)
  const node = [...document.querySelectorAll('div,section')].find(e => /第一条/.test(e.textContent||'') && (e.textContent||'').length<8000);
  const body = (node?node.textContent:'').replace(/\s*\n\s*/g,'\n').replace(/\n{2,}/g,'\n').trim();
  const clauses = [...body.matchAll(/第[一二三四五六七八九十]+条[^\n0-9]{0,24}/g)].map(m=>m[0].trim());
  return { clauses, body };
}
```

## 4. 截图

```
browser_take_screenshot  fullPage=true  filename="nc-home.png"   // 存 cwd
```
- 长图(资产详情/上传器)会很大;>4MB 的 PNG:`sips -s format jpeg -s formatOptions 80 x.png --out x.jpg`。

## 5. 登录态实测(需用户配合)

公开抓不到的上传器、账户中心、协议样张,走登录。**手机号 + 验证码**最可行(微信扫码你看不到二维码)。

流程:
1. `browser_navigate` 到 `/login`,`browser_evaluate` 确认输入框 placeholder(如"请输入手机号""请输入验证码")与"获取验证码"按钮。
2. `browser_type` 填手机号 → **`browser_click`(原生可信点击)** 点"获取验证码";确认按钮变倒计时(如 `60s`)即已发送。
3. **向用户要验证码**(结束本轮,等用户回复)。
4. `browser_type` 填验证码 → **`browser_click` 点"登录"**。
   - ⚠️ **别用 `browser_evaluate` 的 `.click()` 提交登录**:React 表单可能不触发,还会白白消耗一次验证码。原生 `browser_click` 才是可信事件。
5. 登录后 SPA 常有跳转延迟,`/member` 首次可能闪回 `/login`——多等一下、再 `browser_navigate` 确认 `localStorage` 里有 token / 页面出现"退出登录"。
6. 核对**账户掩码号**与用户给的号是否一致;不一致要问用户(可能是浏览器里的旧会话,不是目标账号)。

**登录后典型探查**:账户中心菜单结构、`/upload` 上传器(多角度人脸位 + 示例参考)、配额规则、协议勾选项。取不到(需实名/企业认证/真实交易)就 🔒 标注,不越界。

## 6. React 组件点击

侧栏/菜单用 JS `.click()` 常不触发路由。改用带 ref 的 `browser_click`:先 `browser_snapshot` 拿 `ref`,再 `browser_click target=<ref>`。ref 会随重渲染失效,失效就重新 snapshot。
