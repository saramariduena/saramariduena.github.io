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
    # El JS del buscador (buscadorV1.js) es donde vive la lógica real de
    # la búsqueda: ahí deberían estar la URL del endpoint y el payload.
    try:
        r5 = session.get(f"{BASE_URL}/relatoria/buscador_new/assets/js/buscadorV1.js", timeout=30)
        print("\n" + "=" * 80)
        print(f"[buscadorV1.js] Status: {r5.status_code} | bytes: {len(r5.content)}")
        body = r5.text
        print("--- caracteres 6000-20718 (resto del archivo) ---")
        print(body[6000:20718])
        print("\n--- ocurrencias de 'DataTable(' ---")
        for m in re.finditer(r'.{0,50}DataTable\(.{0,600}', body, re.DOTALL):
            print("  ...", m.group(0).replace("\n", " ")[:700], "...")
        print("\n--- ocurrencias de accion=/accion':/'accion\" con valor ---")
        for m in re.finditer(r'accion[\'"]?\s*[,:=]\s*[\'"]([a-zA-Z_]+)[\'"]', body):
            print("  accion ->", m.group(1))
    except Exception as e:
        logger.error(f"Error buscadorV1.js: {e}")


if __name__ == "__main__":
    main()
