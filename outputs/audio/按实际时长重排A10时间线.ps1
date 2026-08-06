$timelinePath = 'L:\workspace\yinghe-shijie\outputs\audio\A10_等长解说时间线.json'
$manifestPath = 'L:\workspace\yinghe-shijie\outputs\audio\A10_等长分段时长.json'
$timeline = Get-Content -Raw -LiteralPath $timelinePath | ConvertFrom-Json
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

function Format-TimeMs([int]$value) {
  $hours = [int][math]::Floor($value / 3600000)
  $remainder = $value % 3600000
  $minutes = [int][math]::Floor($remainder / 60000)
  $remainder = $remainder % 60000
  $seconds = [int][math]::Floor($remainder / 1000)
  $milliseconds = [int]($remainder % 1000)
  return '{0:D2}:{1:D2}:{2:D2}.{3:D3}' -f $hours, $minutes, $seconds, $milliseconds
}

$cursorMs = 0
$gapMs = 200
for ($i = 0; $i -lt $timeline.segments.Count; $i++) {
  $durationMs = [int][math]::Round([double]$manifest.segments[$i].audio_duration * 1000)
  $timeline.segments[$i].start = Format-TimeMs $cursorMs
  $timeline.segments[$i].end = Format-TimeMs ($cursorMs + $durationMs)
  $cursorMs += $durationMs + $gapMs
}
$timeline.retiming = 'packed_by_measured_tts_duration'
$timeline | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $timelinePath -Encoding UTF8
