"""
Auditor técnico de protección de datos personales para sitios web.

Analiza una URL pública y genera un reporte con hallazgos relacionados con
el tratamiento de datos personales: cookies, rastreadores de terceros,
formularios que recolectan datos, cabeceras de seguridad, HTTPS/TLS y
presencia/contenido de la política de privacidad, con referencia a los
requisitos de la Ley Orgánica de Protección de Datos Personales (LOPDP)
de Ecuador.

Es una herramienta de apoyo técnico, no un dictamen legal: hay
obligaciones de la LOPDP (contratos con encargados del tratamiento,
registro de actividades, evaluaciones de impacto, etc.) que no se pueden
verificar automáticamente desde el sitio web público.

Uso:
    python auditor.py https://ejemplo.com
    python auditor.py https://ejemplo.com --output reporte.md
    python auditor.py https://ejemplo.com --timeout 45
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# --- Base de rastreadores/servicios de terceros conocidos ---
# dominio (o fragmento) -> nombre del servicio
KNOWN_TRACKERS = {
    "google-analytics.com": "Google Analytics",
    "googletagmanager.com": "Google Tag Manager",
    "doubleclick.net": "Google Ads / DoubleClick",
    "connect.facebook.net": "Meta Pixel",
    "facebook.com/tr": "Meta Pixel",
    "hotjar.com": "Hotjar",
    "clarity.ms": "Microsoft Clarity",
    "analytics.tiktok.com": "TikTok Pixel",
    "px.ads.linkedin.com": "LinkedIn Insight",
    "criteo.com": "Criteo",
    "adsrvr.org": "The Trade Desk",
    "mixpanel.com": "Mixpanel",
    "segment.io": "Segment",
    "hs-scripts.com": "HubSpot",
    "hsforms.com": "HubSpot Forms",
    "widget.intercom.io": "Intercom",
    "amplitude.com": "Amplitude",
    "newrelic.com": "New Relic",
    "sentry.io": "Sentry",
}

PRIVACY_LINK_PATTERN = re.compile(
    r"pol[ií]tica.{0,3}(de)?.{0,3}privacidad"
    r"|aviso.{0,3}de.{0,3}privacidad"
    r"|tratamiento.{0,3}de.{0,3}datos"
    r"|protecci[oó]n.{0,3}de.{0,3}datos"
    r"|privacy.{0,3}policy",
    re.IGNORECASE,
)

PII_INPUT_TYPES = {"email", "tel", "password"}
PII_NAME_HINTS = re.compile(
    r"cedula|c[eé]dula|dni|pasaporte|direcci[oó]n|tel[eé]fono|telefono|"
    r"nombre|apellido|fecha.?nac|tarjeta|cvv|rfc|ruc",
    re.IGNORECASE,
)

# frase que debe aparecer en la política de privacidad -> qué requisito cubre
LOPDP_KEYWORDS = {
    "responsable del tratamiento": "identificación del responsable del tratamiento",
    "derechos arco": "mención de derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)",
    "consentimiento": "base de consentimiento del titular de los datos",
    "transferencia internacional": "tratamiento de transferencias internacionales de datos",
    "finalidad": "finalidad del tratamiento de los datos",
    "conservaci": "plazo o criterio de conservación de los datos",
}

SEVERIDAD_ORDEN = {"alto": 0, "medio": 1, "bajo": 2, "info": 3}


@dataclass
class Hallazgo:
    categoria: str
    severidad: str  # "alto" | "medio" | "bajo" | "info"
    descripcion: str


@dataclass
class ResultadoAuditoria:
    url: str
    fecha: str
    hallazgos: list = field(default_factory=list)

    def agregar(self, categoria: str, severidad: str, descripcion: str) -> None:
        self.hallazgos.append(Hallazgo(categoria, severidad, descripcion))


def _ruta_chromium() -> str | None:
    """Permite fijar la ruta al binario de Chromium vía variable de entorno
    (útil en entornos con un navegador preinstalado). Si no se define, se
    usa el Chromium que trae Playwright por defecto."""
    return os.environ.get("AUDITOR_CHROMIUM_PATH")


def _dominio_base(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


def capturar_sitio(url: str, timeout_ms: int = 30000) -> dict:
    """Carga la URL en un navegador headless y captura cookies, requests,
    cabeceras y detalles TLS de la respuesta principal."""
    requests_vistos: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_ruta_chromium())
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.on("request", lambda req: requests_vistos.append(req.url))

        try:
            response = page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        except PlaywrightTimeoutError:
            # el sitio sigue haciendo peticiones (polling, websockets, etc.);
            # seguimos con lo que ya se cargó.
            response = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

        html = page.content()
        cookies = context.cookies()
        headers = {k.lower(): v for k, v in (response.headers if response else {}).items()}
        status = response.status if response else None
        final_url = page.url

        security = None
        if response is not None:
            try:
                security = response.security_details()
            except PlaywrightError:
                security = None

        browser.close()

    return {
        "html": html,
        "cookies": cookies,
        "headers": headers,
        "status": status,
        "final_url": final_url,
        "security": security,
        "requests": requests_vistos,
    }


def revisar_https(final_url: str, resultado: ResultadoAuditoria) -> None:
    if not final_url.startswith("https://"):
        resultado.agregar(
            "Cifrado en tránsito",
            "alto",
            "El sitio se sirve sin HTTPS. Los datos personales enviados por "
            "los usuarios (formularios, cookies de sesión) viajan sin cifrar.",
        )
    else:
        resultado.agregar("Cifrado en tránsito", "info", "El sitio usa HTTPS.")


def revisar_certificado(security: dict | None, resultado: ResultadoAuditoria) -> None:
    if security is None:
        resultado.agregar(
            "Certificado TLS",
            "medio",
            "No se pudieron obtener los detalles del certificado TLS "
            "(sitio sin HTTPS o error al negociar la conexión).",
        )
        return

    valid_to = security.get("validTo")
    if valid_to is None:
        return

    expira = datetime.fromtimestamp(valid_to, tz=timezone.utc)
    dias_restantes = (expira - datetime.now(timezone.utc)).days
    if dias_restantes < 0:
        resultado.agregar("Certificado TLS", "alto", "El certificado TLS está vencido.")
    elif dias_restantes < 15:
        resultado.agregar(
            "Certificado TLS", "medio", f"El certificado TLS vence en {dias_restantes} días."
        )
    else:
        resultado.agregar(
            "Certificado TLS",
            "info",
            f"Certificado válido, emitido por {security.get('issuer', 'desconocido')}, "
            f"vence en {dias_restantes} días.",
        )


SECURITY_HEADERS = {
    "strict-transport-security": (
        "medio",
        "Falta la cabecera Strict-Transport-Security (HSTS): el navegador no "
        "fuerza HTTPS en visitas futuras, permitiendo ataques de downgrade.",
    ),
    "content-security-policy": (
        "medio",
        "Falta Content-Security-Policy: sin esta cabecera es más fácil que un "
        "script inyectado (XSS) exfiltre datos personales del usuario.",
    ),
    "x-content-type-options": (
        "bajo",
        "Falta X-Content-Type-Options: nosniff.",
    ),
    "referrer-policy": (
        "bajo",
        "Falta Referrer-Policy: la URL completa (que puede incluir datos "
        "personales en query params) puede filtrarse a sitios de terceros "
        "vía la cabecera Referer.",
    ),
}


def revisar_cabeceras(headers: dict, resultado: ResultadoAuditoria) -> None:
    for header, (severidad, descripcion) in SECURITY_HEADERS.items():
        if header not in headers:
            resultado.agregar("Cabeceras de seguridad", severidad, descripcion)
    if not any(h in headers for h in SECURITY_HEADERS):
        return
    presentes = [h for h in SECURITY_HEADERS if h in headers]
    if presentes:
        resultado.agregar(
            "Cabeceras de seguridad",
            "info",
            f"Cabeceras presentes: {', '.join(presentes)}.",
        )


def revisar_cookies(cookies: list[dict], url_base: str, resultado: ResultadoAuditoria) -> None:
    if not cookies:
        resultado.agregar("Cookies", "info", "El sitio no estableció cookies durante la carga.")
        return

    base = _dominio_base(url_base)
    terceros = []
    inseguras = []

    for c in cookies:
        dominio_cookie = (c.get("domain") or "").lstrip(".")
        es_propia = dominio_cookie == base or dominio_cookie.endswith("." + base)
        if not es_propia:
            terceros.append(dominio_cookie)
        if not c.get("secure"):
            inseguras.append(c.get("name"))

    resultado.agregar(
        "Cookies",
        "info",
        f"Se establecieron {len(cookies)} cookies "
        f"({len(cookies) - len(set(terceros))} propias, {len(set(terceros))} de terceros).",
    )

    if terceros:
        resultado.agregar(
            "Cookies",
            "medio",
            "Cookies de terceros detectadas en dominios: "
            + ", ".join(sorted(set(terceros)))
            + ". Requieren informar al usuario y, salvo excepción legal, contar con "
            "su consentimiento antes de establecerse.",
        )

    if inseguras:
        resultado.agregar(
            "Cookies",
            "medio",
            f"{len(inseguras)} cookie(s) sin el flag Secure "
            f"({', '.join(str(n) for n in inseguras[:8])}).",
        )


def revisar_rastreadores(requests_vistos: list[str], resultado: ResultadoAuditoria) -> None:
    detectados: dict[str, str] = {}
    for req_url in requests_vistos:
        host = urlparse(req_url).hostname or ""
        for fragmento, nombre in KNOWN_TRACKERS.items():
            if fragmento in host or fragmento in req_url:
                detectados[nombre] = fragmento

    if not detectados:
        resultado.agregar(
            "Rastreadores de terceros",
            "info",
            "No se detectaron rastreadores de terceros conocidos en la lista base.",
        )
        return

    for nombre, fragmento in detectados.items():
        resultado.agregar(
            "Rastreadores de terceros",
            "medio",
            f"Se detectó {nombre} ({fragmento}). Debe estar declarado en la política "
            "de privacidad y, si no es estrictamente necesario para el servicio, "
            "requiere consentimiento previo del usuario.",
        )


def revisar_formularios(html: str, resultado: ResultadoAuditoria) -> None:
    soup = BeautifulSoup(html, "html.parser")
    forms = soup.find_all("form")

    if not forms:
        resultado.agregar("Formularios", "info", "No se encontraron formularios en la página.")
        return

    for i, form in enumerate(forms, start=1):
        campos_pii = []
        for inp in form.find_all(["input", "textarea", "select"]):
            tipo = (inp.get("type") or "text").lower()
            etiqueta = " ".join(
                filter(None, [inp.get("name", ""), inp.get("id", ""), inp.get("placeholder", "")])
            )
            if tipo in PII_INPUT_TYPES or PII_NAME_HINTS.search(etiqueta):
                campos_pii.append(etiqueta or tipo)

        if not campos_pii:
            continue

        action = form.get("action") or ""
        accion_https = action == "" or action.startswith("https://") or action.startswith("/")
        tiene_checkbox_consentimiento = form.find("input", {"type": "checkbox"}) is not None

        if not accion_https:
            severidad = "alto"
            detalle = "envía los datos a una URL no-HTTPS"
        elif not tiene_checkbox_consentimiento:
            severidad = "medio"
            detalle = "no muestra una casilla de consentimiento junto al envío"
        else:
            severidad = "bajo"
            detalle = "incluye una casilla de consentimiento"

        resultado.agregar(
            "Formularios",
            severidad,
            f"Formulario #{i} recolecta datos personales "
            f"({', '.join(c for c in campos_pii[:5] if c)}) y {detalle}.",
        )


def revisar_politica_privacidad(html: str, url_base: str, resultado: ResultadoAuditoria) -> None:
    soup = BeautifulSoup(html, "html.parser")

    enlace = None
    for a in soup.find_all("a", href=True):
        texto = a.get_text(" ", strip=True)
        href = a["href"]
        if PRIVACY_LINK_PATTERN.search(texto) or PRIVACY_LINK_PATTERN.search(href):
            enlace = urljoin(url_base, href)
            break

    if enlace is None:
        resultado.agregar(
            "Política de privacidad",
            "alto",
            "No se encontró un enlace visible a una política de privacidad o "
            "aviso de tratamiento de datos.",
        )
        return

    resultado.agregar(
        "Política de privacidad", "info", f"Enlace a política de privacidad encontrado: {enlace}"
    )

    try:
        resp = requests.get(enlace, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        texto_politica = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True).lower()
    except requests.RequestException as e:
        resultado.agregar(
            "Política de privacidad",
            "bajo",
            f"No se pudo descargar la política de privacidad para revisar su contenido ({e}).",
        )
        return

    faltantes = [
        requisito
        for palabra_clave, requisito in LOPDP_KEYWORDS.items()
        if palabra_clave not in texto_politica
    ]
    if faltantes:
        resultado.agregar(
            "Política de privacidad",
            "medio",
            "La política de privacidad no menciona explícitamente: " + "; ".join(faltantes) + ".",
        )
    else:
        resultado.agregar(
            "Política de privacidad",
            "info",
            "La política de privacidad cubre los elementos clave revisados "
            "(responsable, derechos ARCO, consentimiento, finalidad, conservación).",
        )


def auditar(url: str, timeout_ms: int = 30000) -> ResultadoAuditoria:
    captura = capturar_sitio(url, timeout_ms=timeout_ms)
    resultado = ResultadoAuditoria(url=url, fecha=datetime.now().isoformat(timespec="seconds"))

    revisar_https(captura["final_url"], resultado)
    revisar_certificado(captura["security"], resultado)
    revisar_cabeceras(captura["headers"], resultado)
    revisar_cookies(captura["cookies"], captura["final_url"], resultado)
    revisar_rastreadores(captura["requests"], resultado)
    revisar_formularios(captura["html"], resultado)
    revisar_politica_privacidad(captura["html"], captura["final_url"], resultado)

    return resultado


def generar_reporte_markdown(resultado: ResultadoAuditoria) -> str:
    lineas = [
        f"# Auditoría de protección de datos personales",
        "",
        f"- **URL**: {resultado.url}",
        f"- **Fecha**: {resultado.fecha}",
        "",
    ]

    conteo = {"alto": 0, "medio": 0, "bajo": 0, "info": 0}
    for h in resultado.hallazgos:
        conteo[h.severidad] += 1
    lineas.append(
        f"**Resumen**: {conteo['alto']} alto(s), {conteo['medio']} medio(s), "
        f"{conteo['bajo']} bajo(s), {conteo['info']} informativo(s)."
    )
    lineas.append("")

    categorias = list(dict.fromkeys(h.categoria for h in resultado.hallazgos))
    for categoria in categorias:
        lineas.append(f"## {categoria}")
        hallazgos_cat = sorted(
            (h for h in resultado.hallazgos if h.categoria == categoria),
            key=lambda h: SEVERIDAD_ORDEN[h.severidad],
        )
        for h in hallazgos_cat:
            lineas.append(f"- **[{h.severidad.upper()}]** {h.descripcion}")
        lineas.append("")

    lineas.append(
        "> Esta auditoría es un apoyo técnico automatizado y no sustituye una "
        "revisión legal completa bajo la LOPDP (Ecuador) u otras normas "
        "aplicables: no verifica, por ejemplo, contratos con encargados del "
        "tratamiento, registros de actividades de tratamiento ni evaluaciones "
        "de impacto."
    )

    return "\n".join(lineas)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audita una página web en busca de indicios sobre su tratamiento de datos personales."
    )
    parser.add_argument("url", help="URL del sitio a auditar, ej. https://ejemplo.com")
    parser.add_argument("--output", "-o", help="Ruta de archivo .md donde guardar el reporte")
    parser.add_argument(
        "--timeout", type=int, default=30, help="Tiempo máximo de carga en segundos (default: 30)"
    )
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else f"https://{args.url}"

    try:
        resultado = auditar(url, timeout_ms=args.timeout * 1000)
    except (PlaywrightError, PlaywrightTimeoutError) as e:
        print(f"Error al cargar el sitio: {e}", file=sys.stderr)
        sys.exit(1)

    reporte = generar_reporte_markdown(resultado)
    print(reporte)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(reporte)
        print(f"\nReporte guardado en {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
