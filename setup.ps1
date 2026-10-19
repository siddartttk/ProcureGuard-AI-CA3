$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrapPython = $null
    $candidates = @()
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $discovered = & $pyLauncher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $candidates += $discovered }
    }
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($systemPython) { $candidates += $systemPython.Source }
    $candidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            try {
                & $candidate -c 'import sys; assert sys.version_info >= (3,11)' 2>$null
                if ($LASTEXITCODE -eq 0) { $bootstrapPython = $candidate; break }
            } catch { }
        }
    }
    if (-not $bootstrapPython) { throw 'Install Python 3.11 or newer, then run setup.ps1 again.' }
    & $bootstrapPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
Write-Host 'Installing pinned application and test dependencies. The first setup needs internet access.'
& $venvPython -m pip install -r requirements-tested.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your connection and rerun setup.ps1.' }
Write-Host 'Setup complete. Run START_DEMO.cmd.'
