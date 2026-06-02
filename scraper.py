"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Usa Playwright para renderizar la SPA y extraer sentencias del DOM.
"""

import json
import time
import logging
import urllib.parse
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"


@dataclass
class Sentencia:
    numero: str
    tipo: str
    fecha: str
    ponente: str
    resumen: str
    pdf_url: str
    ficha_url: str


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    from playwright.sync_api import sync_playwright

    sentencias = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # Capturar TODOS los requests y responses
        all_responses = []

        def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" in ct and "corteconstitucional" in url and "google" not in url:
                try:
                    data = response.json()
                    all_responses.append({"url": url, "data": data})
                    # Log sin truncar para diagnóstico
                    data_str = json.dumps(data, ensure_ascii=False)
                    logger.info(f"JSON [{url.split('/')[-1]}]: {data_str[:1000]}")
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            # Probar con flag=true (modo búsqueda)
            for flag_val in [True, False]:
                payload = {
                    "textoSentencia": texto,
                    "numSentencia": numero,
                    "numeroCausa": causa,
                    "flag": flag_val,
                }
                search_url = f"{BASE_URL}/buscador-externo/principal/resultadoSentencia?search={urllib.parse.quote(json.dumps(payload))}"
                logger.info(f"Probando flag={flag_val}: {search_url}")
                all_responses.clear()
                page.goto(search_url, wait_until="networkidle", timeout=30000)
                time.sleep(5)

                # Extraer texto del DOM renderizado por Angular
                body_text = page.inner_text("body")
                logger.info(f"Texto del DOM (primeros 1000 chars): {body_text[:1000]}")

                # Buscar números de sentencia en el texto
                import re
                matches = re.findall(r'\d+-\d+-[A-Z]+/\d+', body_text)
                logger.info(f"Números de sentencia encontrados en DOM: {matches[:20]}")

                # Intentar extraer de los responses JSON
                for resp in all_responses:
                    data = resp["data"]
                    if isinstance(data, dict):
                        dato = data.get("dato", [])
                        if isinstance(dato, list) and dato:
                            # Verificar que no son analytics
                            first = dato[0] if dato else {}
                            if isinstance(first, dict) and "evento" not in first:
                                logger.info(f"dato[] tiene {len(dato)} items. Primer item: {json.dumps(first, ensure_ascii=False)[:300]}")
                                for item in dato[:max_results]:
                                    if isinstance(item, dict):
                                        s = _parse_item(item)
                                        if s.numero:
                                            sentencias.append(s)

                if sentencias or matches:
                    break

            # Si no encontró con URL de resultados, intentar desde la página principal
            if not sentencias:
                logger.info("Intentando desde la página principal...")
                all_responses.clear()
                page.goto(f"{BASE_URL}/buscador-externo/principal", wait_until="networkidle", timeout=30000)
                time.sleep(5)

                body_text = page.inner_text("body")
                logger.info(f"DOM página principal: {body_text[:500]}")

                # Intentar hacer clic en primer resultado si hay lista
                try:
                    items_visible = page.query_selector_all("mat-card, .card, .result, tr, li")
                    logger.info(f"Elementos de lista encontrados: {len(items_visible)}")
                    for el in items_visible[:3]:
                        logger.info(f"Elemento: {el.inner_text()[:100]}")
                except Exception as e:
                    logger.debug(f"Error buscando elementos: {e}")

                for resp in all_responses:
                    data = resp["data"]
                    if isinstance(data, dict):
                        dato = data.get("dato", [])
                        if isinstance(dato, list) and dato:
                            first = dato[0] if dato else {}
                            if isinstance(first, dict) and "evento" not in first:
                                logger.info(f"DATOS ENCONTRADOS: {len(dato)} items")
                                for item in dato[:max_results]:
                                    if isinstance(item, dict):
                                        s = _parse_item(item)
                                        if s.numero:
                                            sentencias.append(s)

            # Último recurso: regex en todo el DOM
            if not sentencias:
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
                logger.info(f"Sentencias por regex HTML: {len(sentencias)}")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def _parse_item(item: dict) -> "Sentencia":
    numero = next((str(item[k]) for k in [
        "numSentencia", "numero", "numberSentence", "num_sentencia",
        "numExpediente", "expediente", "identificador", "codigo"
    ] if item.get(k)), "")

    tipo = next((str(item[k]) for k in [
        "tipoSentencia", "tipo", "typeSentence", "tipoAccion"
    ] if item.get(k)), "")

    fecha = next((str(item[k]) for k in [
        "fechaSentencia", "fecha", "dateSentence", "fechaPublicacion", "anio"
    ] if item.get(k)), "")

    ponente = next((str(item[k]) for k in [
        "magistradoPonente", "ponente", "juezPonente", "magistrado", "jueza"
    ] if item.get(k)), "")

    resumen = next((str(item[k])[:500] for k in [
        "extracto", "resumen", "summary", "descripcion", "tema"
    ] if item.get(k)), "")

    pdf_url = next((str(item[k]) for k in [
        "urlPdf", "pdf_url", "urlDocumento", "linkPdf"
    ] if item.get(k)), "")

    ficha_url = ""
    if numero:
        ficha_url = f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(numero)}"

    return Sentencia(
        numero=numero.strip(), tipo=tipo.strip(), fecha=fecha.strip(),
        ponente=ponente.strip(), resumen=resumen.strip(),
        pdf_url=pdf_url.strip(), ficha_url=ficha_url,
    )


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
