"""Relación de módulos Condor (nombre en español -> nombre técnico).

Actualiza modules_es.md desde Condor y lo carga al contexto (hook SessionStart).
Si Condor no responde, carga la última versión guardada. Siempre termina con código 0.

Uso: python fetch_modules.py [article_id]
"""
from __future__ import annotations

from article_sync import SCRIPT_DIR, sync_article

if __name__ == "__main__":
    sync_article(
        env_key="CONDOR_MODULES_ARTICLE_ID",
        default_id="b5a6fee1-f170-afa7-c27b-6af0b48ffdb8",
        out_file=SCRIPT_DIR / "modules_es.md",
        title="Relación de módulos Condor (nombre en español → nombre técnico)",
    )
