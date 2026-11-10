"""Catálogo de instrucciones del gestor (artículo "JKTIC COMPANY GESTOR CATALOGO INDEX").

Actualiza catalog_index.md desde Condor y lo carga al contexto (hook SessionStart).
Si Condor no responde, carga la última versión guardada. Siempre termina con código 0.

Uso: python fetch_catalog.py [article_id]
"""
from __future__ import annotations

from article_sync import SCRIPT_DIR, sync_article

if __name__ == "__main__":
    sync_article(
        env_key="CONDOR_CATALOG_ARTICLE_ID",
        default_id="db9d1f2b-0538-a162-c809-6af12d4b9cae",
        out_file=SCRIPT_DIR / "catalog_index.md",
        title="Catálogo de instrucciones del gestor de JKTIC (planilla Instrucciones Agentes)",
    )
