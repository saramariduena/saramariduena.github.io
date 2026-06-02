"""
Scraper para el buscador de sentencias de la Corte Constitucional del Ecuador.
Intercepta las llamadas a la API interna que hace la SPA Angular.
"""

import json
import time
import logging
from dataclasses import dataclass, asdict
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
SEARCH_URL = f"{BASE_URL}/buscador-externo/principal"
RESULT_URL = f"{BASE_URL}/buscador-externo/principal/resultadoSentencia"


@dataclass
class Sentencia:
    numero: str
    tipo: str
    fecha: str
    ponente: str
    resumen: str
    pdf_url: str
    ficha_url: str


def _parse_sentencia_from_api(item: dict) -> Sentencia:
    """Convierte un item de la respuesta JSON de la API en una Sentencia."""
    numero = (
        item.get("numSentencia") or
        item.get("numero") or
        item.get("numberSentence") or
        item.get("num_sentencia") or ""
    )
    tipo = (
        item.get("tipoSentencia") or
        item.get("tipo") or
        item.get("typeSentence") or
        item.get("tipo_sentencia") or ""
    )
    fecha = (
        item.get("fechaSentencia") or
        item.get("fecha") or
        item.get("dateSentence") or
        item.get("fecha_sentencia") or ""
    )
    ponente = (
        item.get("magistradoPonente") or
        item.get("ponente") or
        item.get("juezPonente") or
        item.get("juez_ponente") or ""
    )
    resumen = (
        item.get("extracto") or
        item.get("resumen") or
        item.get("summary") or
        item.get("descripcion") or ""
    )[:500]

    # Construir URL de la ficha
    ficha_url = ""
    if numero:
        import urllib.parse
        ficha_url = f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(numero)}"

    # URL del PDF
    pdf_url = (
        item.get("urlPdf") or
        item.get("pdf_url") or
        item.get("urlDocumento") or
        item.get("linkPdf") or ""
    )

    return Sentencia(
        numero=str(numero).strip(),
        tipo=str(tipo).strip(),
        fecha=str(fecha).strip(),
        ponente=str(ponente).strip(),
        resumen=str(resumen).strip(),
        pdf_url=str(pdf_url).strip(),
        ficha_url=ficha_url,
    )


def _extract_from_dom(page) -> list:
    """Extrae sentencias del DOM como fallback si no se interceptó la API."""
    sentencias = []
    try:
        # Obtener todo el texto visible y buscar números de sentencia
        content = page.content()
        # Buscar cualquier elemento con texto que parezca número de sentencia
        elements = page.query_selector_all("*")
        seen = set()
        for el in elements[:500]:
            try:
                text = el.inner_text().strip()
                # Patrón típico: "28-19-IN/22" o "273-19-JP/22"
                import re
                matches = re.findall(r'\d+-\d+-[A-Z]+/\d+', text)
                for match in matches:
                    if match not in seen:
                        seen.add(match)
                        href = ""
                        link = el.query_selector("a") or el
                        try:
                            href = link.get_attribute("href") or ""
                        except Exception:
                            pass
                        if href and not href.startswith("http"):
                            href = f"{BASE_URL}{href}"
                        import urllib.parse
                        sentencias.append(Sentencia(
                            numero=match,
                            tipo="",
                            fecha="",
                            ponente="",
                            resumen="",
                            pdf_url="",
                            ficha_url=href or f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(match)}",
                        ))
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Error en extracción DOM: {e}")
    return sentencias


def get_pdf_url_from_ficha(page, ficha_url: str) -> str:
    """Visita la ficha de una sentencia y extrae la URL del PDF."""
    if not ficha_url:
        return ""
    try:
        # Interceptar respuestas de red para capturar URL del PDF
        pdf_found = []

        def handle_response(response):
            if ".pdf" in response.url.lower() or "storage/api" in response.url:
                pdf_found.append(response.url)

        page.on("response", handle_response)
        page.goto(ficha_url, wait_until="networkidle", timeout=20000)
        time.sleep(1)
        page.remove_listener("response", handle_response)

        if pdf_found:
            return pdf_found[0]

        # Buscar enlace en el DOM
        for selector in ["a[href*='.pdf']", "a[href*='storage/api']", "a[href*='esacc']", "a[download]"]:
            pdf_link = page.query_selector(selector)
            if pdf_link:
                href = pdf_link.get_attribute("href") or ""
                return href if href.startswith("http") else f"{BASE_URL}{href}"
    except Exception as e:
        logger.debug(f"No se pudo obtener PDF de {ficha_url}: {e}")
    return ""


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    """
    Busca sentencias interceptando las llamadas a la API interna de la SPA Angular.
    """
    sentencias = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # Interceptar todas las respuestas de red para capturar la API interna
        api_responses = []

        def handle_response(response):
            url = response.url
            content_type = response.headers.get("content-type", "")
            # Capturar cualquier respuesta JSON que venga del backend de la Corte
            if ("corteconstitucional" in url or "esacc" in url) and "json" in content_type:
                try:
                    data = response.json()
                    api_responses.append({"url": url, "data": data})
                    logger.info(f"API interceptada: {url}")
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            import urllib.parse
            payload = json.dumps({
                "textoSentencia": texto,
                "numSentencia": numero,
                "numeroCausa": causa,
                "flag": False,
            })
            search_url = f"{RESULT_URL}?search={urllib.parse.quote(payload)}"
            logger.info(f"Cargando: {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Si no interceptó nada, intentar desde la página principal
            if not api_responses:
                logger.info("Intentando desde página principal...")
                page.goto(SEARCH_URL, wait_until="networkidle", timeout=30000)
                time.sleep(3)

                if texto or numero or causa:
                    try:
                        inp = page.query_selector("input[type='text'], input[type='search'], input[placeholder*='buscar' i], input[placeholder*='sentencia' i]")
                        if inp:
                            inp.fill(texto or numero or causa)
                            page.keyboard.press("Enter")
                            time.sleep(3)
                            page.wait_for_load_state("networkidle")
                    except Exception as e:
                        logger.debug(f"Error en campo de búsqueda: {e}")

            # Procesar respuestas de la API interceptada
            found_from_api = []
            for resp in api_responses:
                data = resp["data"]
                logger.info(f"Respuesta API ({resp['url']}): tipo={type(data).__name__}")

                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    # Buscar listas dentro del dict
                    for key in ["content", "data", "sentencias", "results", "items", "list", "registros"]:
                        if key in data and isinstance(data[key], list):
                            items = data[key]
                            break
                    if not items:
                        # Tomar el primer valor que sea lista
                        for v in data.values():
                            if isinstance(v, list) and len(v) > 0:
                                items = v
                                break

                for item in items:
                    if isinstance(item, dict):
                        s = _parse_sentencia_from_api(item)
                        if s.numero:
                            found_from_api.append(s)

            if found_from_api:
                logger.info(f"Sentencias obtenidas de API: {len(found_from_api)}")
                sentencias = found_from_api[:max_results]
            else:
                logger.warning("No se interceptó data de API. Intentando extracción del DOM...")
                sentencias = _extract_from_dom(page)[:max_results]
                logger.info(f"Sentencias del DOM: {len(sentencias)}")

            # Obtener URLs de PDF para las sentencias encontradas
            for s in sentencias:
                if s.ficha_url and not s.pdf_url:
                    s.pdf_url = get_pdf_url_from_ficha(page, s.ficha_url)
                    time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error en el scraper: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias encontradas: {len(sentencias)}")
    return sentencias


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
