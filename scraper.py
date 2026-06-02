"""
Scraper para el buscador de sentencias de la Corte Constitucional del Ecuador.
URL base: https://buscador.corteconstitucional.gob.ec/buscador-externo/
"""

import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

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


def _build_search_payload(texto: str = "", numero: str = "", causa: str = "") -> str:
    payload = {
        "textoSentencia": texto,
        "numSentencia": numero,
        "numeroCausa": causa,
        "flag": False,
    }
    return json.dumps(payload)


def _extract_sentencias_from_page(page) -> list[Sentencia]:
    """Extrae sentencias del DOM renderizado por la SPA Angular."""
    sentencias = []

    try:
        # Esperar a que carguen las tarjetas de sentencias
        page.wait_for_selector(".sentencia-card, .result-item, mat-card, .card", timeout=15000)
    except PWTimeout:
        logger.warning("No se encontraron tarjetas de sentencias en la página")
        return sentencias

    # Intentar múltiples selectores por si cambia el diseño
    cards = page.query_selector_all(".sentencia-card, .result-item, mat-card")

    for card in cards:
        try:
            numero = _safe_text(card, ".numero-sentencia, .title, h3, mat-card-title")
            tipo = _safe_text(card, ".tipo-sentencia, .subtitle, .tipo")
            fecha = _safe_text(card, ".fecha, .date, time")
            ponente = _safe_text(card, ".ponente, .judge, .magistrado")
            resumen = _safe_text(card, ".resumen, .summary, p, mat-card-content")

            # URL de la ficha
            link = card.query_selector("a")
            ficha_url = ""
            if link:
                href = link.get_attribute("href") or ""
                ficha_url = href if href.startswith("http") else f"{BASE_URL}{href}"

            # Número desde el URL si no se encontró en el texto
            if not numero and "numero=" in ficha_url:
                numero = ficha_url.split("numero=")[-1]

            if numero:
                sentencias.append(
                    Sentencia(
                        numero=numero.strip(),
                        tipo=tipo.strip(),
                        fecha=fecha.strip(),
                        ponente=ponente.strip(),
                        resumen=resumen.strip()[:500],
                        pdf_url="",  # se obtiene en get_pdf_url()
                        ficha_url=ficha_url,
                    )
                )
        except Exception as e:
            logger.debug(f"Error extrayendo tarjeta: {e}")
            continue

    return sentencias


def _safe_text(element, selector: str) -> str:
    try:
        el = element.query_selector(selector)
        return el.inner_text() if el else ""
    except Exception:
        return ""


def get_pdf_url(page, ficha_url: str) -> str:
    """Visita la ficha de una sentencia y extrae la URL del PDF."""
    try:
        page.goto(ficha_url, wait_until="networkidle", timeout=20000)
        # Buscar enlace al PDF
        pdf_link = page.query_selector("a[href*='.pdf'], a[href*='storage/api']")
        if pdf_link:
            href = pdf_link.get_attribute("href") or ""
            return href if href.startswith("http") else f"{BASE_URL}{href}"
    except Exception as e:
        logger.debug(f"No se pudo obtener PDF de {ficha_url}: {e}")
    return ""


def buscar_sentencias(
    texto: str = "",
    numero: str = "",
    causa: str = "",
    max_results: int = 50,
) -> list[Sentencia]:
    """
    Abre el buscador de la Corte Constitucional y retorna las sentencias encontradas.
    Usa Playwright para renderizar la SPA Angular.
    """
    sentencias: list[Sentencia] = []

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

        try:
            # Construir URL de búsqueda
            payload = _build_search_payload(texto, numero, causa)
            import urllib.parse
            search_url = f"{RESULT_URL}?search={urllib.parse.quote(payload)}"

            logger.info(f"Cargando: {search_url}")
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            found = _extract_sentencias_from_page(page)

            # Si no encontró nada con selectores específicos, intentar con la página principal
            if not found:
                logger.info("Intentando búsqueda desde página principal...")
                page.goto(SEARCH_URL, wait_until="networkidle", timeout=30000)
                time.sleep(2)

                # Escribir en el campo de búsqueda si hay texto
                if texto:
                    try:
                        search_input = page.query_selector("input[type='text'], input[type='search'], mat-form-field input")
                        if search_input:
                            search_input.fill(texto)
                            page.keyboard.press("Enter")
                            time.sleep(3)
                            page.wait_for_load_state("networkidle")
                    except Exception as e:
                        logger.debug(f"No se pudo usar el campo de búsqueda: {e}")

                found = _extract_sentencias_from_page(page)

            # Obtener URL de PDF para cada sentencia (hasta max_results)
            for s in found[:max_results]:
                if s.ficha_url and not s.pdf_url:
                    s.pdf_url = get_pdf_url(page, s.ficha_url)
                    time.sleep(0.5)

            sentencias = found[:max_results]
            logger.info(f"Sentencias encontradas: {len(sentencias)}")

        except Exception as e:
            logger.error(f"Error en el scraper: {e}")
        finally:
            browser.close()

    return sentencias


def sentencias_to_dicts(sentencias: list[Sentencia]) -> list[dict]:
    return [asdict(s) for s in sentencias]
