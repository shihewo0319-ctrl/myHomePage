# myHomePage

我的浏览器首页 —— 素雅弥散光风格（Calm Aurora）。

一个纯 HTML/CSS/JS 的单文件首页：实时时钟、日期、问候语、可用搜索框（回车直达 Bing）与 8 个快捷入口。无任何外部依赖，离线可用。

## 使用

直接双击打开 `index.html` 即可预览。

## 设为浏览器主页 / 新标签页

- **Chrome / Edge（主页按钮）**：设置 → 启动时 → 打开特定网页或一组网页 → 添加本页路径。
- **新标签页**：Chrome 需要扩展（例如 New Tab Redirect）才能替换新标签页；Edge 可在「启动时」设置；Firefox 可通过 about:preferences 设置主页。
- **推荐做法**：本目录自带服务器脚本，`python3 server.py 43210` 即可启动（除静态页面外还内置 `/favicon/` 网页图标代理，为应用台抓取并缓存各站点真实图标）；或托管到 GitHub Pages。

## 自定义

- **快捷入口**：修改 `index.html` 中 `<nav class="links">` 内的 `<a>` 链接（图标、名称、网址）。
- **搜索**：默认回车跳转 Bing，可改 `form` 的 `action` 换搜索引擎（如 `https://www.google.com/search`）。
- **配色**：调整 `body::before` 中四团低饱和色光的透明度即可进一步增淡/加深背景。

## 技术栈

HTML + CSS + 原生 JavaScript，零依赖、单文件。
