$ErrorActionPreference = 'Continue'
$root = 'L:\workspace\yinghe-shijie\videos\exports\短视频\The.Apartment.Job.S01E01.2026.1080p.NF.WEB-DL.AAC2.0.H.264'
$burner = 'L:\workspace\yinghe-shijie\scripts\burn_mapped_subtitles.py'
$log = Join-Path $root 'subtitle_rebuild.log'
"开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content -LiteralPath $log -Encoding UTF8
$done = 0
$fail = 0

Get-ChildItem -LiteralPath $root -Recurse -Filter '*_视频注释版.mp4' | Sort-Object FullName | ForEach-Object {
    $output = $_.FullName
    $backup = Join-Path $_.DirectoryName ($_.BaseName + '_无字幕版.mp4')
    $srt = Join-Path $_.DirectoryName 'original_dialogue_burnin.srt'
    if (-not (Test-Path -LiteralPath $backup) -or -not (Test-Path -LiteralPath $srt)) {
        Add-Content -LiteralPath $log -Value "缺少输入: $output" -Encoding UTF8
        $fail++
        return
    }
    Add-Content -LiteralPath $log -Value "开始: $output" -Encoding UTF8
    & python $burner --input $backup --output $output --srt $srt *> (Join-Path $_.DirectoryName 'subtitle_rebuild.log')
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $output)) {
        $done++
        Add-Content -LiteralPath $log -Value "完成: $output" -Encoding UTF8
    } else {
        $fail++
        Add-Content -LiteralPath $log -Value "失败($LASTEXITCODE): $output" -Encoding UTF8
    }
}

Add-Content -LiteralPath $log -Value "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); DONE=$done FAIL=$fail" -Encoding UTF8
