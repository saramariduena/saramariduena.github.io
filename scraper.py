"""
Scraper para sentencias de la Corte Constitucional del Ecuador.
Payload exacto obtenido interceptando el request real del navegador.
"""

import base64
import json
import logging
import urllib.parse
import requests
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

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


def _encode_payload(data: dict) -> str:
    json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    url_encoded = urllib.parse.quote(json_str)
    return base64.b64encode(url_encoded.encode()).decode()


def _call_api(session: requests.Session, url: str, payload: dict) -> dict:
    body = {"dato": _encode_payload(payload)}
    logger.info(f"POST {url.split('/')[-1]} | {json.dumps(payload)[:300]}")
    resp = session.post(url, json=body, headers=HEADERS, timeout=30)
    logger.info(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            logger.info(f"Respuesta: {json.dumps(data, ensure_ascii=False)[:2000]}")
            return data
        except Exception as e:
            logger.error(f"Error JSON: {e} | {resp.text[:200]}")
    else:
        logger.warning(f"HTTP {resp.status_code}: {resp.text[:300]}")
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
        "fechaSentencia", "fecha", "dateSentence", "fechaPublicacion",
        "fechaDecision", "anio"
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
    hoy = datetime.now()
    hace_30 = hoy - timedelta(days=30)
    # Formato exacto del buscador: "YYYY-MM-DD;YYYY-MM-DD"
    fecha_decision = f"{hace_30.strftime('%Y-%m-%d')};{hoy.strftime('%Y-%m-%d')}"
    logger.info(f"fechaDecision: {fecha_decision}")

    session = requests.Session()
    try:
        session.get(f"{BASE_URL}/buscador-externo/principal", headers=HEADERS, timeout=15)
        _call_api(session, API_CATALOG, {})
    except Exception as e:
        logger.debug(f"Init error: {e}")

    # Payload exacto capturado del navegador real
    payload = {
        "numSentencia": numero,
        "numeroCausa": causa,
        "textoSentencia": texto,
        "motivo": "",
        "metadata": "",
        "subBusqueda": "",
        "tipoLegitimado": 100,
        "legitimados": "",
        "tipoAcciones": [],
        "materias": [],
        "intereses": [],
        "decisiones": [],
        "jueces": [],
        "derechoDemandado": [],
        "derechosTratado": [],
        "derechosVulnerado": [],
        "temaEspecificos": [],
        "conceptos": [],
        "fechaNotificacion": "",
        "fechaDecision": fecha_decision,
        "sort": "desc",
        "precedenteAprobado": "",
        "precedentePropuesto": "",
        "tipoNormas": [],
        "asuntos": [],
        "analisisMerito": "",
        "novedad": "",
        "merito": "",
        "paginacion": {"page": 1, "pageSize": max_results, "total": 0, "contar": True},
        "flag": True,
    }

    data = _call_api(session, API_SEARCH, payload)
    sentencias = []

    if data:
        msg = data.get("mensaje", "")
        total = data.get("totalFilas", 0)
        logger.info(f"totalFilas={total}, mensaje='{msg}'")
        dato = data.get("dato")
        if isinstance(dato, list) and dato:
            logger.info(f"Primer item: {json.dumps(dato[0], ensure_ascii=False)}")
            for item in dato[:max_results]:
                if isinstance(item, dict):
                    s = _parse_item(item)
                    if s.numero:
                        sentencias.append(s)

    logger.info(f"Total sentencias: {len(sentencias)}")
    return sentencias


def sentencias_to_dicts(sentencias: list) -> list:
    return [asdict(s) for s in sentencias]
