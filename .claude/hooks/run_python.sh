#!/usr/bin/env bash
# Ejecuta un script con el Python del .venv del proyecto (Linux: bin/, Windows/Git Bash: Scripts/).
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
py="$root/.venv/bin/python"
[ -x "$py" ] || py="$root/.venv/Scripts/python.exe"
if [ ! -x "$py" ]; then
  echo "[gestor-jktic] Falta el entorno .venv: ejecuta setup.sh (Linux) o setup.ps1 (Windows)."
  exit 0
fi
exec "$py" "$@"
