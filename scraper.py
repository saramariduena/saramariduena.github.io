"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Captura el request/response exacto que hace Angular para obtener las sentencias.
"""

import json
import time
import logging
import requests
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": f"{BASE_URL}/buscador-externo/principal",
    "Origin": BASE_URL,
    "Content-Type": "application/json",
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
    numero = ""
    for k in ["numSentencia", "numero", "numberSentence", "num_sentencia",
              "numExpediente", "expediente", "identificador", "codigo", "id"]:
        if item.get(k):
            numero = str(item[k])
            break

    tipo = ""
    for k in ["tipoSentencia", "tipo", "typeSentence", "tipo_sentencia", "tipoAccion"]:
        if item.get(k):
            tipo = str(item[k])
            break

    fecha = ""
    for k in ["fechaSentencia", "fecha", "dateSentence", "fecha_sentencia",
              "fechaPublicacion", "anio", "year", "fechaEmision"]:
        if item.get(k):
            fecha = str(item[k])
            break

    ponente = ""
    for k in ["magistradoPonente", "ponente", "juezPonente", "juez_ponente",
              "magistrado", "nombreMagistrado", "jueza", "juez"]:
        if item.get(k):
            ponente = str(item[k])
            break

    resumen = ""
    for k in ["extracto", "resumen", "summary", "descripcion", "tema",
              "materia", "palabrasClave"]:
        if item.get(k):
            resumen = str(item[k])[:500]
            break

    pdf_url = ""
    for k in ["urlPdf", "pdf_url", "urlDocumento", "linkPdf", "rutaPdf"]:
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


def _is_sentencias_response(url: str, data) -> bool:
    """Determina si una respuesta de API contiene sentencias (no analytics)."""
    if "googleAnalytics" in url or "analytics" in url.lower():
        return False
    if "admision" in url and "analytics" in url:
        return False
    return True


def _extract_items(data, url: str = "") -> list:
    """Extrae lista de items de una respuesta JSON."""
    if not _is_sentencias_response(url, data):
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        keys = list(data.keys())
        logger.info(f"Claves: {keys}")

        for key in ["dato", "content", "data", "sentencias", "results",
                    "items", "list", "registros", "rows", "resultado"]:
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                # Verificar que no sean items de analytics
                first = data[key][0] if data[key] else {}
                if isinstance(first, dict) and "evento" in first:
                    continue  # son analytics, no sentencias
                logger.info(f"Lista en '{key}': {len(data[key])} items")
                logger.info(f"Primer item: {str(first)[:300]}")
                return data[key]

    return []


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    """Busca sentencias usando Playwright para interceptar la API correcta."""
    from playwright.sync_api import sync_playwright

    sentencias = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = context.new_page()

        captured = []  # (url, request_body, response_data)

        def handle_request(request):
            url = request.url
            if "corteconstitucional" in url and "googleAnalytics" not in url:
                try:
                    body = request.post_data or ""
                    logger.info(f"REQUEST → {request.method} {url} | body: {body[:200]}")
                except Exception:
                    pass

        def handle_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "corteconstitucional" in url and "json" in ct and "googleAnalytics" not in url:
                try:
                    data = response.json()
                    logger.info(f"RESPONSE ← {url} | {str(data)[:400]}")
                    captured.append({"url": url, "data": data})
                except Exception:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            import urllib.parse

            # Cargar con búsqueda vacía primero (trae todas las sentencias recientes)
            payload = json.dumps({
                "textoSentencia": texto,
                "numSentencia": numero,
                "numeroCausa": causa,
                "flag": False,
            })
            search_url = f"{BASE_URL}/buscador-externo/principal/resultadoSentencia?search={urllib.parse.quote(payload)}"
            logger.info(f"Navegando a: {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            time.sleep(5)  # esperar más para que Angular procese

            # Intentar también hacer scroll para disparar más carga
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            except Exception:
                pass

            # Procesar respuestas capturadas
            for entry in captured:
                items = _extract_items(entry["data"], entry["url"])
                for item in items[:max_results]:
                    if isinstance(item, dict):
                        s = _parse_item(item)
                        if s.numero:
                            sentencias.append(s)

            # Si no encontró con URL de resultados, ir a página principal
            if not sentencias:
                logger.info("Sin resultados en URL de búsqueda. Probando página principal...")
                captured.clear()
                page.goto(f"{BASE_URL}/buscador-externo/principal", wait_until="networkidle", timeout=30000)
                time.sleep(5)

                for entry in captured:
                    items = _extract_items(entry["data"], entry["url"])
                    for item in items[:max_results]:
                        if isinstance(item, dict):
                            s = _parse_item(item)
                            if s.numero:
                                sentencias.append(s)

            # Último recurso: regex en el HTML
            if not sentencias:
                import re
                content = page.content()
                matches = re.findall(r'\d+-\d+-[A-Z]+/\d+', content)
                seen = set()
                for match in matches:
                    if match not in seen:
                        seen.add(match)
                        sentencias.append(Sentencia(
                            numero=match, tipo="", fecha="", ponente="",
                            resumen="", pdf_url="",
                            ficha_url=f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(match)}",
                        ))
                if sentencias:
                    logger.info(f"Sentencias por regex: {len(sentencias)}")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias encontradas: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
