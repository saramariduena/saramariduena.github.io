"""
La página base (sin params) devuelve solo 77 bytes -- por eso el <select>
no aparecía. La página CON accion=search (que ya sabemos que renderiza
~29KB con resultado real, incluyendo "Sin resultados" cuando corresponde)
sí trae el formulario completo. Este script busca ahí el <select
searchOption>, todos los <input>/<select> del form, y confirma con qué
searchOption real aparecen resultados de la sentencia T-323 de 2024 (caso
ChatGPT), que sabemos que existe.
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

SENTENCIA_RE = re.compile(r"\b(?:T|C|SU|A|SV|AV)-\d{1,4}[A-Za-z]?[-/]\d{2,4}\b")


def get_full_page(buscar_por, search_option="prov_sentencia"):
    params = {
        "searchOption": search_option,
        "finicio": "1992-01-01",
        "ffin": "2026-08-27",
        "buscar_por": buscar_por,
        "accion": "search",
        "ver_formulario": "si",
        "volver_a": "relatoria",
        "OrderbyOption": "des__score",
        "cant_providencias": "500",
    }
    return session.get(BUSCADOR_URL, params=params, timeout=30)


def main():
    # Página completa buscando por el número de la sentencia T-323 de 2024
    # (caso ChatGPT), que SABEMOS que existe -- para inspeccionar su form.
    r = get_full_page("T-323 DE 2024", "prov_sentencia")
    body = r.text
    print(f"Status: {r.status_code} bytes: {len(r.content)}")
    matches = SENTENCIA_RE.findall(body)
    print(f"Coincidencias sentencia en esta respuesta: {len(set(matches))} -> {list(dict.fromkeys(matches))[:10]}")

    print("\n=== <select ...> encontrados ===")
    for m in re.finditer(r"<select[^>]*>.*?</select>", body, re.IGNORECASE | re.DOTALL):
        block = m.group(0)
        idname = re.search(r'(?:id|name)="([^"]+)"', block)
        print(f"\n--- select {idname.group(1) if idname else '?'} ---")
        for opt in re.finditer(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', block, re.IGNORECASE):
            print(f"    value={opt.group(1)!r} texto={opt.group(2)!r}")

    print("\n=== todos los <input ...> del documento (name/id/value) ===")
    for m in re.finditer(r"<input[^>]+>", body, re.IGNORECASE):
        tag = m.group(0)
        name = re.search(r'name="([^"]*)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if name:
            print(f"  name={name.group(1)!r} value={(value.group(1) if value else '')!r}")


if __name__ == "__main__":
    main()
