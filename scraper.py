"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
El endpoint 100_BUSCR_SNTNCIA requiere rango de fechas obligatorio.
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

    # Rango de fechas: últimos 90 días hasta hoy
    hoy = datetime.now()
    hace_90 = hoy - timedelta(days=90)
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    fecha_desde = hace_90.strftime("%d/%m/%Y")

    # Formatos alternativos
    fecha_hasta_iso = hoy.strftime("%Y-%m-%d")
    fecha_desde_iso = hace_90.strftime("%Y-%m-%d")

    logger.info(f"Rango de búsqueda: {fecha_desde} → {fecha_hasta}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        all_responses = []

        def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" in ct and "corteconstitucional" in url and "google" not in url and "Analytics" not in url:
                try:
                    data = response.json()
                    all_responses.append({"url": url, "data": data})
                    data_str = json.dumps(data, ensure_ascii=False)
                    logger.info(f"JSON [{url.split('/')[-1][:30]}]: {data_str[:2000]}")
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            # Estrategia 1: usar Playwright para interactuar con el formulario de búsqueda
            logger.info("Cargando formulario de búsqueda...")
            page.goto(f"{BASE_URL}/buscador-externo/principal", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Intentar llenar el campo de fecha en el formulario (Búsqueda Avanzada)
            try:
                # Hacer clic en "Búsqueda Avanzada"
                adv = page.query_selector("text=Búsqueda Avanzada, a:has-text('Avanzada'), button:has-text('Avanzada')")
                if adv:
                    adv.click()
                    time.sleep(2)
                    logger.info("Clic en Búsqueda Avanzada")

                # Buscar campos de fecha
                date_inputs = page.query_selector_all("input[type='date'], input[placeholder*='fecha' i], input[placeholder*='desde' i], input[placeholder*='hasta' i], mat-datepicker-input")
                logger.info(f"Campos de fecha encontrados: {len(date_inputs)}")

                for i, inp in enumerate(date_inputs):
                    placeholder = inp.get_attribute("placeholder") or ""
                    name = inp.get_attribute("name") or ""
                    logger.info(f"Campo fecha {i}: placeholder='{placeholder}' name='{name}'")
            except Exception as e:
                logger.debug(f"Error con formulario avanzado: {e}")

            # Estrategia 2: cargar directamente el URL de resultados con fechas en el payload
            payloads_to_try = [
                # Payload con fechas en formato DD/MM/YYYY
                {
                    "textoSentencia": texto, "numSentencia": numero,
                    "numeroCausa": causa, "flag": True,
                    "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
                },
                {
                    "textoSentencia": texto, "numSentencia": numero,
                    "numeroCausa": causa, "flag": True,
                    "fechaInicio": fecha_desde, "fechaFin": fecha_hasta,
                },
                {
                    "textoSentencia": texto, "numSentencia": numero,
                    "numeroCausa": causa, "flag": True,
                    "desde": fecha_desde, "hasta": fecha_hasta,
                },
                # Formato ISO
                {
                    "textoSentencia": texto, "numSentencia": numero,
                    "numeroCausa": causa, "flag": True,
                    "fechaDesde": fecha_desde_iso, "fechaHasta": fecha_hasta_iso,
                },
                # Sin texto, solo fechas
                {
                    "flag": True,
                    "fechaDesde": fecha_desde, "fechaHasta": fecha_hasta,
                },
            ]

            for payload in payloads_to_try:
                all_responses.clear()
                search_url = f"{BASE_URL}/buscador-externo/principal/resultadoSentencia?search={urllib.parse.quote(json.dumps(payload))}"
                logger.info(f"Probando payload: {json.dumps(payload)}")
                page.goto(search_url, wait_until="networkidle", timeout=30000)
                time.sleep(4)

                # Revisar si hay resultados
                for resp in all_responses:
                    data = resp["data"]
                    if isinstance(data, dict):
                        dato = data.get("dato")
                        total = data.get("totalFilas", 0)
                        mensaje = data.get("mensaje", "")
                        logger.info(f"totalFilas={total}, mensaje='{mensaje}', dato_type={type(dato).__name__}")

                        if isinstance(dato, list) and dato:
                            first = dato[0] if dato else {}
                            if isinstance(first, dict) and "evento" not in first:
                                logger.info(f"EXITO! {len(dato)} sentencias. Primer item: {json.dumps(first, ensure_ascii=False)[:500]}")
                                for item in dato[:max_results]:
                                    if isinstance(item, dict):
                                        s = _parse_item(item)
                                        if s.numero:
                                            sentencias.append(s)
                                if sentencias:
                                    break

                if sentencias:
                    break

            # Si aún no hay resultados, log del DOM para diagnóstico
            if not sentencias:
                dom_text = page.inner_text("body")
                logger.info(f"DOM actual: {dom_text[:500]}")
                logger.warning("No se encontraron sentencias con ninguno de los payloads probados.")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            browser.close()

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
