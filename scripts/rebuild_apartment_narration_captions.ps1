$ErrorActionPreference = 'Continue'
$root = 'L:\workspace\yinghe-shijie\videos\exports\短视频\The.Apartment.Job.S01E01.2026.1080p.NF.WEB-DL.AAC2.0.H.264'
$builder = 'L:\workspace\yinghe-shijie\skills\yinghe-short-video\scripts\build_short_video.py'
$log = Join-Path $root 'narration_caption_rebuild.log'
"开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content -LiteralPath $log -Encoding UTF8
$done = 0
$pending = 0
$fail = 0

Get-ChildItem -LiteralPath $root -Recurse -Filter '*编辑计划.json' | Sort-Object FullName | ForEach-Object {
    $planPath = $_.FullName
    $plan = Get-Content -LiteralPath $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($plan.annotation_only) { return }
    $dir = $_.DirectoryName
    $outputName = Split-Path -LeafBase $plan.output_video
    $audio = Join-Path $dir ($outputName + '_中文解说.mp3')
    $timing = Join-Path $dir ($outputName + '_中文解说分段时长.json')
    if (-not (Test-Path -LiteralPath $audio) -or -not (Test-Path -LiteralPath $timing)) {
        $pending++
        Add-Content -LiteralPath $log -Value "待生成配音: $planPath" -Encoding UTF8
        return
    }
    Add-Content -LiteralPath $log -Value "开始: $planPath" -Encoding UTF8
    & python $builder --plan $planPath --narration-audio $audio --narration-timing $timing *> (Join-Path $dir 'caption_rebuild.log')
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $plan.output_video)) {
        $done++
        Add-Content -LiteralPath $log -Value "完成: $($plan.output_video)" -Encoding UTF8
    } else {
        $fail++
        Add-Content -LiteralPath $log -Value "失败($LASTEXITCODE): $planPath" -Encoding UTF8
    }
}

Add-Content -LiteralPath $log -Value "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); DONE=$done PENDING=$pending FAIL=$fail" -Encoding UTF8
