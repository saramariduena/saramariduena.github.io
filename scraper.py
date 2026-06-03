"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Usa el formulario de Búsqueda Avanzada con los campos correctos:
- formcontrolname="desde" / "hasta" para el rango de fechas
- Captura la respuesta de búsqueda DESPUÉS de hacer clic en Buscar
"""

import json
import time
import logging
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
ADV_URL = f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada"


@dataclass
class Sentencia:
    numero: str
    tipo: str
    fecha: str
    ponente: str
    resumen: str
    pdf_url: str
    ficha_url: str


def _is_sentencia_item(item: dict) -> bool:
    """Detecta si un dict es una sentencia real (no un item de catálogo)."""
    sentence_keys = {"numSentencia", "num_sentencia", "numero", "numberSentence",
                     "tipoSentencia", "fechaSentencia", "magistradoPonente"}
    catalog_keys = {"nemonico", "nemonicoGrupo", "materias", "accion"}
    has_sentence = bool(sentence_keys & set(item.keys()))
    has_catalog = bool(catalog_keys & set(item.keys()))
    return has_sentence and not has_catalog


def _parse_item(item: dict) -> "Sentencia":
    numero = next((str(item[k]) for k in [
        "numSentencia", "numero", "numberSentence", "num_sentencia",
        "numExpediente", "expediente", "identificador", "codigo", "id"
    ] if item.get(k)), "")

    tipo = next((str(item[k]) for k in [
        "tipoSentencia", "tipo", "typeSentence", "tipoAccion", "accion"
    ] if item.get(k)), "")

    fecha = next((str(item[k]) for k in [
        "fechaSentencia", "fecha", "dateSentence", "fechaPublicacion",
        "fechaEmision", "anio", "year"
    ] if item.get(k)), "")

    ponente = next((str(item[k]) for k in [
        "magistradoPonente", "ponente", "juezPonente", "magistrado",
        "jueza", "juez", "nombreJuez"
    ] if item.get(k)), "")

    resumen = next((str(item[k])[:500] for k in [
        "extracto", "resumen", "summary", "descripcion", "tema", "materia"
    ] if item.get(k)), "")

    pdf_url = next((str(item[k]) for k in [
        "urlPdf", "pdf_url", "urlDocumento", "linkPdf", "rutaPdf"
    ] if item.get(k)), "")

    ficha_url = ""
    if numero:
        ficha_url = f"{BASE_URL}/buscador-externo/principal/fichaSentencia?numero={urllib.parse.quote(numero)}"

    return Sentencia(
        numero=numero.strip(), tipo=tipo.strip(), fecha=fecha.strip(),
        ponente=ponente.strip(), resumen=resumen.strip(),
        pdf_url=pdf_url.strip(), ficha_url=ficha_url,
    )


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    from playwright.sync_api import sync_playwright

    sentencias = []

    # Últimos 30 días (para monitoreo de novedades)
    hoy = datetime.now()
    hace_30 = hoy - timedelta(days=30)
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    fecha_desde = hace_30.strftime("%d/%m/%Y")
    logger.info(f"Rango: {fecha_desde} → {fecha_hasta}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Solo capturar respuestas DESPUÉS del clic en Buscar
        search_clicked = False
        post_search_responses = []

        def on_response(response):
            if not search_clicked:
                return  # ignorar respuestas del catálogo inicial
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" in ct and "corteconstitucional" in url and "google" not in url and "Analytics" not in url:
                try:
                    data = response.json()
                    post_search_responses.append({"url": url, "data": data})
                    logger.info(f"POST-SEARCH [{url.split('/')[-1][:35]}]: {json.dumps(data, ensure_ascii=False)[:2000]}")
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            logger.info("Cargando página de búsqueda avanzada...")
            page.goto(ADV_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Llenar el campo "desde"
            input_desde = page.query_selector("input[formcontrolname='desde']")
            if input_desde:
                input_desde.click()
                input_desde.fill(fecha_desde)
                input_desde.press("Tab")
                time.sleep(0.5)
                logger.info(f"Campo 'desde' = {fecha_desde}")
            else:
                logger.warning("No se encontró el campo 'desde'")

            # Llenar el campo "hasta"
            input_hasta = page.query_selector("input[formcontrolname='hasta']")
            if input_hasta:
                input_hasta.click()
                input_hasta.fill(fecha_hasta)
                input_hasta.press("Tab")
                time.sleep(0.5)
                logger.info(f"Campo 'hasta' = {fecha_hasta}")
            else:
                logger.warning("No se encontró el campo 'hasta'")

            # Llenar texto si se proporcionó
            if texto:
                input_texto = page.query_selector("input[formcontrolname='textoSentencia']")
                if input_texto:
                    input_texto.fill(texto)
                    logger.info(f"Campo 'textoSentencia' = {texto}")

            # Llenar número de sentencia si se proporcionó
            if numero:
                input_num = page.query_selector("input[formcontrolname='numSentencia']")
                if input_num:
                    input_num.fill(numero)
                    logger.info(f"Campo 'numSentencia' = {numero}")

            # Hacer clic en "Buscar"
            search_btn = page.query_selector("button:has-text('Buscar'), button[type='submit']")
            if search_btn:
                search_clicked = True
                logger.info("Haciendo clic en Buscar...")
                search_btn.click()
                time.sleep(8)  # esperar respuesta de búsqueda
                page.wait_for_load_state("networkidle", timeout=15000)
            else:
                logger.warning("No se encontró el botón Buscar")

            # Procesar respuestas de búsqueda
            logger.info(f"Respuestas post-búsqueda capturadas: {len(post_search_responses)}")
            for resp in post_search_responses:
                data = resp["data"]
                url = resp["url"]
                if isinstance(data, dict):
                    dato = data.get("dato")
                    total = data.get("totalFilas", 0)
                    mensaje = data.get("mensaje", "")
                    logger.info(f"  [{url.split('/')[-1][:30]}] totalFilas={total}, mensaje='{mensaje}'")

                    if isinstance(dato, list) and dato:
                        # Verificar si son sentencias reales
                        first = dato[0]
                        if isinstance(first, dict):
                            logger.info(f"  Primer item: {json.dumps(first, ensure_ascii=False)[:400]}")
                            if _is_sentencia_item(first):
                                logger.info(f"  ✓ Sentencias reales: {len(dato)}")
                                for item in dato[:max_results]:
                                    if isinstance(item, dict):
                                        s = _parse_item(item)
                                        if s.numero:
                                            sentencias.append(s)
                            else:
                                logger.info(f"  ✗ No son sentencias (catálogo)")

            # Si no capturó nada, log del DOM actual
            if not sentencias:
                dom = page.inner_text("body")
                logger.info(f"DOM actual tras búsqueda: {dom[:600]}")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
