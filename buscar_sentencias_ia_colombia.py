"""
Búsqueda histórica en el buscador oficial de Relatoría de la Corte
Constitucional de Colombia de sentencias relacionadas con derecho digital
e inteligencia artificial: protección de datos, redes sociales, temas
electrónicos, IA y derechos digitales en general.

Mismos ejes de búsqueda que buscar_sentencias_ia.py (Ecuador), adaptados
a terminología colombiana (p. ej. "habeas data" es figura constitucional
propia en Colombia, art. 15 y Ley 1581 de 2012).

Este script:
  - Busca desde 1992 (entrada en funciones de la Corte) hasta hoy.
  - No compara contra ningún estado previo ni marca nada como "visto".
  - No envía correos ni sube archivos a Drive.

Los términos de búsqueda se pueden sobreescribir con la variable de entorno
TERMINOS_BUSQUEDA (separados por coma), por ejemplo para repetir solo la
búsqueda de IA: TERMINOS_BUSQUEDA="inteligencia artificial,algoritmo,chatgpt".

Requiere acceso de red real a corteconstitucional.gov.co. Ejecutar donde
haya salida a internet real (localmente o vía `workflow_dispatch` en GitHub
Actions), no en un sandbox con egress restringido.

Uso:
    python buscar_sentencias_ia_colombia.py
"""

import json
import logging
import os
import time

from scraper_colombia import buscar_sentencias, sentencias_to_dicts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Mismos tres ejes que en Ecuador: (1) protección de datos y trámites
# electrónicos básicos, (2) tecnologías emergentes / biometría / IA,
# (3) delitos y usos específicos de internet.
TERMINOS_DEFECTO = [
    # Tanda 1: protección de datos y trámites electrónicos
    "proteccion de datos personales",
    "habeas data",
    "redes sociales",
    "internet",
    "telefonia movil",
    "plataforma digital",
    "notificacion electronica",
    "firma electronica",
    "datos informaticos",
    "derecho al olvido",
    # Tanda 2: tecnologías emergentes, biometría e IA
    "inteligencia artificial",
    "algoritmo",
    "chatgpt",
    "sesgo algoritmico",
    "biometria",
    "reconocimiento facial",
    "big data",
    "aprendizaje automatico",
    "ciberseguridad",
    "criptomoneda",
    "blockchain",
    "comercio electronico",
    "geolocalizacion",
    "aplicacion movil",
    "whatsapp",
    "videovigilancia",
    "dron",
    # Tanda 3: delitos y usos específicos de internet
    "voto electronico",
    "internet de las cosas",
    "chatbot",
    "robot",
    "automatizacion",
    "contrato inteligente",
    "streaming",
    "cookies",
    "ciberacoso",
    "grooming",
    "pornografia infantil",
    "sexting",
    "nombre de dominio",
    "apuestas en linea",
    "influencer",
    "publicidad digital",
    "delito informatico",
    "suplantacion de identidad",
    "phishing",
    "estafa electronica",
    "vigilancia digital",
    "huella digital",
    "correo electronico",
    "mensajeria instantanea",
]

_override = os.environ.get("TERMINOS_BUSQUEDA", "").strip()
TERMINOS = [t.strip() for t in _override.split(",") if t.strip()] if _override else TERMINOS_DEFECTO


def main():
    encontradas = {}

    for termino in TERMINOS:
        logger.info(f"Buscando: '{termino}'")
        try:
            resultados = buscar_sentencias(texto=termino, max_results=500)
        except Exception as e:
            logger.error(f"Error buscando '{termino}': {e}")
            resultados = []

        logger.info(f"  -> {len(resultados)} resultado(s)")
        for s in resultados:
            encontradas.setdefault(s.numero, {"sentencia": s, "terminos": set()})
            encontradas[s.numero]["terminos"].add(termino)

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
    for _, item in sorted(encontradas.items()):
        s = item["sentencia"]
        terminos = sorted(item["terminos"])
        print(f"\nNúmero: {s.numero}")
        print(f"Año: {s.anio}")
        print(f"Términos que la encontraron: {', '.join(terminos)}")
        print(f"Título/resumen: {s.titulo[:300]}")
        print(f"Ficha: {s.ficha_url}")
        salida.append({**sentencias_to_dicts([s])[0], "terminos_encontrados": terminos})

    with open("sentencias_ia_encontradas_colombia.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Guardado en sentencias_ia_encontradas_colombia.json")


if __name__ == "__main__":
    main()
