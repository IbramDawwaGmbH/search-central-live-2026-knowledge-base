param([Parameter(Mandatory = $true)][string]$List, [int]$Long = 1600, [int]$Quality = 87)
# Writes JPEG previews with Windows' own image decoders (WPF/WIC). HEIC needs the "HEIF Image Extensions" from
# the Microsoft Store; the Python HEIF plugin is not used. Called by ingest.py.
# $List: UTF-8 text, one "source<TAB>destination<TAB>orientation" per line. orientation is the EXIF value 1-8
# (pass 1 for HEIC: its decoder already applies the rotation). The long side is scaled down to $Long pixels.
# Prints "ok<TAB>destination<TAB>WxH" or "ERR<TAB>source<TAB>message" per line. Never touches the source.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName PresentationCore
foreach ($line in Get-Content -LiteralPath $List -Encoding UTF8) {
  if (-not $line.Trim()) { continue }
  $src, $dst, $o = $line -split "`t"
  $fs = $null; $out = $null
  try {
    $fs = [System.IO.File]::OpenRead($src)
    $dec = [System.Windows.Media.Imaging.BitmapDecoder]::Create($fs, [System.Windows.Media.Imaging.BitmapCreateOptions]::None, [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad)
    $frame = $dec.Frames[0]
    $scale = [Math]::Min(1.0, $Long / [Math]::Max($frame.PixelWidth, $frame.PixelHeight))
    $angle = 0; $fx = 1; $fy = 1
    switch ([int]$o) { 2 { $fx = -1 } 3 { $angle = 180 } 4 { $fy = -1 } 5 { $angle = 90; $fx = -1 } 6 { $angle = 90 } 7 { $angle = 270; $fx = -1 } 8 { $angle = 270 } }
    $g = New-Object System.Windows.Media.TransformGroup
    if ($angle) { $g.Children.Add((New-Object System.Windows.Media.RotateTransform -ArgumentList $angle)) }
    $g.Children.Add((New-Object System.Windows.Media.ScaleTransform -ArgumentList ($scale * $fx), ($scale * $fy)))
    $bmp = New-Object System.Windows.Media.Imaging.TransformedBitmap -ArgumentList $frame, $g
    if ($bmp.Format.BitsPerPixel -ne 24) { $bmp = New-Object System.Windows.Media.Imaging.FormatConvertedBitmap -ArgumentList $bmp, ([System.Windows.Media.PixelFormats]::Bgr24), $null, 0 }
    $enc = New-Object System.Windows.Media.Imaging.JpegBitmapEncoder
    $enc.QualityLevel = $Quality
    $enc.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bmp))
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    $out = [System.IO.File]::Create("$dst.part"); $enc.Save($out); $out.Close(); $out = $null
    Move-Item -LiteralPath "$dst.part" -Destination $dst -Force
    "ok`t$dst`t$($bmp.PixelWidth)x$($bmp.PixelHeight)"
  } catch {
    "ERR`t$src`t$($_.Exception.Message -replace '\s+', ' ')"
  } finally {
    if ($out) { $out.Close() }
    if ($fs) { $fs.Close() }
  }
}
