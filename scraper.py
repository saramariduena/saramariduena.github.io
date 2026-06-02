"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Interactúa con el formulario Angular para capturar el request exacto.
"""

import json
import time
import logging
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

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


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    from playwright.sync_api import sync_playwright

    sentencias = []

    hoy = datetime.now()
    hace_90 = hoy - timedelta(days=90)
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    fecha_desde = hace_90.strftime("%d/%m/%Y")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Capturar requests Y responses para ver el body exacto
        all_responses = []
        request_bodies = {}

        def on_request(request):
            url = request.url
            if "corteconstitucional" in url and "google" not in url and "Analytics" not in url:
                try:
                    body = request.post_data_json or request.post_data or ""
                    request_bodies[url] = body
                    if body:
                        logger.info(f"REQUEST BODY [{url.split('/')[-1][:30]}]: {str(body)[:500]}")
                except Exception:
                    pass

        def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" in ct and "corteconstitucional" in url and "google" not in url and "Analytics" not in url:
                try:
                    data = response.json()
                    all_responses.append({"url": url, "data": data})
                    logger.info(f"RESPONSE [{url.split('/')[-1][:30]}]: {json.dumps(data, ensure_ascii=False)[:1000]}")
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            # ESTRATEGIA 1: Interactuar con el formulario Angular directamente
            logger.info("=== Estrategia 1: Interaccion con formulario ===")
            page.goto(f"{BASE_URL}/buscador-externo/principal", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Escanear todos los inputs del formulario
            inputs = page.query_selector_all("input, mat-select, select")
            logger.info(f"Total inputs en página: {len(inputs)}")
            for inp in inputs:
                try:
                    attrs = {
                        "type": inp.get_attribute("type") or "",
                        "placeholder": inp.get_attribute("placeholder") or "",
                        "name": inp.get_attribute("name") or "",
                        "id": inp.get_attribute("id") or "",
                        "formcontrolname": inp.get_attribute("formcontrolname") or "",
                        "ng-reflect-name": inp.get_attribute("ng-reflect-name") or "",
                    }
                    if any(attrs.values()):
                        logger.info(f"INPUT: {attrs}")
                except Exception:
                    pass

            # Intentar hacer clic en "Búsqueda Avanzada"
            try:
                adv_btns = page.query_selector_all("button, a, span, mat-tab-header")
                for btn in adv_btns:
                    txt = btn.inner_text().strip().lower()
                    if "avanzada" in txt or "advanced" in txt:
                        logger.info(f"Clic en: '{btn.inner_text().strip()}'")
                        btn.click()
                        time.sleep(2)
                        break
            except Exception as e:
                logger.debug(f"Error buscando botón avanzado: {e}")

            # ESTRATEGIA 2: Usar la URL de búsqueda avanzada
            logger.info("=== Estrategia 2: URL busqueda avanzada ===")
            all_responses.clear()
            request_bodies.clear()
            page.goto(f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            dom_adv = page.inner_text("body")
            logger.info(f"DOM busqueda avanzada: {dom_adv[:800]}")

            # Escanear inputs de la búsqueda avanzada
            inputs_adv = page.query_selector_all("input, mat-select, select, mat-datepicker-input")
            logger.info(f"Inputs en busqueda avanzada: {len(inputs_adv)}")
            for inp in inputs_adv:
                try:
                    attrs = {
                        "type": inp.get_attribute("type") or "",
                        "placeholder": inp.get_attribute("placeholder") or "",
                        "name": inp.get_attribute("name") or "",
                        "formcontrolname": inp.get_attribute("formcontrolname") or "",
                        "ng-reflect-name": inp.get_attribute("ng-reflect-name") or "",
                        "class": (inp.get_attribute("class") or "")[:50],
                    }
                    logger.info(f"INPUT ADV: {attrs}")
                except Exception:
                    pass

            # Intentar llenar campos de fecha en búsqueda avanzada
            try:
                all_inputs = page.query_selector_all("input")
                date_filled = 0
                for inp in all_inputs:
                    placeholder = (inp.get_attribute("placeholder") or "").lower()
                    fc_name = (inp.get_attribute("formcontrolname") or "").lower()
                    inp_type = (inp.get_attribute("type") or "").lower()

                    if any(k in placeholder + fc_name for k in ["desde", "hasta", "inicio", "fin", "fecha", "date", "start", "end"]):
                        value = fecha_desde if date_filled == 0 else fecha_hasta
                        inp.fill(value)
                        inp.press("Tab")
                        time.sleep(0.5)
                        logger.info(f"Llenado campo '{placeholder or fc_name}' con '{value}'")
                        date_filled += 1

                # Buscar y hacer clic en el botón de búsqueda
                search_btns = page.query_selector_all("button[type='submit'], button:has-text('Buscar'), button:has-text('Search')")
                if search_btns:
                    search_btns[0].click()
                    logger.info("Clic en botón Buscar")
                    time.sleep(5)
                    page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.info(f"Error llenando formulario: {e}")

            # Revisar resultados de ambas estrategias
            for resp in all_responses:
                data = resp["data"]
                if isinstance(data, dict):
                    dato = data.get("dato")
                    total = data.get("totalFilas", 0)
                    mensaje = data.get("mensaje", "")
                    logger.info(f"Resultado: totalFilas={total}, mensaje='{mensaje}'")

                    if isinstance(dato, list) and dato:
                        first = dato[0] if dato else {}
                        if isinstance(first, dict) and "evento" not in first:
                            logger.info(f"SENTENCIAS ENCONTRADAS: {len(dato)}")
                            logger.info(f"Primer item completo: {json.dumps(first, ensure_ascii=False)}")
                            for item in dato[:max_results]:
                                if isinstance(item, dict):
                                    s = _parse_item(item)
                                    if s.numero:
                                        sentencias.append(s)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
