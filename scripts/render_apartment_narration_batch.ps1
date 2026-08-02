$ErrorActionPreference = 'Continue'
$workspace = 'L:\workspace\yinghe-shijie'
$root = 'L:\workspace\yinghe-shijie\videos\exports\短视频\The.Apartment.Job.S01E01.2026.1080p.NF.WEB-DL.AAC2.0.H.264'
$batchLog = Join-Path $root 'render_narration_batch.log'
Set-Location -LiteralPath $workspace

"开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content -LiteralPath $batchLog -Encoding UTF8
$plans = Get-ChildItem -LiteralPath $root -Recurse -Filter '*编辑计划.json' | ForEach-Object {
    $plan = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $plan.annotation_only) {
        [PSCustomObject]@{ Path = $_.FullName; Output = $plan.output_video }
    }
} | Sort-Object Path

$done = 0
$failed = 0
foreach ($item in $plans) {
    if (Test-Path -LiteralPath $item.Output) {
        Add-Content -LiteralPath $batchLog -Value "跳过已完成: $($item.Path)" -Encoding UTF8
        $done++
        continue
    }
    $dir = Split-Path -Parent $item.Path
    $log = Join-Path $dir 'render.log'
    Add-Content -LiteralPath $batchLog -Value "开始: $($item.Path)" -Encoding UTF8
    & python '.\skills\yinghe-short-video\scripts\produce_short_video.py' --plan $item.Path *> $log
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $item.Output)) {
        $done++
        Add-Content -LiteralPath $batchLog -Value "完成: $($item.Output)" -Encoding UTF8
    } else {
        $failed++
        Add-Content -LiteralPath $batchLog -Value "失败($LASTEXITCODE): $($item.Path)" -Encoding UTF8
    }
}

Add-Content -LiteralPath $batchLog -Value "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); DONE=$done FAIL=$failed" -Encoding UTF8
