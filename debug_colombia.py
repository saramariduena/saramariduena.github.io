"""
Script de diagnóstico: la respuesta completa (~29KB) del GET a buscador_new
con accion=search probablemente SÍ contiene la tabla de resultados más
abajo en el HTML — los intentos anteriores solo imprimieron los primeros
2000-3000 caracteres (puro <head>/CSS). Este script busca en el body
COMPLETO cualquier patrón de número de sentencia o indicios de resultados.
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


def analizar(nombre, resp):
    print("\n" + "=" * 80)
    print(f"[{nombre}] Status: {resp.status_code} | bytes: {len(resp.content)}")
    body = resp.text
    matches = SENTENCIA_RE.findall(body)
    print(f"Ocurrencias de patrón sentencia (T-/C-/SU-/A-###-##): {len(matches)}")
    print("Ejemplos:", matches[:20])
    for kw in ["Sin resultados", "No fue posible", "totalFilas", "No se encontraron",
               "div_resultado_detalle", "table", "prov_sentencia\"", "checkbox"]:
        idx = body.find(kw)
        print(f"  '{kw}' encontrado en offset: {idx}")
    # imprimir un bloque alrededor de donde debería estar el div de resultados
    idx = body.find('id="div_resultado_detalle"')
    if idx == -1:
        idx = body.find('div_container')
    if idx >= 0:
        print("\n--- contexto alrededor de resultados ---")
        print(body[idx:idx + 3000])
    else:
        print("\n--- últimos 3000 caracteres del body (por si el resultado está al final) ---")
        print(body[-3000:])


def main():
    params = {
        "searchOption": "prov_sentencia",
        "finicio": "1992-01-01",
        "ffin": "2026-08-27",
        "buscar_por": "inteligencia artificial",
        "accion": "search",
        "ver_formulario": "si",
        "volver_a": "relatoria",
        "OrderbyOption": "des__score",
        "cant_providencias": "500",
    }
    r = session.get(BUSCADOR_URL, params=params, timeout=30)
    analizar("GET buscador_new (params completos, como URL real de ejemplo)", r)

    # Probar también buscando algo con muchísimos resultados esperables: "habeas data"
    params2 = {**params, "buscar_por": "habeas data"}
    r2 = session.get(BUSCADOR_URL, params=params2, timeout=30)
    analizar("GET buscador_new (habeas data)", r2)


if __name__ == "__main__":
    main()
