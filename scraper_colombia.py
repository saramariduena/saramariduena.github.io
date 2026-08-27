"""
Scraper para sentencias de la Corte Constitucional de Colombia.

A diferencia de scraper.py (Ecuador, que usa la API JSON real del
buscador), el buscador de Relatoría de Colombia
(https://www.corteconstitucional.gov.co/relatoria/buscador_new/) es una
página HTML server-side renderizada: se le pasan los criterios de
búsqueda como query string y devuelve una página con enlaces a cada
sentencia. Este scraper hace ese GET y extrae los enlaces a fichas de
sentencia, que siguen el patrón real observado:

    https://www.corteconstitucional.gov.co/relatoria/<año>/<TIPO>-<num>-<yy>.htm

p. ej. https://www.corteconstitucional.gov.co/relatoria/2024/T-323-24.htm
"""

import logging
import re
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import date

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.corteconstitucional.gov.co"
BUSCADOR_URL = f"{BASE_URL}/relatoria/buscador_new/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9",
    "Referer": BASE_URL + "/relatoria/",
}

# Patrón real de las fichas de sentencia: /relatoria/<año>/T-323-24.htm,
# /relatoria/2011/C-748-11.htm, /relatoria/2019/SU-420-19.htm, etc.
FICHA_PATTERN = re.compile(
    r"/relatoria/(?P<anio>\d{4})/(?P<numero>(?:[TCA]|SU|SV|AV)-\d+[A-Za-z]?-\d{2,4})\.htm",
    re.IGNORECASE,
)

FECHA_INICIO = "1992-01-01"  # la Corte Constitucional de Colombia entró en funciones en 1992


@dataclass
class Sentencia:
    numero: str
    anio: str
    titulo: str
    ficha_url: str


def _normaliza_numero(numero: str) -> str:
    return numero.upper().strip()


def _parse_resultados(html: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    vistos = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = FICHA_PATTERN.search(href)
        if not m:
            continue
        numero = _normaliza_numero(m.group("numero"))
        if numero in vistos:
            continue
        titulo = a.get_text(strip=True)
        # El título suele estar vacío o repetir el número; si es así, se
        # intenta usar el texto del bloque contenedor como resumen corto.
        if not titulo or titulo == numero:
            padre = a.find_parent(["li", "div", "tr"])
            if padre:
                titulo = padre.get_text(" ", strip=True)[:300]
        ficha_url = href if href.startswith("http") else urllib.parse.urljoin(BASE_URL, href)
        vistos[numero] = Sentencia(
            numero=numero, anio=m.group("anio"), titulo=titulo[:300], ficha_url=ficha_url,
        )
    return list(vistos.values())


def buscar_sentencias(texto: str, max_results: int = 500, session: requests.Session = None) -> list:
    """Busca sentencias por texto libre en el buscador de Relatoría.

    Devuelve una lista de objetos Sentencia. No lanza excepción ante fallos
    de red: registra el error y devuelve lista vacía, para que un lote de
    búsquedas por muchos términos no se caiga entero por un timeout aislado.
    """
    session = session or requests.Session()
    session.headers.update(HEADERS)

    params = {
        "searchOption": "prov_sentencia",
        "finicio": FECHA_INICIO,
        "ffin": date.today().isoformat(),
        "buscar_por": texto,
        "accion": "search",
        "ver_formulario": "si",
        "volver_a": "relatoria",
        "OrderbyOption": "des__score",
        "cant_providencias": max_results,
    }

    try:
        resp = session.get(BUSCADOR_URL, params=params, timeout=30)
        logger.info(f"GET {resp.url} -> {resp.status_code} ({len(resp.text)} bytes)")
    except Exception as e:
        logger.error(f"Error de red buscando '{texto}': {e}")
        return []

    if resp.status_code != 200:
        logger.warning(f"HTTP {resp.status_code} buscando '{texto}': {resp.text[:300]}")
        return []

    resultados = _parse_resultados(resp.text)
    logger.info(f"  -> {len(resultados)} sentencia(s) encontrada(s) para '{texto}'")
    return resultados


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
