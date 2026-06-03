"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
La API recibe el payload como: {"dato": base64(urlencode(json))}
Endpoint de búsqueda: 100_BUSCR_SNTNCIA
Estructura del formulario obtenida via Angular form group inspection.
"""

import base64
import json
import logging
import time
import urllib.parse
import requests
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
API_SEARCH = f"{BASE_URL}/buscador-externo/rest/api/sentencia/100_BUSCR_SNTNCIA"
API_CATALOG = f"{BASE_URL}/buscador-externo/rest/api/catalogoSentencia/100_OBT_RSMN_CTLG"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada",
}


def _to_iso(dt: datetime) -> str:
    """Convierte datetime a formato ISO que usa Angular: 2026-05-04T00:00:00.000Z"""
    return dt.strftime("%Y-%m-%dT00:00:00.000Z")


def _encode_payload(data: dict) -> str:
    json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    url_encoded = urllib.parse.quote(json_str)
    b64 = base64.b64encode(url_encoded.encode()).decode()
    return b64


def _call_api(session: requests.Session, url: str, payload: dict, extra_body: dict = None) -> dict:
    encoded = _encode_payload(payload)
    body = {"dato": encoded}
    if extra_body:
        body.update(extra_body)
    logger.info(f"POST {url.split('/')[-1]} | payload: {json.dumps(payload)[:300]} | extra: {extra_body}")
    resp = session.post(url, json=body, headers=HEADERS, timeout=30)
    logger.info(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            logger.info(f"Respuesta: {json.dumps(data, ensure_ascii=False)[:2000]}")
            return data
        except Exception as e:
            logger.error(f"Error parseando JSON: {e} | texto: {resp.text[:200]}")
    else:
        logger.warning(f"HTTP {resp.status_code}: {resp.text[:200]}")
    return {}


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


def _extract_sentencias(data: dict, max_results: int) -> list:
    sentencias = []
    dato = data.get("dato")
    if isinstance(dato, list) and dato:
        first = dato[0] if dato else {}
        if isinstance(first, dict):
            logger.info(f"Primer item: {json.dumps(first, ensure_ascii=False)}")
            for item in dato[:max_results]:
                if isinstance(item, dict):
                    s = _parse_item(item)
                    if s.numero:
                        sentencias.append(s)
    return sentencias


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    sentencias = []

    hoy = datetime.now()
    hace_30 = hoy - timedelta(days=30)
    iso_hasta = _to_iso(hoy)
    iso_desde = _to_iso(hace_30)
    logger.info(f"Rango ISO: {iso_desde} → {iso_hasta}")

    session = requests.Session()

    try:
        session.get(f"{BASE_URL}/buscador-externo/principal", headers=HEADERS, timeout=15)
        logger.info("Cookies obtenidas")
    except Exception as e:
        logger.debug(f"Error cookies: {e}")

    # Inicializar catálogo igual que el navegador
    try:
        _call_api(session, API_CATALOG, {})
        logger.info("Catálogo inicializado")
    except Exception as e:
        logger.debug(f"Error catálogo: {e}")

    # Estructura exacta del formulario Angular (obtenida via __ngContext__ inspection)
    # Los campos de selección múltiple (jueces, decisiones, etc.) deben ser arrays
    base_form = {
        "numSentencia": numero,
        "numeroCausa": causa,
        "textoSentencia": texto,
        "tipoLegitimado": 100,
        "legitimados": "",
        "desde": iso_desde,
        "hasta": iso_hasta,
        "jueces": [],
        "decisiones": [],
        "intereses": [],
        "materias": [],
        "tipoAcciones": [],
        "asuntos": [],
        "tipoNorma": [],
        "merito": "",
        "novedad": "",
        "precedenteAprobado": "",
        "precedentePropuesto": "",
        "analisisMerito": "",
        "opcionBusqueda": 1,
    }

    # (payload_inner, extra_outer_body)
    payloads = [
        # 1. metadata en el cuerpo EXTERNO del request (no dentro de dato)
        (base_form, {"metadata": ""}),
        # 2. metadata no vacío en cuerpo externo
        (base_form, {"metadata": "sentencias"}),
        # 3. metadata + subBusqueda + motivo en cuerpo externo
        (base_form, {"metadata": "", "subBusqueda": "", "motivo": ""}),
        # 4. Metadata no vacío dentro del dato codificado
        ({"metadata": "sentencias", "subBusqueda": "", "motivo": "", **base_form}, None),
        # 5. Solo base_form sin nada extra
        (base_form, None),
    ]

    for i, (payload, extra) in enumerate(payloads):
        logger.info(f"\n--- Intento {i+1} ---")
        data = _call_api(session, API_SEARCH, payload, extra)
        if data:
            msg = data.get("mensaje", "")
            tipo_msg = data.get("tipoMensaje", "")
            total = data.get("totalFilas", 0)
            logger.info(f"totalFilas={total}, tipoMensaje='{tipo_msg}', mensaje='{msg}'")
            found = _extract_sentencias(data, max_results)
            if found:
                sentencias.extend(found)
                logger.info(f"✓ {len(found)} sentencias con intento {i+1}")
                break
        time.sleep(1)

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
