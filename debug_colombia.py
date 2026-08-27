"""
Descubrimiento clave: searchOption=prov_sentencia busca por NÚMERO de
sentencia (p.ej. "T-388 DE 2019"), no texto completo — por eso "habeas
data" e "inteligencia artificial" no encontraban nada con esa opción,
aunque la búsqueda en sí funciona (server-rendered, sin JS necesario).
El mensaje de "sin resultados" sugiere otras opciones: "Texto completo
de la providencia", "Temas/subtemas", "Normas". Este script extrae las
opciones reales del <select id="searchOption"> del HTML para saber sus
valores exactos, y luego prueba una búsqueda de texto completo con cada
una.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup

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


def main():
    r = session.get(BUSCADOR_URL, timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    sel = soup.find("select", id="searchOption")
    print("=== opciones reales de #searchOption ===")
    opciones = []
    if sel:
        for opt in sel.find_all("option"):
            val = opt.get("value", "")
            texto = opt.get_text(strip=True)
            opciones.append(val)
            print(f"  value={val!r} texto={texto!r}")
    else:
        print("  No se encontró el <select id='searchOption'> en el HTML inicial.")

    # Probar full-text search con cada opción candidata (las que no sean
    # claramente "por número" o "por magistrado")
    candidatos = [v for v in opciones if v and v not in ("prov_sentencia", "prov_magistrados")]
    if not candidatos:
        candidatos = ["texto_completo", "prov_texto", "prov_temas", "ver_todas"]

    for opt_val in candidatos[:6]:
        params = {
            "searchOption": opt_val,
            "finicio": "1992-01-01",
            "ffin": "2026-08-27",
            "buscar_por": "inteligencia artificial",
            "accion": "search",
            "ver_formulario": "si",
            "volver_a": "relatoria",
            "OrderbyOption": "des__score",
            "cant_providencias": "50",
        }
        resp = session.get(BUSCADOR_URL, params=params, timeout=30)
        body = resp.text
        matches = SENTENCIA_RE.findall(body)
        sin_resultados = "No se encontraron resultados" in body
        print(f"\n[searchOption={opt_val!r}] status={resp.status_code} bytes={len(resp.content)} "
              f"sin_resultados={sin_resultados} matches_sentencia={len(set(matches))}")
        if matches:
            print("  ejemplos:", list(dict.fromkeys(matches))[:15])


if __name__ == "__main__":
    main()
