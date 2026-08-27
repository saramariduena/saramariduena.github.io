"""
Scraper para sentencias de la Corte Constitucional de Colombia.

El buscador de Relatoría (https://www.corteconstitucional.gov.co/relatoria/
buscador_new/) es una página server-side (PHP) que renderiza los resultados
directamente en el HTML de respuesta a un GET — no requiere ejecutar
JavaScript. Los nombres reales de los parámetros del formulario (obtenidos
inspeccionando el HTML del propio buscador, ya que difieren de los que
aparecen en URLs de ejemplo compartidas informalmente) son:

    searchOption : campo donde buscar. 'texto' = texto completo de las
                   providencias (la opción de búsqueda libre real;
                   'prov_sentencia' es solo para buscar por número exacto
                   de sentencia/auto, no texto libre).
    fini / ffin  : rango de fechas (YYYY-MM-DD).
    buscar_por   : el texto a buscar.
    accion       : 'search' para ejecutar la búsqueda.
    verform      : 'si'.
    OrderbyOption: 'des__score' (orden por relevancia descendente).
    maxprov      : cantidad máxima de providencias a traer.

La respuesta es HTML con los resultados ya renderizados (títulos,
metadatos, providencias) — se extraen los números de sentencia con una
expresión regular sobre el texto (T-###-##, C-###-##, SU-###-##, A-###-##)
y se reconstruye la URL de ficha real, con el patrón confirmado
/relatoria/<año>/<TIPO>-<num>-<yy>.htm (p. ej. la Sentencia T-323 de 2024
sobre uso de ChatGPT por un juez vive en /relatoria/2024/T-323-24.htm).
"""

import logging
import re
from dataclasses import dataclass, asdict
from datetime import date

import requests

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

FECHA_INICIO = "1992-01-01"  # la Corte Constitucional de Colombia entró en funciones en 1992

# Números de sentencia tal como aparecen en el texto: "T-323/24", "T-323-24",
# "C-748/11", "SU-420/19", "A-045/22", etc.
SENTENCIA_RE = re.compile(
    r"\b(?P<tipo>T|C|SU|SV|AV|A)-(?P<num>\d{1,4}[A-Za-z]?)[-/](?P<anio>\d{2,4})\b"
)


@dataclass
class Sentencia:
    numero: str       # forma normalizada para citar, p.ej. "T-323 de 2024"
    slug: str          # forma usada en la URL, p.ej. "T-323-24"
    anio: str
    ficha_url: str


def _normaliza(tipo: str, num: str, anio: str) -> "Sentencia":
    anio = anio if len(anio) == 4 else ("20" + anio if int(anio) < 50 else "19" + anio)
    yy = anio[-2:]
    slug = f"{tipo}-{num}-{yy}"
    numero = f"{tipo}-{num} de {anio}"
    ficha_url = f"{BASE_URL}/relatoria/{anio}/{slug}.htm"
    return Sentencia(numero=numero, slug=slug, anio=anio, ficha_url=ficha_url)


def _parse_resultados(html: str) -> list:
    vistos = {}
    for m in SENTENCIA_RE.finditer(html):
        s = _normaliza(m.group("tipo").upper(), m.group("num").upper(), m.group("anio"))
        vistos.setdefault(s.slug, s)
    return list(vistos.values())


def buscar_sentencias(texto: str, max_results: int = 500, session: requests.Session = None) -> list:
    """Busca sentencias por texto libre (texto completo de la providencia)
    en el buscador de Relatoría. Devuelve una lista de objetos Sentencia.
    No lanza excepción ante fallos de red: registra el error y devuelve
    lista vacía, para que un lote de búsquedas por muchos términos no se
    caiga entero por un timeout aislado.
    """
    session = session or requests.Session()
    session.headers.update(HEADERS)

    params = {
        "searchOption": "texto",
        "fini": FECHA_INICIO,
        "ffin": date.today().isoformat(),
        "buscar_por": texto,
        "accion": "search",
        "verform": "si",
        "OrderbyOption": "des__score",
        "maxprov": max_results,
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

    if "No se encontraron resultados" in resp.text:
        logger.info(f"  -> 0 sentencia(s) encontrada(s) para '{texto}' (sin resultados)")
        return []

    resultados = _parse_resultados(resp.text)
    logger.info(f"  -> {len(resultados)} sentencia(s) única(s) encontrada(s) para '{texto}'")
    return resultados


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
