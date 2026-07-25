---
name: download-authorized-video
description: 当用户提供 YouTube 或其他受支持的视频链接，并要求将有权使用的视频保存到硬核视界项目中进行测试、剪辑、归档或制作时使用。默认把源视频保存到 `videos/raw/`，方便选题、字幕、审片和短视频技能统一查找。
---

# 授权视频下载

只保存用户有权下载的视频，例如用户自己发布的视频、创作者明确授权的视频，或明确允许离线保存的来源。默认将源文件保存到项目的 `videos/raw/` 目录。不得下载受 DRM 保护的内容，也不得绕过登录、付费墙或其他访问控制。

## 工作流程

1. 确认用户提供了视频链接，并确认用户有权保存该源片。
2. 下载前先读取元数据：

   ```powershell
   powershell -ExecutionPolicy Bypass -File skills/download-authorized-video/scripts/download-authorized-video.ps1 -Url '<URL>' -MetadataOnly
   ```

3. 用户确认授权后保存视频：

   ```powershell
   powershell -ExecutionPolicy Bypass -File skills/download-authorized-video/scripts/download-authorized-video.ps1 -Url '<URL>'
   ```

4. 报告绝对输出路径、标题、时长、频道、源链接和最终格式。遇到失败时使用 `-MetadataOnly` 诊断；不得把用户引导到第三方在线视频下载网站。

## 脚本行为

- 优先使用本技能内置的 `bin/yt-dlp.exe`；找不到时再使用系统 PATH 中的 `yt-dlp`。
- 如果系统有 FFmpeg，则用它合并视频流和音频流。
- 默认输出模板为 `videos/raw/<platform>-<title>-<video-id>.<ext>`。
- 可以用 `-OutputDirectory` 指定其他输出目录。
- 使用 `-UpdateTool` 时，从 yt-dlp 官方 GitHub 发布页获取最新版 `yt-dlp.exe`。

## 边界

- 不处理 DRM、付费内容、登录绕过或访问控制绕过。
- 不使用浏览器 Cookie、账号凭据或代理访问受限媒体。
- 只使用本技能内置脚本和 yt-dlp 官方 GitHub 发布文件。
