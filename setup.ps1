# Instala el entorno Python del gestor de JKTIC (Windows PowerShell).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Se requiere Python 3.10 o superior" }
if (-not (Test-Path .venv)) { & $py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m playwright install chromium
$envFile = ".claude\skills\jktic-company\.env"
if (-not (Test-Path $envFile)) { Copy-Item ".claude\skills\jktic-company\.env.example" $envFile }
Write-Host "Listo. Completa $envFile si aun no tiene credenciales."
