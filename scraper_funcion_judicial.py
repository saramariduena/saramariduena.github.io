"""
Scraper de "Procesos resueltos por juez" del portal de la Función Judicial
del Ecuador (procesosjudiciales.funcionjudicial.gob.ec).

IMPORTANTE — dos limitaciones confirmadas en producción (2026-07-09):

1. La API real de este portal (api.funcionjudicial.gob.ec) rechaza conexiones
   desde IPs fuera de Ecuador (net::ERR_CONNECTION_RESET desde GitHub Actions
   y desde sandboxes de Claude Code). Este script SOLO funciona ejecutado
   desde una computadora/red con IP ecuatoriana. Ver
   debug_intercept_funcion_judicial.py para el detalle del hallazgo.

2. La página de búsqueda (E-SATJE) exige resolver un reCAPTCHA ("No soy un
   robot") antes de poder buscar. Por eso el navegador NO corre en modo
   headless: se abre visible y el flujo se PAUSA después de escribir el
   nombre del juez, para que una persona marque el captcha y haga clic en
   "Buscar" a mano. El script continúa automáticamente desde ahí (extrae
   resultados, pagina, genera CSV y envía el correo). No es 100%
   desatendido — necesita ese paso manual cada vez que se ejecuta.

Automatiza el flujo real del portal con Playwright (no usa la API REST
directamente porque no se pudo capturar su contrato completo): clic en
"Procesos resueltos por juez", escribe el nombre del juez, pausa para el
captcha manual, y luego pagina y extrae resultados.

Como la estructura exacta de la tabla de resultados nunca pudo verificarse
en vivo antes del reCAPTCHA, la extracción es "best effort": guarda siempre
un HTML crudo y un screenshot de los resultados junto al CSV, para poder
ajustar los selectores si hace falta.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

BASE_URL = "https://procesosjudiciales.funcionjudicial.gob.ec"
MAX_PAGINAS = 20

# Patrón típico de número de causa/proceso judicial ecuatoriano, ej: 09332-2023-00123
PATRON_CAUSA = re.compile(r"\b\d{4,5}-\d{4}-\d{4,5}\b")


@dataclass
class ProcesoJudicial:
    numero_causa: str
    texto_completo: str


def _guardar_debug(page_html: str, prefix: str = "fj_juez"):
    Path(f"{prefix}_resultados_raw.html").write_text(page_html, encoding="utf-8")
    logger.info(f"HTML crudo de resultados guardado en {prefix}_resultados_raw.html")


async def _extraer_resultados_pagina(page) -> list[dict]:
    """Extrae filas de tabla o bloques repetidos con heurística genérica."""
    return await page.evaluate("""() => {
        const filas = [];

        // Estrategia 1: tabla estándar o mat-table
        const tabla = document.querySelector('table, mat-table');
        if (tabla) {
            const rows = tabla.querySelectorAll('tr, mat-row');
            rows.forEach(r => {
                const celdas = Array.from(r.querySelectorAll('td, mat-cell'))
                    .map(c => c.textContent.trim())
                    .filter(t => t.length > 0);
                if (celdas.length > 0) filas.push(celdas.join(' | '));
            });
            if (filas.length > 0) return filas;
        }

        // Estrategia 2: tarjetas/lista de resultados (heurística por clase)
        const candidatos = document.querySelectorAll(
            '[class*="resultado"], [class*="proceso"], [class*="causa"], mat-card, li'
        );
        candidatos.forEach(el => {
            const texto = el.textContent.trim().replace(/\\s+/g, ' ');
            if (texto.length > 20 && texto.length < 2000) filas.push(texto);
        });
        return filas;
    }""")


async def _hay_mensaje_sin_resultados(page) -> bool:
    texto = (await page.content()).lower()
    frases = ["no se encontraron", "sin resultados", "no existen registros", "no hay resultados"]
    return any(f in texto for f in frases)


async def _ir_a_siguiente_pagina(page) -> bool:
    """Intenta hacer clic en el botón 'siguiente' de paginación. Retorna True si avanzó."""
    try:
        siguiente = page.locator(
            'button[aria-label*="Next" i], button[aria-label*="siguiente" i], '
            '.mat-paginator-navigation-next'
        ).first
        if await siguiente.count() == 0:
            return False
        disabled = await siguiente.get_attribute("disabled")
        if disabled is not None:
            return False
        await siguiente.click(timeout=5000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await asyncio.sleep(2)
        return True
    except Exception as e:
        logger.debug(f"No se pudo paginar: {e}")
        return False


async def buscar_procesos_por_juez_async(
    nombre_juez: str, max_paginas: int = MAX_PAGINAS, headless: bool = False
) -> list[dict]:
    resultados_crudos: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
        )
        page = await context.new_page()

        logger.info(f"Cargando {BASE_URL} ...")
        await page.goto(BASE_URL, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle", timeout=30000)

        btn_juez = page.locator('button:has-text("Procesos resueltos por juez")').first
        await btn_juez.click(timeout=10000, force=True)
        await page.wait_for_load_state("networkidle", timeout=20000)
        await asyncio.sleep(1)

        texto_input = page.locator('input[formcontrolname="texto"]').first
        await texto_input.fill(nombre_juez)
        await asyncio.sleep(1)

        # El portal exige resolver un reCAPTCHA antes de buscar. Un script no
        # puede (ni debe) resolverlo automáticamente: se pausa aquí para que
        # una persona lo resuelva a mano en la ventana del navegador.
        print("\n" + "=" * 70)
        print("ACCIÓN MANUAL REQUERIDA en la ventana del navegador que se abrió:")
        print(f'  1. Verifica que el campo de búsqueda tenga: "{nombre_juez}"')
        print('  2. Marca la casilla "No soy un robot" (resuelve el desafío si aparece)')
        print('  3. Haz clic en el botón "Buscar"')
        print("  4. Espera a que aparezcan los resultados en pantalla")
        print("=" * 70)
        await asyncio.to_thread(input, "Cuando veas los resultados, vuelve aquí y presiona Enter para continuar... ")

        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        await asyncio.sleep(3)

        try:
            await page.screenshot(path="fj_juez_resultados_screenshot.png", full_page=True)
        except Exception as e:
            logger.warning(f"No se pudo tomar screenshot: {e}")

        _guardar_debug(await page.content())

        if await _hay_mensaje_sin_resultados(page):
            logger.warning("El portal indica que no hay resultados para esta búsqueda.")
            await browser.close()
            return []

        pagina = 1
        while pagina <= max_paginas:
            filas = await _extraer_resultados_pagina(page)
            logger.info(f"Página {pagina}: {len(filas)} filas extraídas")
            resultados_crudos.extend(filas)

            avanzo = await _ir_a_siguiente_pagina(page)
            if not avanzo:
                break
            pagina += 1

        await browser.close()

    # Deduplicar y estructurar
    vistos = set()
    procesos = []
    for texto in resultados_crudos:
        if texto in vistos:
            continue
        vistos.add(texto)
        m = PATRON_CAUSA.search(texto)
        numero_causa = m.group(0) if m else ""
        procesos.append(ProcesoJudicial(numero_causa=numero_causa, texto_completo=texto))

    logger.info(f"Total de procesos únicos extraídos: {len(procesos)}")
    return [asdict(p) for p in procesos]


def buscar_procesos_por_juez(nombre_juez: str, max_paginas: int = MAX_PAGINAS, headless: bool = False) -> list[dict]:
    return asyncio.run(buscar_procesos_por_juez_async(nombre_juez, max_paginas, headless))
