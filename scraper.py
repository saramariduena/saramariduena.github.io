"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
La API recibe el payload como: {"dato": base64(urlencode(json))}
Endpoint de búsqueda: 100_BUSCR_SNTNCIA
"""

import base64
import json
import logging
import time
import urllib.parse
import requests
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://buscador.corteconstitucional.gob.ec"
API_SEARCH = f"{BASE_URL}/buscador-externo/rest/api/sentencia/100_BUSCR_SNTNCIA"
API_STATS  = f"{BASE_URL}/buscador-externo/rest/api/sentencia/100_OBT_RSM_ESTDTCO"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/buscador-externo/principal/busquedaAvanzada",
}


def _encode_payload(data: dict) -> str:
    """Codifica el payload como base64(urlencode(json)) — formato que usa la API."""
    json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    url_encoded = urllib.parse.quote(json_str)
    b64 = base64.b64encode(url_encoded.encode()).decode()
    return b64


def _call_api(session: requests.Session, url: str, payload: dict) -> dict:
    """Llama a la API con el formato correcto."""
    encoded = _encode_payload(payload)
    body = {"dato": encoded}
    logger.info(f"POST {url.split('/')[-1]} | payload: {json.dumps(payload)}")
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


def buscar_sentencias(texto: str = "", numero: str = "", causa: str = "", max_results: int = 50) -> list:
    sentencias = []

    hoy = datetime.now()
    hace_30 = hoy - timedelta(days=30)
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    fecha_desde = hace_30.strftime("%d/%m/%Y")
    logger.info(f"Rango: {fecha_desde} → {fecha_hasta}")

    session = requests.Session()

    # Obtener cookies visitando la página principal
    try:
        session.get(f"{BASE_URL}/buscador-externo/principal", headers=HEADERS, timeout=15)
        logger.info("Cookies obtenidas de la página principal")
    except Exception as e:
        logger.debug(f"Error obteniendo cookies: {e}")

    # Payloads a intentar con los campos reales del formulario
    payloads_search = [
        # Con todos los campos del formulario
        {"textoSentencia": texto, "numSentencia": numero, "numeroCausa": causa,
         "desde": fecha_desde, "hasta": fecha_hasta, "flag": True},
        # Sin flag
        {"textoSentencia": texto, "numSentencia": numero, "numeroCausa": causa,
         "desde": fecha_desde, "hasta": fecha_hasta},
        # Solo fechas
        {"desde": fecha_desde, "hasta": fecha_hasta},
        # Con nombres alternativos
        {"textoSentencia": texto, "desde": fecha_desde, "hasta": fecha_hasta,
         "tipoAcciones": None, "jueces": None, "decisiones": None,
         "materias": None, "merito": None, "novedad": None, "flag": True},
    ]

    for i, payload in enumerate(payloads_search):
        logger.info(f"\n--- Intento {i+1} con 100_BUSCR_SNTNCIA ---")
        data = _call_api(session, API_SEARCH, payload)

        if data:
            dato = data.get("dato")
            total = data.get("totalFilas", 0)
            mensaje = data.get("mensaje", "")
            tipo_msg = data.get("tipoMensaje", "")
            logger.info(f"totalFilas={total}, tipoMensaje='{tipo_msg}', mensaje='{mensaje}'")

            if isinstance(dato, list) and dato:
                first = dato[0] if dato else {}
                if isinstance(first, dict):
                    logger.info(f"Primer item: {json.dumps(first, ensure_ascii=False)}")
                    for item in dato[:max_results]:
                        if isinstance(item, dict):
                            s = _parse_item(item)
                            if s.numero:
                                sentencias.append(s)

        if sentencias:
            logger.info(f"✓ Encontradas {len(sentencias)} sentencias con intento {i+1}")
            break

        time.sleep(1)

    # Si no funcionó con 100_BUSCR_SNTNCIA, intentar con 100_OBT_RSM_ESTDTCO
    if not sentencias:
        logger.info("\n--- Intentando con 100_OBT_RSM_ESTDTCO ---")
        payload_stats = {"desde": fecha_desde, "hasta": fecha_hasta, "flag": False}
        data = _call_api(session, API_STATS, payload_stats)
        if data:
            dato = data.get("dato")
            if isinstance(dato, list) and dato:
                first = dato[0] if dato else {}
                logger.info(f"Primer item stats: {json.dumps(first, ensure_ascii=False)}")
                for item in dato[:max_results]:
                    if isinstance(item, dict):
                        s = _parse_item(item)
                        if s.numero:
                            sentencias.append(s)

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias[:max_results]


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
