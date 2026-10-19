$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { & (Join-Path $PSScriptRoot 'setup.ps1') }
& $projectPython -m streamlit run app.py
