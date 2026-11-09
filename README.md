# TXT 在线订阅 → M3U 在线订阅

GitHub Actions 每 6 小时拉取一个或多个 TXT 网址，转换并合并为 UTF-8 扩展 M3U，更新仓库根目录的 live.m3u。播放器填写固定 Raw 链接即可，无须本地文件、服务器或 GitHub Pages。

## 多网址配置

Secret 名称仍然使用 TXT_URL；在它的值中每行填写一个完整订阅网址，直接换行，不要用逗号连接。单网址配置保持兼容。

```text
https://example.com/source-a.txt
https://example.org/source-b.txt
https://example.net/source-c.txt
```

上面仅为写法示例，请全部替换成真实订阅网址。你现有的 https://jk.html-5.me/i/03537.txt 可以作为其中一行。

- 按网址填写顺序合并，各源内部频道顺序保留。
- 相同网址只下载一次，空行及以 # 开头的整行备注忽略。
- 频道名、分组、播放地址全部相同的条目自动去重；同名但播放地址不同的频道保留为多个条目，供播放器切换。分组不同也保留。
- 每个源独立解析分组，后一份没有分组的源不会继承前一份的最后分组。
- 任何一个源拉取失败、浏览器加载失败或没有有效频道，整次更新失败并保留上一份完整 M3U；不会用缺失部分来源的列表覆盖旧文件。日志用来源序号定位失败项。
- 最终只生成一个 live.m3u，播放器依然只需订阅一个网址。此版本不为每个输入源分别生成独立文件。
- 输入须是频道文本订阅地址。普通网站首页、文章页或只有下载按钮的网页，需要先取得频道列表直链；本版不会自动从任意网页寻找链接。

升级时同时替换 convert.py 和 .github/workflows/update.yml。工作流总超时调整为 30 分钟；来源较多或响应较慢仍可能超时，失败时旧列表保留。

## 已部署旧版时如何修复

本版增加普通 Chromium 浏览器加载：HTTP 请求返回 HTML 或拉取失败时，尝试在隔离的浏览器会话中打开原始网址，读取浏览器展示的纯文本。原始网址无需修改，不要手动添加 `?i=1`。

1. 用本包中的 convert.py 覆盖仓库根目录同名文件。
2. 用本包中的 .github/workflows/update.yml 覆盖仓库同路径文件。必须一起更新，因为工作流增加了 Playwright 和 Chromium 安装步骤。
3. 保持原有 TXT_URL Secret，手动运行 Update M3U。
4. 生成结果仍是根目录 live.m3u，播放器订阅链接不变。

针对 https://jk.html-5.me/i/03537.txt ：本次已在浏览器中观察到正常频道列表，以及自动附加的 `?i=1` 参数。这与托管商公开说明的 JavaScript/Cookie 浏览器验证行为相符。普通 Python 请求收到 HTML 并不代表 TXT 内容有错。

验证范围：已通过本地解析、HTTP/浏览器分支选择、浏览器文本读取模拟、失败保留旧输出及 YAML 检查；浏览器实际打开原站成功。尚未在你的 GitHub Actions 环境实测本版，因此不能保证其运行 IP 能获得相同响应。浏览器会按网站的正常行为运行页面，不提供验证码识别、指纹伪装或手工构造验证 Cookie；遇到交互验证或访问拒绝会失败并保留旧列表。长期可靠的做法是向源提供者索取可供程序直接读取的镜像地址。

## 网页部署步骤

1. 在 GitHub 新建 Public 仓库，建议命名 iptv-m3u，勾选添加 README，默认分支使用 main。
2. 解压本压缩包。把 convert.py 上传至仓库根目录。README.md 是使用说明，可以替换仓库原说明。
3. 创建工作流：仓库 → Add file → Create new file，文件名填写 `.github/workflows/update.yml`，复制压缩包内同路径 update.yml 的全部内容并提交。注意不是把 update.yml 上传到根目录，也不是把压缩包直接上传。
4. 仓库 → Settings → Secrets and variables → Actions → Secrets → New repository secret：Name 填 TXT_URL；Secret 填你的 TXT 在线直链，多个网址每行一个。网址应返回频道文本，不能是网页预览地址。
5. 仓库 → Actions → Update M3U → Run workflow → 选择 main → Run workflow。首次工作流若因为尚未配置 TXT_URL 失败，完成第 4 步后重新运行即可。
6. 出现绿色成功标记后，仓库根目录会生成 live.m3u。在播放器添加以下网址，替换用户名和仓库名：

   https://raw.githubusercontent.com/你的GitHub用户名/iptv-m3u/main/live.m3u

   也可打开仓库里的 live.m3u，点击 Raw 后复制浏览器最终地址。不要使用 github.com/.../blob/... 的预览页面地址。

## 支持的 TXT 格式

```text
央视频道,#genre#
CCTV-1 综合,https://example.com/cctv1.m3u8
CCTV-2 财经,https://example.com/cctv2.m3u8
卫视频道,#genre#
湖南卫视,https://example.com/hunan.m3u8
```

频道行必须用英文逗号分隔，第一次逗号之后的地址完整保留，不会因 URL 参数内的逗号而截断。支持保留频道顺序、同名不同地址的频道和 #genre# 分组，完全相同的条目去重；支持 UTF-8（含 BOM）、GB18030 和有 BOM 的 UTF-16。允许 HTTP、HTTPS、RTSP、RTMP、RTMPS、UDP、RTP 频道地址。这里只转换格式，不检测播放、不转码、不把同名频道合并为单条多线路记录、不处理额外鉴权头或特殊 TVBox 语法。

## 自动更新与错误处理

- 默认 cron 为 `17 */6 * * *`：每 6 小时的第 17 分钟运行一次，使用 UTC。GitHub 定时任务可能延迟，不保证准点。
- 手动运行会立即进入队列；修改 Secret 不会自动触发，需要手动运行一次或等待定时任务。
- 无法获得有效频道文本、编码不支持或未识别到频道时，任务失败并保留上一次已发布文件；日志不会输出 TXT_URL。
- 本版在 HTTP 失败或返回 HTML 时先尝试浏览器加载；两种方式均失败后才停止，不会把验证页面发布成 M3U。每次运行需安装 Chromium，耗时及流量高于旧版。
- 有频道时，无法识别的其他行会跳过，日志给出跳过行数。首次部署请抽查频道数和分组。
- 内容未变时不创建提交。公开仓库连续 60 天没有活动，定时工作流可能被 GitHub 自动停用；即使源始终未变也需要留意 Actions，必要时启用后手动运行。
- 如果 git push 返回 403：检查 Settings → Actions → General 中的工作流写权限及组织限制；分支保护规则也可能阻止机器人直接提交。无需个人访问令牌。
- 播放器可能缓存列表，更新后要刷新订阅。若播放器所在网络无法访问 raw.githubusercontent.com，这个链接也无法使用；需改用能访问的静态托管。

## 公开范围

方案需要公开仓库以便播放器匿名读取 Raw。TXT_URL 存在 Secret 中，但生成结果以及它的 Git 历史是公开的，包括频道地址中的任何令牌。只发布可以公开的直播源。需要私密订阅时应改用带鉴权的托管方式。

## 官方参考

- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs
- https://github.com/actions/setup-python
- https://github.com/actions/checkout
- https://playwright.dev/python/docs/ci-intro
- https://forum.infinityfree.com/t/browser-security-system-features-and-limitations/49353
