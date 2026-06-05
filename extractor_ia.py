"""
Extractor de variables jurídicas asistido por IA.
Fase 1 del modelo pedagógico de jurimetría: dada una sentencia en texto,
devuelve un diccionario con las variables estructuradas.
Requiere ANTHROPIC_API_KEY en el entorno.
"""

import json
import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)

VARIABLES = [
    "numero_causa",
    "tipo_accion",
    "organo_jurisdiccional",
    "fecha_inicio",
    "fecha_resolucion",
    "duracion_dias",
    "decision",
    "derecho_invocado",
    "materia",
    "etapa_prueba_dias",
    "observaciones",
]

EXTRACTION_PROMPT = """\
Eres un asistente jurídico especializado en análisis de decisiones judiciales del Ecuador.
Analiza el siguiente texto y extrae las variables indicadas. Responde ÚNICAMENTE con JSON válido.

VARIABLES:
- numero_causa: identificador del proceso (string)
- tipo_accion: tipo de acción o recurso (ej: "acción de protección", "apelación", "casación")
- organo_jurisdiccional: tribunal, juzgado o corte que resuelve
- fecha_inicio: fecha de presentación o ingreso del proceso (formato YYYY-MM-DD o null)
- fecha_resolucion: fecha de la sentencia o resolución (formato YYYY-MM-DD o null)
- duracion_dias: días entre fecha_inicio y fecha_resolucion (entero calculado, o null)
- decision: "favorable" | "desfavorable" | "inadmitida" | "inhibitoria" | "otro" | "no determinado"
- derecho_invocado: lista de derechos constitucionales o legales invocados (array de strings)
- materia: área del derecho (ej: "constitucional", "laboral", "civil", "contencioso-administrativo")
- etapa_prueba_dias: duración en días de la etapa probatoria si se menciona explícitamente (entero o null)
- observaciones: cualquier dato relevante no capturado arriba (string o null)

TEXTO:
{texto}
"""

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no está configurado en el entorno.")
        _client = anthropic.Anthropic(api_key=api_key)
        return _client
    except ImportError:
        raise ImportError("Instala el paquete anthropic: pip install anthropic")


def extraer_variables(texto: str, reintentos: int = 3) -> dict:
    """
    Extrae variables jurídicas estructuradas de un texto de sentencia usando Claude.
    Retorna un dict con las claves definidas en VARIABLES.
    En caso de error, retorna un dict vacío con claves nulas.
    """
    texto_limpio = texto.strip()[:12000]  # Limita tokens de entrada
    prompt = EXTRACTION_PROMPT.format(texto=texto_limpio)

    for intento in range(1, reintentos + 1):
        try:
            client = _get_client()
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            # Extrae el bloque JSON aunque venga envuelto en ```json ... ```
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                # Asegura que todas las claves esperadas existen
                for key in VARIABLES:
                    data.setdefault(key, None)
                return data
            else:
                logger.warning(f"Intento {intento}: respuesta sin JSON válido: {raw[:200]}")
        except Exception as e:
            logger.warning(f"Intento {intento} fallido: {e}")
            if intento < reintentos:
                time.sleep(2 ** intento)

    return _vacio()


def extraer_lote(sentencias: list[dict], campo_texto: str = "resumen",
                 delay: float = 0.5) -> list[dict]:
    """
    Extrae variables de una lista de sentencias.
    Cada elemento debe tener el campo indicado por `campo_texto`.
    Devuelve la lista enriquecida con las variables extraídas.
    """
    resultados = []
    total = len(sentencias)
    for i, s in enumerate(sentencias, 1):
        texto = s.get(campo_texto, "")
        if not texto:
            logger.warning(f"[{i}/{total}] Sin texto en campo '{campo_texto}', se omite.")
            variables = _vacio()
        else:
            logger.info(f"[{i}/{total}] Extrayendo variables de: {s.get('numero', '(sin número)')}")
            variables = extraer_variables(texto)
            if delay:
                time.sleep(delay)

        fila = {**s, **variables}
        resultados.append(fila)

    return resultados


def _vacio() -> dict:
    return {k: None for k in VARIABLES}
