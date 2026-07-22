"""
Búsqueda histórica en el buscador oficial de la Corte Constitucional del Ecuador
de sentencias relacionadas con derecho digital: protección de datos, redes
sociales, temas electrónicos y derechos digitales en general.

A diferencia de main.py (el monitor semanal), este script:
  - No compara contra state.json ni marca nada como "visto".
  - No envía correos ni sube archivos a Drive.
  - Busca en un rango de fechas amplio (desde la creación de la Corte
    Constitucional en 2008 hasta hoy), no solo en los últimos 30 días.

Los términos de búsqueda se pueden sobreescribir con la variable de entorno
TERMINOS_BUSQUEDA (separados por coma), por ejemplo para volver a correr la
búsqueda original de IA: TERMINOS_BUSQUEDA="inteligencia artificial,algoritmo".

Requiere acceso de red a buscador.corteconstitucional.gob.ec. Ejecutar donde
haya salida a internet real (localmente o vía `workflow_dispatch` en GitHub
Actions), no en un sandbox con egress restringido.

Uso:
    python buscar_sentencias_ia.py
"""

import json
import logging
import os
import sys
import time

from scraper import buscar_sentencias, sentencias_to_dicts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DIAS_HISTORICO = 6500  # ~18 años: cubre toda la existencia de la Corte Constitucional (desde 2008)

TERMINOS_DEFECTO = [
    "protección de datos personales",
    "hábeas data",
    "redes sociales",
    "internet",
    "telefonía móvil",
    "plataforma digital",
    "notificación electrónica",
    "firma electrónica",
    "datos informáticos",
]

_override = os.environ.get("TERMINOS_BUSQUEDA", "").strip()
TERMINOS = [t.strip() for t in _override.split(",") if t.strip()] if _override else TERMINOS_DEFECTO


def main():
    encontradas = {}

    for termino in TERMINOS:
        logger.info(f"Buscando: '{termino}'")
        try:
            resultados = buscar_sentencias(texto=termino, max_results=100, dias=DIAS_HISTORICO)
        except Exception as e:
            logger.error(f"Error buscando '{termino}': {e}")
            resultados = []

        logger.info(f"  -> {len(resultados)} resultado(s)")
        for s in resultados:
            encontradas.setdefault(s.numero or s.ficha_url, {"sentencia": s, "terminos": set()})
            encontradas[s.numero or s.ficha_url]["terminos"].add(termino)

        time.sleep(2)

    if not encontradas:
        print("\n" + "=" * 70)
        print("Sin resultados para los términos buscados:")
        print(", ".join(TERMINOS))
        print("=" * 70)
        return

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(encontradas)} sentencia(s) única(s) encontrada(s)")
    print("=" * 70)

    salida = []
    for _, item in encontradas.items():
        s = item["sentencia"]
        terminos = sorted(item["terminos"])
        print(f"\nNúmero: {s.numero}")
        print(f"Tipo: {s.tipo}")
        print(f"Fecha: {s.fecha}")
        print(f"Ponente: {s.ponente}")
        print(f"Términos que la encontraron: {', '.join(terminos)}")
        print(f"Resumen: {s.resumen[:300]}")
        print(f"Ficha: {s.ficha_url}")
        salida.append({**sentencias_to_dicts([s])[0], "terminos_encontrados": terminos})

    with open("sentencias_ia_encontradas.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Guardado en sentencias_ia_encontradas.json")


if __name__ == "__main__":
    main()
