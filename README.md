# TXT 在线订阅 → M3U 在线订阅

GitHub Actions 每 6 小时拉取一次你的 TXT 网址，转换为 UTF-8 扩展 M3U，更新仓库根目录的 live.m3u。播放器填写固定 Raw 链接即可，无须本地文件、服务器或 GitHub Pages。

## 网页部署步骤

1. 在 GitHub 新建 Public 仓库，建议命名 iptv-m3u，勾选添加 README，默认分支使用 main。
2. 解压本压缩包。把 convert.py 上传至仓库根目录。README.md 是使用说明，可以替换仓库原说明。
3. 创建工作流：仓库 → Add file → Create new file，文件名填写 `.github/workflows/update.yml`，复制压缩包内同路径 update.yml 的全部内容并提交。注意不是把 update.yml 上传到根目录，也不是把压缩包直接上传。
4. 仓库 → Settings → Secrets and variables → Actions → Secrets → New repository secret：Name 填 TXT_URL；Secret 填你的 TXT 在线直链。此网址应直接返回频道文本，不能是网页预览地址。
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

频道行必须用英文逗号分隔，第一次逗号之后的地址完整保留，不会因 URL 参数内的逗号而截断。支持保留频道顺序、重复频道和 #genre# 分组；支持 UTF-8（含 BOM）、GB18030 和有 BOM 的 UTF-16。允许 HTTP、HTTPS、RTSP、RTMP、RTMPS、UDP、RTP 频道地址。这里只转换格式，不检测播放、不转码、不合并多线路、不处理额外鉴权头或特殊 TVBox 语法。

## 自动更新与错误处理

- 默认 cron 为 `17 */6 * * *`：每 6 小时的第 17 分钟运行一次，使用 UTC。GitHub 定时任务可能延迟，不保证准点。
- 手动运行会立即进入队列；修改 Secret 不会自动触发，需要手动运行一次或等待定时任务。
- 拉取失败、返回 HTML、编码不支持或未识别到频道时，任务失败并保留上一次已发布文件；日志不会输出 TXT_URL。
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
