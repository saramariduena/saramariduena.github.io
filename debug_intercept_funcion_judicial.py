"""
Debug: intercepta las llamadas reales a la API del portal de procesos
judiciales de la Función Judicial del Ecuador, para descubrir el endpoint
de búsqueda, los campos del formulario y la forma de los resultados
(incluyendo si el juez es un filtro de búsqueda o solo un dato del resultado).

Mismo enfoque que debug_intercept.py (usado para la Corte Constitucional),
adaptado a este portal.
"""

import asyncio
import json
import re

from playwright.async_api import async_playwright

BASE_URL = "https://procesosjudiciales.funcionjudicial.gob.ec"

STATIC_EXT = re.compile(r"\.(js|css|png|jpg|jpeg|svg|gif|woff2?|ttf|eot|ico|map)(\?|$)", re.IGNORECASE)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
            ignore_https_errors=True,
        )
        page = await context.new_page()

        captured = []

        async def on_response(resp):
            try:
                req = resp.request
                url = resp.url
                if STATIC_EXT.search(url):
                    return
                ctype = resp.headers.get("content-type", "")
                is_json = "json" in ctype
                looks_like_api = any(k in url.lower() for k in ["/api/", "consulta", "provincia", "catalogo", "juez", "busqueda", "rest"])
                if req.method == "GET" and not is_json and not looks_like_api and resp.status < 400:
                    return

                req_body = req.post_data or ""
                body_preview = ""
                if is_json:
                    try:
                        body_preview = (await resp.text())[:2000]
                    except Exception:
                        body_preview = "<no se pudo leer el body>"

                captured.append({
                    "method": req.method,
                    "url": url,
                    "status": resp.status,
                    "request_body": req_body[:1500],
                    "response_preview": body_preview,
                })
                print(f"\n[{req.method}] {url} -> {resp.status}")
                if req_body:
                    print(f"  REQUEST BODY: {req_body[:800]}")
                if body_preview:
                    print(f"  RESPONSE: {body_preview[:1200]}")
            except Exception as e:
                print(f"[capture error] {e}")

        async def on_request_failed(req):
            try:
                if STATIC_EXT.search(req.url):
                    return
                failure = req.failure
                print(f"\n[REQUEST FAILED] [{req.method}] {req.url} -> {failure}")
            except Exception as e:
                print(f"[requestfailed capture error] {e}")

        page.on("response", on_response)
        page.on("requestfailed", on_request_failed)

        print(f"Cargando {BASE_URL} ...")
        try:
            await page.goto(BASE_URL, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            print(f"[!] Aviso al cargar página: {e}")
        await asyncio.sleep(3)

        try:
            await page.screenshot(path="fj_home.png", full_page=True)
            print("\nScreenshot guardado: fj_home.png")
        except Exception as e:
            print(f"[!] No se pudo capturar screenshot: {e}")

        # Volcar todos los campos de formulario visibles en la carga inicial
        fields = await page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input, select, textarea, button').forEach(el => {
                out.push({
                    tag: el.tagName,
                    type: el.type || '',
                    id: el.id || '',
                    name: el.name || '',
                    formcontrolname: el.getAttribute('formcontrolname') || '',
                    placeholder: el.placeholder || '',
                    text: (el.innerText || el.value || '').slice(0, 60),
                });
            });
            return out;
        }""")
        print("\n=== CAMPOS DEL FORMULARIO (carga inicial) ===")
        print(json.dumps(fields, indent=2, ensure_ascii=False))

        # Detectar posible captcha
        html_lower = (await page.content()).lower()
        if "recaptcha" in html_lower or "captcha" in html_lower or "hcaptcha" in html_lower:
            print("\n[!] POSIBLE CAPTCHA detectado en la página.")

        # Intentar seleccionar la primera opción disponible en cada <select>
        # (suele disparar cascadas provincia -> judicatura -> etc.)
        selects = await page.query_selector_all("select")
        print(f"\nSelects encontrados: {len(selects)}")
        for i, sel in enumerate(selects):
            try:
                options = await sel.query_selector_all("option")
                if len(options) > 1:
                    value = await options[1].get_attribute("value")
                    await sel.select_option(value=value)
                    print(f"  select[{i}] -> seleccionado value={value}")
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"  select[{i}] error: {e}")

        await asyncio.sleep(2)

        # Clic específico en "Procesos resueltos por juez"
        clicked = False
        try:
            btn = page.locator('button:has-text("Procesos resueltos por juez")').first
            if await btn.count() > 0:
                await btn.click(timeout=8000, force=True)
                print("\nClic en botón 'Procesos resueltos por juez'")
                clicked = True
                await page.wait_for_load_state("networkidle", timeout=20000)
                await asyncio.sleep(3)
        except Exception as e:
            print(f"\n[!] Error al hacer clic en 'Procesos resueltos por juez': {e}")

        if not clicked:
            print("\n[!] No se pudo hacer clic en el botón de búsqueda por juez.")

        print(f"\nURL actual: {page.url}")

        try:
            await page.screenshot(path="fj_after_search.png", full_page=True)
            print("Screenshot guardado: fj_after_search.png")
        except Exception as e:
            print(f"[!] No se pudo capturar screenshot final: {e}")

        # Volcar campos del formulario DESPUÉS del clic (pantalla de búsqueda por juez)
        fields_after = await page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('input, select, textarea, button, mat-select, [role="combobox"]').forEach(el => {
                out.push({
                    tag: el.tagName,
                    type: el.type || '',
                    id: el.id || '',
                    name: el.name || '',
                    formcontrolname: el.getAttribute('formcontrolname') || '',
                    placeholder: el.placeholder || el.getAttribute('placeholder') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    text: (el.innerText || el.value || '').slice(0, 80),
                });
            });
            return out;
        }""")
        print("\n=== CAMPOS DEL FORMULARIO (después de clic en 'Procesos resueltos por juez') ===")
        print(json.dumps(fields_after, indent=2, ensure_ascii=False))

        # Intentar abrir cualquier <mat-select> / combobox para ver catálogos (provincia, judicatura, etc.)
        combos = await page.query_selector_all('mat-select, [role="combobox"]')
        print(f"\nCombos/selects encontrados tras el clic: {len(combos)}")
        for i, combo in enumerate(combos):
            try:
                await combo.click(timeout=3000)
                await asyncio.sleep(1.5)
                options_text = await page.evaluate("""() => {
                    const opts = document.querySelectorAll('mat-option, [role="option"]');
                    return Array.from(opts).slice(0, 15).map(o => o.textContent.trim());
                }""")
                print(f"  combo[{i}] opciones (primeras 15): {options_text}")
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  combo[{i}] error: {e}")

        try:
            await page.screenshot(path="fj_juez_form.png", full_page=True)
            print("\nScreenshot guardado: fj_juez_form.png")
        except Exception as e:
            print(f"[!] No se pudo capturar screenshot del formulario de juez: {e}")

        # Escribir un texto de prueba (>=3 caracteres) y enviar la búsqueda para
        # capturar el endpoint real de la API de búsqueda.
        print("\n--- Escribiendo texto de prueba y buscando ---")
        try:
            texto_input = page.locator('input[formcontrolname="texto"]').first
            await texto_input.fill("Garcia")
            await asyncio.sleep(1.5)
            pre_count = len(captured)
            buscar_btn = page.locator('button[type="submit"]:has-text("Buscar")').first
            await buscar_btn.click(timeout=8000, force=True)
            print("Clic en 'Buscar' con texto de prueba 'Garcia'")
            await asyncio.sleep(2)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[!] Error al completar/enviar la búsqueda: {e}")
            pre_count = len(captured)

        print(f"\nURL tras buscar: {page.url}")
        new_reqs = captured[pre_count:]
        print(f"Requests nuevos tras la búsqueda: {len(new_reqs)}")
        for r in new_reqs:
            print(f"  [{r['method']}] {r['url']} -> {r['status']}")

        try:
            await page.screenshot(path="fj_resultados.png", full_page=True)
            print("Screenshot guardado: fj_resultados.png")
        except Exception as e:
            print(f"[!] No se pudo capturar screenshot de resultados: {e}")

        # Volcar cualquier tabla / lista de resultados visible
        resultados_html = await page.evaluate("""() => {
            const cont = document.querySelector('table, mat-table, [class*="resultado"], [class*="result"]');
            return cont ? cont.outerHTML.slice(0, 3000) : null;
        }""")
        print("\n=== HTML DE RESULTADOS (si existe) ===")
        print(resultados_html)

        print(f"\n=== TOTAL REQUESTS RELEVANTES CAPTURADOS: {len(captured)} ===")
        print("\n=== RESUMEN DE ENDPOINTS ÚNICOS ===")
        vistos = set()
        for c in captured:
            ep = c["url"].split("?")[0]
            if ep not in vistos:
                vistos.add(ep)
                print(f"  [{c['method']}] {ep}")

        await browser.close()


asyncio.run(main())
