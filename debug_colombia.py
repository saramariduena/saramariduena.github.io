"""
Validación rápida: con los nombres de campo reales (fini, ffin, verform,
maxprov) y searchOption='texto' (texto completo), ¿aparece la sentencia
T-323 de 2024 al buscar "inteligencia artificial" como texto libre?
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


def buscar(texto, search_option):
    params = {
        "searchOption": search_option,
        "fini": "1992-01-01",
        "ffin": "2026-08-27",
        "buscar_por": texto,
        "accion": "search",
        "verform": "si",
        "OrderbyOption": "des__score",
        "maxprov": "500",
    }
    r = session.get(BUSCADOR_URL, params=params, timeout=30)
    body = r.text
    matches = list(dict.fromkeys(SENTENCIA_RE.findall(body)))
    print(f"[searchOption={search_option!r} buscar_por={texto!r}] status={r.status_code} bytes={len(r.content)} "
          f"sin_resultados={'No se encontraron resultados' in body} matches={len(matches)}")
    if matches:
        print("  ", matches[:20])
    m = re.search(r"tot_provi_found['\"]?\s*value=['\"](\d+)", body)
    if m:
        print("  tot_provi_found:", m.group(1))
    return matches


def main():
    for opt in ["texto", "todos"]:
        buscar("inteligencia artificial", opt)
        buscar("habeas data", opt)
        buscar("chatgpt", opt)


if __name__ == "__main__":
    main()
