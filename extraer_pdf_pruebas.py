"""
Descarga el PDF oficial de una o varias sentencias de la Corte Constitucional
del Ecuador (vía el mismo buscador real que usa scraper.py) y extrae del
texto completo los fragmentos relacionados con pruebas/elementos probatorios
y con el derecho constitucional vulnerado.

A diferencia de buscar_sentencias_ia.py (que busca por texto libre), este
script busca por NÚMERO DE CAUSA exacto, descarga el PDF correspondiente y
hace una búsqueda de palabras clave sobre el texto extraído.

No envía correos, no sube archivos a Drive, no hace commits. Solo imprime
resultados en el log y los guarda como artefacto JSON.

Los números de causa se pasan con la variable de entorno NUMEROS_BUSQUEDA
(separados por coma), por ejemplo:
    NUMEROS_BUSQUEDA="384-23-EP/26,2114-23-EP/26"

Requiere acceso de red real (GitHub Actions / workflow_dispatch), no un
sandbox con egress restringido.
"""

import json
import logging
import os
import re

import requests

from scraper import buscar_sentencias, sentencias_to_dicts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DIAS_HISTORICO = 6500  # cubre toda la existencia de la Corte (desde 2008)

NUMEROS_DEFECTO = [
    "3253-21-EP/24",
    "2281-21-EP/25",
    "2114-23-EP/26",
    "384-23-EP/26",
]

_override = os.environ.get("NUMEROS_BUSQUEDA", "").strip()
NUMEROS = [n.strip() for n in _override.split(",") if n.strip()] if _override else NUMEROS_DEFECTO

PALABRAS_CLAVE_PRUEBA = [
    "prueba", "pruebas", "elemento probatorio", "elementos probatorios",
    "evidencia", "aportó", "aportaron", "adjuntó", "adjuntaron",
    "captura de pantalla", "captura", "certificado", "certificación",
    "whatsapp", "correo electrónico", "llamada telefónica", "informe técnico",
    "constancia", "acta de audiencia", "registro de conexión",
]

PALABRAS_CLAVE_DERECHO = [
    "se vulneró", "se vulnera", "vulneración del derecho", "derecho vulnerado",
    "declara vulnerado", "violación del derecho",
]


def _extraer_texto_pdf(contenido: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf no está instalado")
        return ""
    import io
    try:
        reader = PdfReader(io.BytesIO(contenido))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:
        logger.error(f"Error extrayendo texto del PDF: {e}")
        return ""


def _buscar_parrafos(texto: str, palabras: list, contexto: int = 400) -> list:
    texto_lower = texto.lower()
    encontrados = []
    vistos = set()
    for palabra in palabras:
        for m in re.finditer(re.escape(palabra.lower()), texto_lower):
            inicio = max(0, m.start() - contexto)
            fin = min(len(texto), m.end() + contexto)
            fragmento = " ".join(texto[inicio:fin].split())
            clave = fragmento[:80]
            if clave not in vistos:
                vistos.add(clave)
                encontrados.append({"palabra_clave": palabra, "fragmento": fragmento})
    return encontrados


def main():
    salida = []

    for numero in NUMEROS:
        logger.info(f"Buscando número de causa exacto: '{numero}'")
        try:
            resultados = buscar_sentencias(numero=numero, max_results=5, dias=DIAS_HISTORICO)
        except Exception as e:
            logger.error(f"Error buscando '{numero}': {e}")
            resultados = []

        if not resultados:
            logger.warning(f"  -> Sin resultados para '{numero}'")
            salida.append({"numero_buscado": numero, "encontrado": False})
            continue

        s = resultados[0]
        logger.info(f"  -> Encontrado: {s.numero} | PDF: {s.pdf_url}")

        if not s.pdf_url:
            logger.warning(f"  -> Sin pdf_url para {s.numero}")
            salida.append({"numero_buscado": numero, "encontrado": True, "pdf_url": "", "nota": "sin pdf_url"})
            continue

        try:
            resp = requests.get(s.pdf_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=60)
            logger.info(f"  -> Descarga PDF status: {resp.status_code}, {len(resp.content)} bytes")
        except Exception as e:
            logger.error(f"  -> Error descargando PDF: {e}")
            salida.append({"numero_buscado": numero, "encontrado": True, "pdf_url": s.pdf_url, "nota": f"error descarga: {e}"})
            continue

        if resp.status_code != 200:
            salida.append({"numero_buscado": numero, "encontrado": True, "pdf_url": s.pdf_url, "nota": f"HTTP {resp.status_code}"})
            continue

        texto = _extraer_texto_pdf(resp.content)
        logger.info(f"  -> Texto extraído: {len(texto)} caracteres")

        pruebas = _buscar_parrafos(texto, PALABRAS_CLAVE_PRUEBA)
        derecho = _buscar_parrafos(texto, PALABRAS_CLAVE_DERECHO)

        print("\n" + "=" * 70)
        print(f"SENTENCIA: {s.numero} ({s.fecha})")
        print(f"PDF: {s.pdf_url}")
        print(f"Texto extraído: {len(texto)} caracteres")
        print(f"\n--- Fragmentos sobre PRUEBAS ({len(pruebas)}) ---")
        for p in pruebas[:15]:
            print(f"[{p['palabra_clave']}] ...{p['fragmento']}...")
        print(f"\n--- Fragmentos sobre DERECHO VULNERADO ({len(derecho)}) ---")
        for d in derecho[:15]:
            print(f"[{d['palabra_clave']}] ...{d['fragmento']}...")
        print("=" * 70)

        salida.append({
            "numero_buscado": numero,
            "encontrado": True,
            **sentencias_to_dicts([s])[0],
            "longitud_texto": len(texto),
            "fragmentos_pruebas": pruebas,
            "fragmentos_derecho": derecho,
        })

    with open("pruebas_extraidas.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print("\n[OK] Guardado en pruebas_extraidas.json")


if __name__ == "__main__":
    main()
