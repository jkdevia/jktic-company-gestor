"""Conexión al ambiente Condor de JKTIC.

Importar desde otros scripts de esta skill:
    from connect import jktic_session
    with jktic_session() as condor:
        ...

Ejecutar directamente para probar la conexión (un login y un logout):
    python connect.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CLIENT = "jktic-company"
SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_DIR / ".env"

# Cliente SOAP genérico de la skill condor-soap.
sys.path.insert(0, str(SKILL_DIR.parent / "condor-soap" / "scripts"))

from condor_soap import CondorError, CondorSession, load_config  # noqa: E402


def jktic_config() -> dict[str, str]:
    """Configuración de JKTIC leída de jktic-company/.env."""
    return load_config(ENV_FILE)


def jktic_session(timeout: int = 20) -> CondorSession:
    """Sesión SOAP contra el Condor de JKTIC (usar con `with`)."""
    return CondorSession(jktic_config(), timeout=timeout)


def main() -> int:
    try:
        with jktic_session() as condor:
            modules = condor.service.get_available_modules(condor.session_id).modules
            print(f"OK: conexión a JKTIC establecida; {len(modules)} módulos disponibles.")
    except CondorError as exc:
        print(f"FALLO: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
