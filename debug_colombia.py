"""
El <select id="searchOption"> no aparece en el HTML inicial estático —
probablemente se carga por otra vía (fragmento server-side incluido con
otro id, o generado dinámicamente). Este script busca CUALQUIER mención
de 'searchOption' y cualquier <select> en el HTML crudo, con contexto,
para encontrar los valores reales de las opciones de búsqueda.
"""

import logging
import re

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.corteconstitucional.gov.co"
BUSCADOR_URL = f"{BASE_URL}/relatoria/buscador_new/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)


def main():
    r = session.get(BUSCADOR_URL, timeout=30)
    body = r.text
    print(f"Status: {r.status_code} bytes: {len(r.content)}")

    print("\n=== todas las ocurrencias de 'searchOption' (con contexto) ===")
    for m in re.finditer(r"searchOption", body):
        i = m.start()
        print("  ...", body[max(0, i - 100):i + 150].replace("\n", " ").strip(), "...")

    print("\n=== todos los <select ...> con su id/name ===")
    for m in re.finditer(r"<select[^>]*>", body, re.IGNORECASE):
        print("  ", m.group(0))

    print("\n=== todos los <option value=...>texto</option> en todo el documento ===")
    for m in re.finditer(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', body, re.IGNORECASE):
        print(f"  value={m.group(1)!r} texto={m.group(2)!r}")

    print("\n=== bloque completo del formulario (desde <form hasta 6000 chars después) ===")
    idx = body.find("<form")
    if idx >= 0:
        print(body[idx:idx + 6000])


if __name__ == "__main__":
    main()
