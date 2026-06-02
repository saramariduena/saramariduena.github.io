"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Llama directamente a la API REST interna descubierta por interceptación de red.
"""

import json
import time
import logging
import requests
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
API_BASE = f"{BASE_URL}/buscador-externo/rest/api/sentencia"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": f"{BASE_URL}/buscador-externo/principal",
    "Origin": BASE_URL,
}


@dataclass
class Sentencia:
    numero: str
    tipo: str
    fecha: str
    ponente: str
    resumen: str
    pdf_url: str
    ficha_url: str


def _parse_item(item: dict) -> Sentencia:
    # Intentar todos los nombres de campo posibles
    numero = ""
    for k in ["numSentencia", "numero", "numberSentence", "num_sentencia", "nro_sentencia",
              "numExpediente", "expediente", "identificador", "codigo"]:
        if item.get(k):
            numero = str(item[k])
            break

    tipo = ""
    for k in ["tipoSentencia", "tipo", "typeSentence", "tipo_sentencia", "tipoAccion", "accion"]:
        if item.get(k):
            tipo = str(item[k])
            break

    fecha = ""
    for k in ["fechaSentencia", "fecha", "dateSentence", "fecha_sentencia", "fechaPublicacion",
              "fecha_publicacion", "anio", "year"]:
        if item.get(k):
            fecha = str(item[k])
            break

    ponente = ""
    for k in ["magistradoPonente", "ponente", "juezPonente", "juez_ponente", "magistrado",
              "nombreMagistrado", "jueza", "juez"]:
        if item.get(k):
            ponente = str(item[k])
            break

    resumen = ""
    for k in ["extracto", "resumen", "summary", "descripcion", "tema", "materia",
              "palabrasClave", "keywords"]:
        if item.get(k):
            resumen = str(item[k])[:500]
            break

    pdf_url = ""
    for k in ["urlPdf", "pdf_url", "urlDocumento", "linkPdf", "rutaPdf", "archivo"]:
        if item.get(k):
            pdf_url = str(item[k])
            break

    import urllib.parse
    ficha_url = ""
    if numero:
        ficha_url = f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(numero)}"

    return Sentencia(
        numero=numero.strip(), tipo=tipo.strip(), fecha=fecha.strip(),
        ponente=ponente.strip(), resumen=resumen.strip(),
        pdf_url=pdf_url.strip(), ficha_url=ficha_url,
    )


def _extract_items_from_response(data) -> list:
    """Extrae la lista de sentencias de cualquier estructura JSON."""
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Log de las claves para depuración
        logger.info(f"Claves en respuesta API: {list(data.keys())[:20]}")

        # Buscar listas en claves conocidas
        for key in ["content", "data", "sentencias", "results", "items", "list",
                    "registros", "rows", "records", "sentencia", "response",
                    "payload", "body", "resultado", "listado"]:
            if key in data and isinstance(data[key], list):
                logger.info(f"Lista encontrada en clave '{key}': {len(data[key])} items")
                return data[key]

        # Buscar cualquier lista en el dict
        for k, v in data.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                logger.info(f"Lista encontrada en clave '{k}': {len(v)} items")
                return v

        # Si hay un solo nivel más de anidamiento
        for k, v in data.items():
            if isinstance(v, dict):
                nested = _extract_items_from_response(v)
                if nested:
                    return nested

    return []


def _try_api_endpoints(texto: str = "", max_results: int = 50) -> list:
    """Intenta múltiples endpoints de la API REST."""
    session = requests.Session()
    session.headers.update(HEADERS)

    # Primero obtener una cookie de sesión visitando la página principal
    try:
        session.get(f"{BASE_URL}/buscador-externo/principal", timeout=15)
    except Exception:
        pass

    # Endpoints a probar
    endpoints = [
        # Endpoint de búsqueda principal descubierto
        {
            "method": "POST",
            "url": f"{API_BASE}/100_OBT_RSM_ESTDTCO",
            "json": {"textoSentencia": texto, "numSentencia": "", "numeroCausa": "", "flag": False, "page": 0, "size": max_results},
        },
        {
            "method": "GET",
            "url": f"{API_BASE}/100_OBT_RSM_ESTDTCO",
            "params": {"textoSentencia": texto, "page": 0, "size": max_results},
        },
        # Variantes del endpoint
        {
            "method": "POST",
            "url": f"{API_BASE}/buscar",
            "json": {"textoSentencia": texto, "page": 0, "size": max_results},
        },
        {
            "method": "GET",
            "url": f"{API_BASE}/buscar",
            "params": {"texto": texto, "page": 0, "size": max_results},
        },
        {
            "method": "POST",
            "url": f"{BASE_URL}/buscador-externo/rest/api/sentencia/listar",
            "json": {"texto": texto, "page": 0, "size": max_results},
        },
    ]

    for ep in endpoints:
        try:
            method = ep["method"]
            url = ep["url"]
            logger.info(f"Probando {method} {url}")

            if method == "POST":
                resp = session.post(url, json=ep.get("json", {}), timeout=20)
            else:
                resp = session.get(url, params=ep.get("params", {}), timeout=20)

            logger.info(f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type','')}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    logger.info(f"Respuesta JSON recibida: {str(data)[:300]}")
                    items = _extract_items_from_response(data)
                    if items:
                        logger.info(f"Encontrados {len(items)} items en {url}")
                        return items
                except Exception as e:
                    logger.debug(f"No es JSON: {e}")
        except Exception as e:
            logger.debug(f"Error en {ep['url']}: {e}")
            continue

    return []


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    """Busca sentencias usando la API REST de la Corte Constitucional."""
    sentencias = []

    # Intentar con la API REST directamente
    items = _try_api_endpoints(texto=texto or numero or causa, max_results=max_results)

    if items:
        for item in items[:max_results]:
            if isinstance(item, dict):
                s = _parse_item(item)
                if s.numero:
                    sentencias.append(s)
        logger.info(f"Sentencias parseadas: {len(sentencias)}")
    else:
        # Fallback: usar Playwright para interceptar la API
        logger.info("API REST directa falló. Usando Playwright como fallback...")
        sentencias = _playwright_fallback(texto=texto, numero=numero, causa=causa, max_results=max_results)

    return sentencias


def _playwright_fallback(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    """Usa Playwright para interceptar la API e intentar parsear la respuesta completa."""
    from playwright.sync_api import sync_playwright
    sentencias = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = context.new_page()

        all_api_data = []

        def handle_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "corteconstitucional" in url and "json" in ct:
                try:
                    data = response.json()
                    all_api_data.append({"url": url, "data": data})
                    # Log completo de la respuesta para diagnóstico
                    logger.info(f"API: {url} → {str(data)[:500]}")
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            import urllib.parse
            payload = json.dumps({"textoSentencia": texto, "numSentencia": numero, "numeroCausa": causa, "flag": False})
            url = f"{BASE_URL}/buscador-externo/principal/resultadoSentencia?search={urllib.parse.quote(payload)}"
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(4)

            for entry in all_api_data:
                items = _extract_items_from_response(entry["data"])
                for item in items[:max_results]:
                    if isinstance(item, dict):
                        s = _parse_item(item)
                        if s.numero:
                            sentencias.append(s)

            if not sentencias:
                # Extracción por regex del HTML como último recurso
                import re
                content = page.content()
                matches = re.findall(r'\d+-\d+-[A-Z]+/\d+', content)
                seen = set()
                for match in matches:
                    if match not in seen:
                        seen.add(match)
                        sentencias.append(Sentencia(
                            numero=match, tipo="", fecha="", ponente="", resumen="",
                            pdf_url="",
                            ficha_url=f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(match)}",
                        ))
                logger.info(f"Sentencias por regex: {len(sentencias)}")

        except Exception as e:
            logger.error(f"Error en Playwright: {e}", exc_info=True)
        finally:
            browser.close()

    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
