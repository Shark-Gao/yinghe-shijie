---
name: download-authorized-video
description: Inspect and download an authorized online video into the Yinghe Shijie project. Use when a user supplies a YouTube or supported video URL and asks to save it locally for permitted testing, editing, archiving, or production.
---

# Authorized video download

Save only videos the user is permitted to download, such as owned content, creator-authorized content, or sources expressly available for offline saving. Save output to the project `videos/` directory by default. Do not download DRM-protected content or bypass sign-in, paywalls, or access controls.

## Workflow

1. Confirm that the user supplied a URL and has permission to save the source.
2. Read metadata before download:

   ```powershell
   powershell -ExecutionPolicy Bypass -File skills/download-authorized-video/scripts/download-authorized-video.ps1 -Url '<URL>' -MetadataOnly
   ```

3. Save the video after permission is confirmed:

   ```powershell
   powershell -ExecutionPolicy Bypass -File skills/download-authorized-video/scripts/download-authorized-video.ps1 -Url '<URL>'
   ```

4. Report the absolute output path, title, duration, and final format. Diagnose failures with `-MetadataOnly`; do not redirect users to third-party online download sites.

## Script behavior

- Prefer `bin/yt-dlp.exe` inside this skill; fall back to `yt-dlp` on PATH.
- Use FFmpeg on PATH to merge video and audio when available.
- Use the output template `videos/<platform>-<title>-<video-id>.<ext>`.
- Accept `-OutputDirectory` for another destination.
- Use `-UpdateTool` to get the latest official `yt-dlp.exe` from its GitHub release.

## Boundaries

- Do not handle DRM, paid content, login bypasses, or access-control bypasses.
- Do not use browser cookies, account credentials, or proxies for restricted media.
- Use only the bundled script and official yt-dlp GitHub releases.
