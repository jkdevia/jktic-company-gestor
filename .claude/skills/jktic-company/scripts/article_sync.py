"""Sincroniza un artículo jkk_articles de Condor con un archivo .md local y lo carga al contexto.

Cada ejecución hace dos pasos:
  1. Actualizar: consulta el artículo en Condor y reescribe el archivo .md.
  2. Cargar: lee el archivo y lo imprime, para que quede en el contexto
     (los hooks SessionStart toman esta salida).

Si el paso 1 falla, avisa y el paso 2 carga la última versión guardada del archivo.
Nunca lanza excepciones, para no bloquear el inicio de sesión.
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PREFIX = "[jktic-company]"

# connect.py está en esta misma carpeta.
sys.path.insert(0, str(SCRIPT_DIR))


def emit(text: str) -> None:
    """Imprime en UTF-8 aunque la consola de Windows use otra codificación."""
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()


def update_file(article_id: str | None, env_key: str, default_id: str, out_file: Path) -> str:
    """Paso 1: consulta el artículo y reescribe out_file. Devuelve un mensaje de estado."""
    try:
        from connect import jktic_config
        from condor_soap import CondorSession
    except ImportError as exc:
        return f"no actualizado: dependencias no instaladas ({exc}); ejecutar setup.sh o setup.ps1"

    try:
        config = jktic_config()
        article_id = article_id or config.get(env_key) or default_id
        with CondorSession(config) as condor:
            fields = condor.entry_to_dict(condor.get_entry("jkk_articles", article_id))
    except Exception as exc:  # CondorError, red, etc.: no bloquear la sesión
        return f"no actualizado: {exc}"

    content = fields.get("contenido", "")
    if not content:
        return f"no actualizado: el artículo {article_id} no tiene contenido"

    body = html.unescape(content)
    body = re.sub(r"</?pre[^>]*>", "", body, flags=re.IGNORECASE).strip()
    header = (f"<!-- Fuente: Condor jkk_articles id={article_id} | {fields.get('name', '')} | "
              f"versión {fields.get('version', '')} | modificado en Condor {fields.get('date_modified', '')} -->\n")
    try:
        out_file.write_text(header + body + "\n", encoding="utf-8")
    except OSError as exc:
        return f"no actualizado: no se pudo escribir {out_file.name} ({exc})"
    return "actualizado desde Condor"


def load_context(status: str, out_file: Path, title: str) -> None:
    """Paso 2: lee out_file y lo imprime para cargarlo al contexto."""
    if not out_file.is_file():
        emit(f"{PREFIX} {status}. No existe {out_file.name}; no hay {title} para cargar.\n")
        return
    stamp = datetime.fromtimestamp(out_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    emit(f"{PREFIX} {out_file.name} {status} (archivo del {stamp}). {title}:\n\n")
    emit(out_file.read_text(encoding="utf-8"))
    emit("\n")


def sync_article(*, env_key: str, default_id: str, out_file: Path, title: str) -> None:
    """Actualiza y carga un artículo. Acepta un id opcional como primer argumento de la línea de comandos."""
    article_id = sys.argv[1] if len(sys.argv) > 1 else None
    load_context(update_file(article_id, env_key, default_id, out_file), out_file, title)
