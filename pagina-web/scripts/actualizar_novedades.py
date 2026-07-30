"""Genera pagina-web/novedades.json a partir de feeds RSS públicos de Google News.

No requiere API keys: usa el endpoint público de búsqueda RSS de Google News.
Pensado para correr periódicamente desde GitHub Actions.
"""

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from email.utils import parsedate_to_datetime

CONSULTAS = [
    "inteligencia artificial derecho",
    "protección de datos Ecuador",
    "derechos digitales América Latina",
    "regulación inteligencia artificial",
]

FEED_URL = (
    "https://news.google.com/rss/search?q={query}&hl=es-419&gl=EC&ceid=EC:es-419"
)

MAX_NOTICIAS = 10
TIMEOUT_SEGUNDOS = 15
SALIDA = Path(__file__).resolve().parent.parent / "novedades.json"


def limpiar_texto(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def obtener_feed(consulta):
    url = FEED_URL.format(query=urllib.parse.quote(consulta))
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SEGUNDOS) as respuesta:
        return respuesta.read()


def parsear_items(xml_bytes):
    items = []
    raiz = ET.fromstring(xml_bytes)
    for item in raiz.findall("./channel/item"):
        titulo = limpiar_texto(item.findtext("title"))
        enlace = limpiar_texto(item.findtext("link"))
        fuente = limpiar_texto(item.findtext("source"))
        fecha_texto = item.findtext("pubDate")
        try:
            fecha = parsedate_to_datetime(fecha_texto)
        except (TypeError, ValueError):
            fecha = None
        if not titulo or not enlace:
            continue
        items.append(
            {
                "titulo": titulo,
                "enlace": enlace,
                "fuente": fuente or "Google News",
                "fecha": fecha.isoformat() if fecha else None,
            }
        )
    return items


def main():
    todas = []
    vistos = set()

    for consulta in CONSULTAS:
        try:
            xml_bytes = obtener_feed(consulta)
            items = parsear_items(xml_bytes)
        except Exception as error:  # una falla en un feed no debe tumbar todo
            print(f"Aviso: no se pudo leer el feed para '{consulta}': {error}")
            continue

        for item in items:
            clave = item["enlace"]
            if clave in vistos:
                continue
            vistos.add(clave)
            todas.append(item)

    def orden(item):
        return item["fecha"] or ""

    todas.sort(key=orden, reverse=True)
    seleccion = todas[:MAX_NOTICIAS]

    salida = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "noticias": seleccion,
    }

    SALIDA.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Escritas {len(seleccion)} noticias en {SALIDA}")


if __name__ == "__main__":
    main()
