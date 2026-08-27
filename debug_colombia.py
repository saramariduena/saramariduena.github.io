"""
Script de diagnóstico puntual: prueba el POST real a index.php (el
endpoint AJAX real usado por buscadorV1.js, con accion=search) para ver
qué devuelve y qué campos de FormData realmente necesita.
"""

import logging

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.corteconstitucional.gov.co"
INDEX_URL = f"{BASE_URL}/relatoria/buscador_new/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "es-CO,es;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/relatoria/buscador_new/",
}

session = requests.Session()
session.headers.update(HEADERS)


def intentar(nombre, data):
    print("\n" + "=" * 80)
    print(f"[{nombre}] POST {INDEX_URL}")
    print("data:", data)
    try:
        r = session.post(INDEX_URL, data=data, timeout=30)
        print(f"Status: {r.status_code} | Content-Type: {r.headers.get('Content-Type')} | bytes: {len(r.content)}")
        print("--- primeros 3000 caracteres ---")
        print(r.text[:3000])
    except Exception as e:
        logger.error(f"Error: {e}")


def main():
    base_fields = {
        "searchOption": "prov_sentencia",
        "buscar_por": "inteligencia artificial",
        "finicio": "1992-01-01",
        "ffin": "2026-08-27",
        "OrderbyOption": "des__score",
        "maxprov": "500",
        "ver_formulario": "si",
        "volver_a": "relatoria",
    }

    intentar("accion=search (form-urlencoded)", {**base_fields, "accion": "search"})
    intentar("accion=searchByAggs (form-urlencoded)", {**base_fields, "accion": "searchByAggs"})

    # Intento con multipart real (como hace $.ajax con FormData/contentType:false)
    print("\n" + "=" * 80)
    print("[accion=search (multipart real)]")
    try:
        files = {k: (None, v) for k, v in {**base_fields, "accion": "search"}.items()}
        r = session.post(INDEX_URL, files=files, timeout=30)
        print(f"Status: {r.status_code} | Content-Type: {r.headers.get('Content-Type')} | bytes: {len(r.content)}")
        print(r.text[:3000])
    except Exception as e:
        logger.error(f"Error multipart: {e}")


if __name__ == "__main__":
    main()
