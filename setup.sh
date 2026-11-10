#!/usr/bin/env bash
# Instala el entorno Python del gestor de JKTIC (Linux/macOS).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Se requiere Python 3.10 o superior"; exit 1; }
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
[ -f .claude/skills/jktic-company/.env ] || cp .claude/skills/jktic-company/.env.example .claude/skills/jktic-company/.env
.venv/bin/python -m playwright install chromium
echo "Listo. Completa .claude/skills/jktic-company/.env si aún no tiene credenciales."
