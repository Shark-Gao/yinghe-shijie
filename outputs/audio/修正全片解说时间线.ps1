$timelinePath = 'L:\workspace\yinghe-shijie\outputs\audio\A10_等长解说时间线.json'
$durationMs = 986709

function Format-TimeMs([int]$value) {
  $hours = [int][math]::Floor($value / 3600000)
  $remainder = $value % 3600000
  $minutes = [int][math]::Floor($remainder / 60000)
  $remainder = $remainder % 60000
  $seconds = [int][math]::Floor($remainder / 1000)
  $milliseconds = [int]($remainder % 1000)
  return '{0:D2}:{1:D2}:{2:D2}.{3:D3}' -f $hours, $minutes, $seconds, $milliseconds
}

$timeline = Get-Content -Raw -LiteralPath $timelinePath | ConvertFrom-Json
$count = $timeline.segments.Count
for ($i = 0; $i -lt $count; $i++) {
  $startMs = [int][math]::Round($durationMs * $i / $count)
  $endMs = [int][math]::Round($durationMs * ($i + 1) / $count)
  $timeline.segments[$i].start = Format-TimeMs $startMs
  $timeline.segments[$i].end = Format-TimeMs $endMs
}
$timeline.video_duration = Format-TimeMs $durationMs
$timeline | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $timelinePath -Encoding UTF8
