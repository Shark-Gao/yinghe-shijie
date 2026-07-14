[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^https?://')]
    [string]$Url,

    [string]$OutputDirectory,

    [switch]$MetadataOnly,

    [switch]$UpdateTool
)

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent (Split-Path -Parent $skillRoot)
$OutputDirectory = if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    Join-Path $projectRoot 'videos'
} else {
    $OutputDirectory
}
$bundledYtDlp = Join-Path $skillRoot 'bin\yt-dlp.exe'

function Get-YtDlpPath {
    if (Test-Path -LiteralPath $bundledYtDlp) {
        return $bundledYtDlp
    }

    $command = Get-Command 'yt-dlp' -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw 'yt-dlp was not found. Run this script with -UpdateTool or install yt-dlp first.'
}

if ($UpdateTool) {
    $binDirectory = Split-Path -Parent $bundledYtDlp
    New-Item -ItemType Directory -Force -Path $binDirectory | Out-Null
    Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile $bundledYtDlp
    & $bundledYtDlp --version
    if (-not $Url) { exit 0 }
}

if (-not $Url) {
    throw 'Provide -Url, or use -UpdateTool by itself to update yt-dlp.'
}

$ytDlp = Get-YtDlpPath
if ($MetadataOnly) {
    & $ytDlp --skip-download --no-playlist --print '%(id)s | %(title)s | %(uploader)s | %(duration_string)s' -- $Url
    exit $LASTEXITCODE
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$ffmpeg = Get-Command 'ffmpeg' -ErrorAction SilentlyContinue
$arguments = @(
    '--no-playlist',
    '--windows-filenames',
    '--format', 'bv*+ba/b',
    '--merge-output-format', 'mp4',
    '--output', (Join-Path $OutputDirectory '%(extractor_key)s-%(title)s-%(id)s.%(ext)s'),
    '--print', 'after_move:FILE=%(filepath)s',
    '--', $Url
)

if (-not $ffmpeg) {
    Write-Warning 'FFmpeg was not found. Separate video and audio streams may not merge into one MP4 file.'
}

& $ytDlp @arguments
exit $LASTEXITCODE
