$baseDir = 'L:\workspace\yinghe-shijie\videos\exports\长视频\A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑'
$audioDir = 'L:\workspace\yinghe-shijie\outputs\audio'
$planPath = Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_长视频计划.json'
$actualTimelinePath = Join-Path $audioDir 'A10_等长实际配音时间线.json'

$plan = Get-Content -Raw -LiteralPath $planPath | ConvertFrom-Json
$actual = Get-Content -Raw -LiteralPath $actualTimelinePath | ConvertFrom-Json
$narrationSeconds = [math]::Round((@($actual.segments | ForEach-Object {[double]$_.audio_duration}) | Measure-Object -Sum).Sum, 3)
$videoSeconds = 986.709

$plan.output_video = Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_长视频完整版_配音版.mp4'
$plan.subtitle_file = Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_中文字幕.srt'
$plan.subtitle_timeline = Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_实际配音时间线.json'
$plan.annotation_file = Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_全片画面注释.json'
$plan.background_music = ''
$plan.burn_captions = $false
$plan.write_subtitles = $true
$plan.mix.source_volume = 0.12
$plan.mix.narration_volume = 1.0
$plan.mix.music_volume = 0.0
$plan.mix.source_audio_note = '使用云扬中文解说作为主声道，源片原声压低到0.12；中文字幕独立交付，不烧录进MP4。'
$plan.narration = [pscustomobject]@{
  provider = 'edge'
  voice = 'zh-CN-YunyangNeural'
  rate = '+10%'
  segments = @($actual.segments)
}
$plan.audio_generation = [pscustomobject]@{
  status = 'generated'
  voice = 'zh-CN-YunyangNeural'
  rate = '+10%'
  output_audio = (Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_等长_Yunyang.mp3')
  auto_mix_audio = (Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_自动混音_正式版.mp3')
  direct_read_audio = (Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_中文字幕直读_Yunyang.mp3')
  direct_read_bgm_reference = (Join-Path $baseDir 'A-10为何围绕一门机炮设计？看懂“疣猪”的生存逻辑_中文字幕直读_背景音乐_正式版.mp3')
  spoken_seconds = $narrationSeconds
  video_seconds = $videoSeconds
  coverage_ratio = [math]::Round($narrationSeconds / $videoSeconds, 4)
}
$plan.source_subtitle_coverage.note = '原始输入SRT覆盖00:00:14.800—00:12:50.566；本次按长视频流程重写并补足全片中文解说时间线，后段解说依据源片画面和主题延展，不宣称是原字幕逐句翻译。'
$plan.preflight_review.revision_notes = @(
  '按用户要求恢复完整长视频云扬男声解说流程，解说时间线覆盖原始16分26秒画面。',
  'MP4不烧录中文字幕；中文字幕作为独立SRT交付，便于在剪映中继续调整。',
  '最终主版本不加入BGM，使用自动混音压低源片原声；另保留直读+BGM参考音频。'
)
$plan.platform_descriptions.general = '一架攻击机为什么不追求高速和隐身，反而把整机围绕一门30毫米机炮设计？本片从GAU-8机炮、钛合金座舱、冗余操纵、发动机布局和近距空中支援任务出发，拆解A-10如何把火力、生存性与前线持续支援组合成一套完整系统。全片配有云扬中文解说，中文字幕单独提供。\n\n#攻击机 #A10 #军事科普 #武器系统'
$plan.platform_descriptions.bilibili = '从一门机炮开始，拆解A-10“疣猪”的整机取舍：为什么它要低空、慢速、重装甲？GAU-8的后坐力、贫铀弹、液压冗余、钛合金座舱和发动机布局，如何共同服务于近距空中支援？全片配有云扬中文解说，中文字幕单独提供。\n\n#A10 #军事科普 #航空工程 #武器系统'
$plan | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $planPath -Encoding UTF8
