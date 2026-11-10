"""Prueba de humo de Playwright: abre el navegador, carga la página de Condor
(sin iniciar sesión), valida la respuesta y guarda una captura de pantalla.

La URL se deriva de CONDOR_SOAP_URL en .claude/skills/<cliente>/.env
(.../system/soap.php -> .../system/index.php). Funciona en Windows y Linux.

Uso:
    python scripts/browser_smoke_test.py                         # cliente jktic-company, headless
    python scripts/browser_smoke_test.py --client otro-company   # otro cliente
    python scripts/browser_smoke_test.py --headed                # muestra el navegador
    python scripts/browser_smoke_test.py --url https://ejemplo.com
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from dotenv import dotenv_values
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_DIR / ".claude" / "skills"
DEFAULT_CLIENT = "jktic-company"
OUTPUT_DIR = PROJECT_DIR / "output" / "screenshots"


def condor_url(client: str) -> str:
    env_file = SKILLS_DIR / client / ".env"
    soap_url = (dotenv_values(env_file).get("CONDOR_SOAP_URL") or "").strip()
    if not soap_url:
        sys.exit(f"Falta CONDOR_SOAP_URL en {env_file}; usa --url para indicar otra página.")
    return urljoin(soap_url, "index.php")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de humo de Playwright")
    parser.add_argument("--client", default=DEFAULT_CLIENT, help=f"skill del cliente (por defecto {DEFAULT_CLIENT})")
    parser.add_argument("--url", help="página a abrir (por defecto, la de Condor del cliente)")
    parser.add_argument("--headed", action="store_true", help="mostrar la ventana del navegador")
    args = parser.parse_args()

    url = args.url or condor_url(args.client)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUTPUT_DIR / f"smoke_{datetime.now():%Y%m%d_%H%M%S}.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not args.headed)
            page = browser.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            status = response.status if response else None
            title = page.title()
            page.screenshot(path=str(shot), full_page=True)
            browser.close()
    except PlaywrightError as exc:
        print(f"FALLO: Playwright no pudo abrir {url}: {exc}")
        print("Si falta el navegador: python -m playwright install chromium")
        return 1

    ok = status is not None and status < 400
    print(f"{'OK' if ok else 'FALLO'}: HTTP {status} | título: {title!r}")
    print(f"Captura: {shot}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
