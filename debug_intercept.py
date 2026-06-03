"""
Debug v3: inspecciona el Angular form group directamente via ng.getComponent
para obtener la estructura exacta de datos que se envía al buscar.
"""
import asyncio
import json
import base64
import urllib.parse
from playwright.async_api import async_playwright

BASE_URL = "https://buscador.corteconstitucional.gob.ec"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-web-security"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # Capturar TODOS los requests POST
        all_requests = []
        async def on_request(req):
            if req.method == "POST":
                try:
                    body_text = req.post_data or ""
                    try:
                        body = json.loads(body_text) if body_text else {}
                    except Exception:
                        body = {"_raw": body_text[:500]}
                    dato = body.get("dato", "")
                    decoded = ""
                    if dato:
                        try:
                            decoded = urllib.parse.unquote(base64.b64decode(dato).decode())
                        except Exception:
                            decoded = f"RAW:{dato[:200]}"
                    ep = req.url.split("/")[-1].split("?")[0]
                    all_requests.append({"url": req.url, "endpoint": ep, "body": body, "decoded": decoded})
                    if "corteconstitucional" in req.url or "sentencia" in req.url.lower():
                        print(f"\n[API POST] {ep}")
                        print(f"  decoded: {decoded[:500]}")
                except Exception as e:
                    print(f"[POST error] {e}")
        page.on("request", on_request)

        print("Cargando página...")
        await page.goto(f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=25000)
        await asyncio.sleep(5)

        print(f"\nRequests en carga inicial: {len(all_requests)}")
        for r in all_requests:
            if "corteconstitucional" in r["url"]:
                print(f"  {r['endpoint']}: {r['decoded'][:200]}")

        # Inspeccionar Angular form group structure
        print("\n--- Inspeccionando Angular form ---")
        form_info = await page.evaluate("""() => {
            try {
                // Buscar el componente Angular de búsqueda avanzada
                const allEls = document.querySelectorAll('*');
                let formGroupValue = null;
                let formGroupKeys = null;

                for (const el of allEls) {
                    // Intentar acceder al __ngContext__ de Angular
                    const ctx = el.__ngContext__;
                    if (ctx) {
                        // Buscar en el contexto un FormGroup
                        for (const item of ctx) {
                            if (item && typeof item === 'object' && item.controls && typeof item.getRawValue === 'function') {
                                formGroupValue = item.getRawValue();
                                formGroupKeys = Object.keys(item.controls);
                                break;
                            }
                        }
                        if (formGroupValue) break;
                    }
                }

                return {
                    found: !!formGroupValue,
                    keys: formGroupKeys,
                    value: formGroupValue ? JSON.stringify(formGroupValue) : null
                };
            } catch(e) {
                return {error: e.toString()};
            }
        }""")
        print(f"Form group: {json.dumps(form_info, indent=2)}")

        # Llenar fechas y forzar Angular change detection
        print("\n--- Llenando fechas ---")
        result = await page.evaluate("""() => {
            function fillAngular(el, value) {
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, value);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('blur', {bubbles: true}));
            }

            const inputs = Array.from(document.querySelectorAll('input'));
            const desde = inputs.find(i => i.getAttribute('formcontrolname') === 'desde' ||
                                         (i.placeholder || '').toLowerCase().includes('desde'));
            const hasta = inputs.find(i => i.getAttribute('formcontrolname') === 'hasta' ||
                                         (i.placeholder || '').toLowerCase().includes('hasta'));

            if (desde) fillAngular(desde, '04/05/2026');
            if (hasta) fillAngular(hasta, '03/06/2026');

            return {
                desdeFound: !!desde, desdeValue: desde ? desde.value : null,
                hastaFound: !!hasta, hastaValue: hasta ? hasta.value : null
            };
        }""")
        print(f"Fill result: {result}")
        await asyncio.sleep(2)

        # Leer el form group DESPUÉS de llenar fechas
        form_after = await page.evaluate("""() => {
            try {
                const allEls = document.querySelectorAll('*');
                for (const el of allEls) {
                    const ctx = el.__ngContext__;
                    if (ctx) {
                        for (const item of ctx) {
                            if (item && typeof item === 'object' && item.controls && typeof item.getRawValue === 'function') {
                                return {keys: Object.keys(item.controls), value: JSON.stringify(item.getRawValue())};
                            }
                        }
                    }
                }
                return {found: false};
            } catch(e) {
                return {error: e.toString()};
            }
        }""")
        print(f"\nForm después de llenar fechas:")
        print(f"  keys: {form_after.get('keys')}")
        val = form_after.get('value')
        if val:
            try:
                parsed = json.loads(val)
                print(f"  value: {json.dumps(parsed, indent=4, ensure_ascii=False)}")
            except Exception:
                print(f"  value raw: {val[:500]}")

        # Capturar el request de búsqueda
        print("\n--- Intentando búsqueda ---")
        pre_count = len(all_requests)

        # Intentar click en botón Buscar
        try:
            buscar = page.locator('button:has-text("Buscar")').last
            if await buscar.count() > 0:
                await buscar.click()
                print("Clic en Buscar")
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(6)

        new_reqs = [r for r in all_requests[pre_count:] if "corteconstitucional" in r["url"]]
        print(f"\nRequests API después de buscar: {len(new_reqs)}")
        for r in new_reqs:
            print(f"  endpoint: {r['endpoint']}")
            print(f"  decoded: {r['decoded']}")
            print(f"  body keys: {list(r['body'].keys()) if isinstance(r['body'], dict) else 'N/A'}")

        if not new_reqs:
            print("\n[!] No se capturó request de búsqueda. Volcando todos los POST del ciclo:")
            for r in all_requests:
                print(f"  {r['endpoint']}: {r.get('decoded', '')[:100]}")

        await browser.close()

asyncio.run(main())
