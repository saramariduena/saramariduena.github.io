"""
Script de diagnóstico v2: captura el payload real del buscador CCE.
Usa eventos Angular explícitos y espera larga para capturar el request de búsqueda.
"""
import asyncio
import json
import base64
import urllib.parse
from playwright.async_api import async_playwright

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
SEARCH_URL = f"{BASE_URL}/buscador-externo/rest/api/sentencia/100_BUSCR_SNTNCIA"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        all_requests = []

        async def on_request(req):
            if req.method == "POST":
                try:
                    body = req.post_data_json or {}
                    dato = body.get("dato", "")
                    decoded = ""
                    if dato:
                        try:
                            decoded = urllib.parse.unquote(base64.b64decode(dato).decode())
                        except Exception:
                            decoded = f"RAW:{dato[:200]}"
                    info = {"url": req.url, "body": body, "decoded": decoded}
                    all_requests.append(info)
                    endpoint = req.url.split("/")[-1]
                    print(f"[POST] {endpoint} | decoded: {decoded[:300]}")
                except Exception as e:
                    all_requests.append({"url": req.url, "error": str(e)})
                    print(f"[POST] {req.url.split('/')[-1]} error: {e}")

        page.on("request", on_request)

        print("1. Cargando página principal...")
        await page.goto(f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=20000)
        await asyncio.sleep(4)

        print(f"   Requests capturados en carga: {len(all_requests)}")
        for r in all_requests:
            print(f"   - {r['url'].split('/')[-1]}: {r.get('decoded', '')[:100]}")

        # Imprimir todos los campos del formulario
        print("\n2. Inspeccionando formulario...")
        form_fields = await page.evaluate("""() => {
            const inputs = document.querySelectorAll('input, select, textarea, mat-select');
            return Array.from(inputs).map(el => ({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                placeholder: el.placeholder || '',
                formcontrolname: el.getAttribute('formcontrolname') || '',
                value: el.value || ''
            }));
        }""")
        for f in form_fields:
            print(f"   {f}")

        # Buscar botones
        buttons = await page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim(),
                type: b.type,
                disabled: b.disabled,
                class: b.className
            }));
        }""")
        print(f"\n3. Botones encontrados: {len(buttons)}")
        for b in buttons[:10]:
            print(f"   {b}")

        # Llenar fechas con Angular events
        print("\n4. Llenando fechas con Angular events...")
        fecha_desde = "04/05/2026"
        fecha_hasta = "03/06/2026"

        filled = await page.evaluate(f"""async () => {{
            const allInputs = document.querySelectorAll('input');
            let desdeEl = null, hastaEl = null;
            for (const inp of allInputs) {{
                const fcn = inp.getAttribute('formcontrolname');
                const ph = (inp.placeholder || '').toLowerCase();
                if (fcn === 'desde' || ph.includes('desde')) desdeEl = inp;
                if (fcn === 'hasta' || ph.includes('hasta')) hastaEl = inp;
            }}

            function fillAngular(el, value) {{
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, value);
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
            }}

            if (desdeEl) fillAngular(desdeEl, '{fecha_desde}');
            if (hastaEl) fillAngular(hastaEl, '{fecha_hasta}');

            return {{
                desdeFound: !!desdeEl,
                hastaFound: !!hastaEl,
                desdeValue: desdeEl ? desdeEl.value : 'NOT FOUND',
                hastaValue: hastaEl ? hastaEl.value : 'NOT FOUND'
            }};
        }}""")
        print(f"   Resultado: {filled}")

        await asyncio.sleep(2)

        # Intentar submit por múltiples métodos
        print("\n5. Intentando enviar formulario...")
        pre_count = len(all_requests)

        # Método 1: click en botón Buscar
        try:
            btn = page.locator('button:has-text("Buscar")').first
            if await btn.count() > 0:
                await btn.click()
                print("   Clic en 'Buscar'")
                await asyncio.sleep(3)
        except Exception as e:
            print(f"   Error clic Buscar: {e}")

        # Método 2: submit del formulario
        if len(all_requests) == pre_count:
            try:
                await page.evaluate("""() => {
                    const forms = document.querySelectorAll('form');
                    if (forms.length > 0) forms[0].submit();
                }""")
                print("   form.submit()")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"   Error form.submit: {e}")

        # Método 3: Enter en el campo hasta
        if len(all_requests) == pre_count:
            try:
                hastaInput = page.locator('input[formcontrolname="hasta"]').first
                if await hastaInput.count() > 0:
                    await hastaInput.press("Enter")
                    print("   Enter en campo hasta")
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"   Error Enter: {e}")

        # Esperar requests adicionales
        await asyncio.sleep(5)

        new_requests = all_requests[pre_count:]
        print(f"\n6. Requests capturados después de submit: {len(new_requests)}")
        for r in new_requests:
            print(f"   URL: {r['url']}")
            print(f"   Body: {r.get('body', '')}")
            print(f"   Decoded: {r.get('decoded', '')}")
            print()

        if not new_requests:
            print("\n[!] No se capturó ningún request de búsqueda.")
            print("    Todos los requests POST del ciclo completo:")
            for r in all_requests:
                print(f"    {r['url'].split('/')[-1]}: {r.get('decoded', r.get('error', ''))[:200]}")

        await browser.close()

asyncio.run(main())
