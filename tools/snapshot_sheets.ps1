# Excel で開いたときの見た目を、シートごとに PNG にする（README とポートフォリオの画像用）
# 使い方: powershell -File tools\snapshot_sheets.ps1 <レポート.xlsx> <出力フォルダ>
param([string]$Xlsx, [string]$OutDir)
$ErrorActionPreference = 'Stop'
$Xlsx = (Resolve-Path $Xlsx).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($Xlsx, 0, $true)
  $areas = @{ '概要' = 'A1:B16'; '一覧' = 'A1:H22'; 'カテゴリ別' = 'A1:R24'; '評価別' = 'A1:L18'; '前回との差分' = 'A1:E14' }
  foreach ($ws in $wb.Worksheets) {
    $name = $ws.Name
    if (-not $areas.ContainsKey($name)) { continue }
    $ws.Activate()
    $rng = $ws.Range($areas[$name])
    $rng.CopyPicture(1, 2)  # 画面の見た目どおり、ビットマップで
    $co = $ws.ChartObjects().Add(0, 0, $rng.Width, $rng.Height)
    $co.Activate()
    Start-Sleep -Milliseconds 300
    $co.Chart.Paste()
    $png = Join-Path $OutDir ("sheet_" + $ws.Index + ".png")
    $co.Chart.Export($png) | Out-Null
    $co.Delete()
    Write-Output "$name -> $png"
  }
  $wb.Close($false)
} finally {
  $xl.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
