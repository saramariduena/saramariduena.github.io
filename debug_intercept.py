"""
Script de diagnóstico: usa Playwright para interceptar el request real
que hace el navegador cuando busca sentencias en el buscador CCE.
Ejecutar como paso adicional en el workflow para ver el payload exacto.
"""
import asyncio
import json
import base64
import urllib.parse
from playwright.async_api import async_playwright

BASE_URL = "https://buscador.corteconstitucional.gob.ec"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        captured = []

        async def on_request(req):
            if "rest/api" in req.url and req.method == "POST":
                try:
                    body = req.post_data_json
                    dato = body.get("dato", "") if body else ""
                    decoded = ""
                    if dato:
                        try:
                            decoded = urllib.parse.unquote(base64.b64decode(dato).decode())
                        except Exception:
                            decoded = f"(error decodificando: {dato[:100]})"
                    info = {
                        "url": req.url,
                        "raw_body": body,
                        "dato_decoded": decoded,
                    }
                    captured.append(info)
                    print(f"\n[INTERCEPTED] {req.url.split('/')[-1]}")
                    print(f"  raw dato: {dato[:200]}")
                    print(f"  decoded:  {decoded}")
                except Exception as e:
                    print(f"[ERROR interceptando] {e}")

        page.on("request", on_request)

        print(f"Navegando a {BASE_URL}/buscador-externo/principal/busquedaAvanzada ...")
        await page.goto(f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=20000)

        # Esperar que cargue el formulario
        await asyncio.sleep(3)

        # Intentar llenar el campo "desde" de fecha
        desde_selectors = [
            'input[formcontrolname="desde"]',
            'input[placeholder*="desde" i]',
            'input[placeholder*="Desde" i]',
            'mat-date-range-input input:first-child',
        ]
        for sel in desde_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    await el.fill("04/05/2026")
                    await page.keyboard.press("Tab")
                    print(f"[OK] Llenó 'desde' con selector: {sel}")
                    break
            except Exception as e:
                print(f"[SKIP] {sel}: {e}")

        # Intentar llenar el campo "hasta" de fecha
        hasta_selectors = [
            'input[formcontrolname="hasta"]',
            'input[placeholder*="hasta" i]',
            'input[placeholder*="Hasta" i]',
            'mat-date-range-input input:last-child',
        ]
        for sel in hasta_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    await el.fill("03/06/2026")
                    await page.keyboard.press("Tab")
                    print(f"[OK] Llenó 'hasta' con selector: {sel}")
                    break
            except Exception as e:
                print(f"[SKIP] {sel}: {e}")

        await asyncio.sleep(1)

        # Buscar y hacer clic en el botón de búsqueda
        button_selectors = [
            'button[type="submit"]',
            'button:has-text("Buscar")',
            'button:has-text("BUSCAR")',
            'button.btn-buscar',
            'button.search-button',
        ]
        for sel in button_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    print(f"[OK] Clic en botón: {sel}")
                    break
            except Exception as e:
                print(f"[SKIP] {sel}: {e}")

        # Esperar respuestas de red
        await asyncio.sleep(5)

        if not captured:
            print("\n[!] No se interceptaron requests a la API. Inspeccionando HTML del formulario...")
            html = await page.content()
            # Buscar formcontrolname en el HTML
            import re
            names = re.findall(r'formcontrolname="([^"]+)"', html)
            print(f"formcontrolname encontrados: {names}")

            # Imprimir inputs visibles
            inputs = await page.locator('input').all()
            print(f"Total inputs en la página: {len(inputs)}")
            for inp in inputs[:20]:
                try:
                    attrs = await inp.evaluate("el => ({type: el.type, name: el.name, placeholder: el.placeholder, id: el.id})")
                    print(f"  input: {attrs}")
                except Exception:
                    pass
        else:
            print(f"\n[RESUMEN] Interceptados {len(captured)} requests")
            print(json.dumps(captured, indent=2, ensure_ascii=False))

        await browser.close()

asyncio.run(main())
