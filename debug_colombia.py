"""
Script de diagnóstico puntual para entender por qué scraper_colombia.py
devuelve 0 resultados: inspecciona el HTML crudo que devuelve
buscador_new, busca scripts, endpoints de API embebidos, y prueba
variantes de la petición (headers, POST, JSON).

Uso: python debug_colombia.py
Requiere red real (correr vía GitHub Actions, no en el sandbox de dev).
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


def dump(nombre, resp):
    print("\n" + "=" * 80)
    print(f"[{nombre}] {resp.request.method} {resp.url}")
    print(f"Status: {resp.status_code} | Content-Type: {resp.headers.get('Content-Type')} | bytes: {len(resp.content)}")
    body = resp.text
    print("--- primeros 2000 caracteres ---")
    print(body[:2000])
    print("--- scripts <script src=...> ---")
    for m in re.findall(r'<script[^>]+src="([^"]+)"', body):
        print("  ", m)
    print("--- pistas de API (api/, axios, fetch(, /rest/, .json) ---")
    pistas = set()
    for pat in [r'["\'](/[^"\']*api[^"\']*)["\']', r'["\'](/[^"\']*/rest/[^"\']*)["\']',
                r'["\']([^"\']*\.json[^"\']*)["\']', r'fetch\(["\']([^"\']+)', r'axios\.[a-z]+\(["\']([^"\']+)']:
        for m in re.findall(pat, body, re.IGNORECASE):
            pistas.add(m)
    for p in sorted(pistas)[:40]:
        print("  ", p)


def main():
    r1 = session.get(BUSCADOR_URL, params={
        "searchOption": "prov_sentencia",
        "buscar_por": "inteligencia artificial",
        "accion": "search",
    }, timeout=30)
    dump("GET buscador_new (con query)", r1)

    r2 = session.get(f"{BASE_URL}/relatoria/", timeout=30)
    dump("GET /relatoria/ (base)", r2)

    # Probar con Accept: application/json por si el mismo endpoint responde distinto
    try:
        r3 = session.get(BUSCADOR_URL, params={"buscar_por": "inteligencia artificial"},
                          headers={**HEADERS, "Accept": "application/json, text/plain, */*",
                                   "X-Requested-With": "XMLHttpRequest"}, timeout=30)
        dump("GET buscador_new (Accept: json, XHR)", r3)
    except Exception as e:
        logger.error(f"Error variante JSON: {e}")

    # robots.txt / sitemap por si delatan rutas de API
    try:
        r4 = session.get(f"{BASE_URL}/robots.txt", timeout=15)
        print("\n=== robots.txt ===")
        print(r4.text[:2000])
    except Exception as e:
        logger.error(f"Error robots.txt: {e}")


if __name__ == "__main__":
    main()
