# Windows 用の exe（Python なしで動く）を dist\webcollect\ に作る
# 使い方: powershell -ExecutionPolicy Bypass -File build_exe.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean --onefile --name webcollect --paths src run_webcollect.py
New-Item -ItemType Directory -Force dist\webcollect | Out-Null
Move-Item -Force dist\webcollect.exe dist\webcollect\webcollect.exe
Copy-Item -Force config.example.yaml dist\webcollect\config.yaml
Copy-Item -Force docs\使い方.txt dist\webcollect\使い方.txt
Write-Output "dist\webcollect に作りました"
