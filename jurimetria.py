"""
Jurimetría Asistida por IA — Orquestador principal
Implementa el modelo pedagógico de tres fases para la enseñanza del
análisis empírico del Derecho en facultades de Derecho del Ecuador.

Fases:
  1. recopilar  — Descarga sentencias desde la Corte Constitucional o carga
                  archivos de texto desde una carpeta local (para EXPEL u otros).
  2. extraer    — Usa la IA (Claude) para extraer variables jurídicas estructuradas
                  de cada sentencia.
  3. analizar   — Calcula estadísticas descriptivas y exporta el CSV para análisis
                  en hoja de cálculo.

Uso rápido (taller):
  python jurimetria.py recopilar --max 30
  python jurimetria.py extraer
  python jurimetria.py analizar

Para cargar textos propios (ej: descargados de EXPEL):
  python jurimetria.py recopilar --carpeta ./mis_sentencias
  python jurimetria.py extraer
  python jurimetria.py analizar

Variables de entorno requeridas para la fase de extracción:
  ANTHROPIC_API_KEY   — clave de la API de Claude
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

DATOS_BRUTOS = Path("jurimetria_brutos.json")
DATOS_ENRIQUECIDOS = Path("jurimetria_enriquecidos.json")
CSV_SALIDA = Path("jurimetria_datos.csv")
RESUMEN_SALIDA = Path("jurimetria_resumen.txt")


# ---------------------------------------------------------------------------
# Fase 1 — Recopilación
# ---------------------------------------------------------------------------

def cmd_recopilar(args):
    """Descarga sentencias o carga textos desde carpeta local."""
    sentencias = []

    if args.carpeta:
        carpeta = Path(args.carpeta)
        if not carpeta.is_dir():
            logger.error(f"La carpeta '{carpeta}' no existe.")
            sys.exit(1)
        sentencias = _cargar_desde_carpeta(carpeta)
    else:
        sentencias = _descargar_corte_constitucional(
            texto=args.texto,
            max_results=args.max,
        )

    if not sentencias:
        logger.warning("No se obtuvieron sentencias. Revisa la conexión o la carpeta.")
        sys.exit(1)

    DATOS_BRUTOS.write_text(
        json.dumps(sentencias, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        f"Fase 1 completa: {len(sentencias)} sentencias guardadas en '{DATOS_BRUTOS}'"
    )
    logger.info(
        "Siguiente paso → formula tu pregunta de investigación y ejecuta: "
        "python jurimetria.py extraer"
    )


def _descargar_corte_constitucional(texto: str, max_results: int) -> list[dict]:
    from scraper import buscar_sentencias, sentencias_to_dicts

    logger.info(
        f"Descargando desde Corte Constitucional del Ecuador "
        f"(texto='{texto}', max={max_results})..."
    )
    sentencias = buscar_sentencias(texto=texto, max_results=max_results)
    return sentencias_to_dicts(sentencias)


def _cargar_desde_carpeta(carpeta: Path) -> list[dict]:
    """
    Carga archivos .txt o .json desde una carpeta.
    Útil para sentencias descargadas manualmente de EXPEL u otros repositorios.
    - Archivos .txt: cada archivo es una sentencia; el nombre de archivo se usa como número.
    - Archivo unico sentencias.json: lista de dicts con al menos {"numero", "resumen"}.
    """
    sentencias = []

    json_unico = carpeta / "sentencias.json"
    if json_unico.exists():
        datos = json.loads(json_unico.read_text(encoding="utf-8"))
        if isinstance(datos, list):
            logger.info(f"Cargando {len(datos)} sentencias desde {json_unico}")
            return datos

    archivos_txt = sorted(carpeta.glob("*.txt"))
    if not archivos_txt:
        logger.warning(f"No se encontraron archivos .txt en '{carpeta}'.")
        return []

    for archivo in archivos_txt:
        contenido = archivo.read_text(encoding="utf-8", errors="replace").strip()
        sentencias.append(
            {
                "numero": archivo.stem,
                "tipo": "",
                "fecha": "",
                "ponente": "",
                "resumen": contenido[:8000],
                "pdf_url": "",
                "ficha_url": str(archivo),
            }
        )
    logger.info(f"Cargadas {len(sentencias)} sentencias desde '{carpeta}'")
    return sentencias


# ---------------------------------------------------------------------------
# Fase 2 — Extracción con IA
# ---------------------------------------------------------------------------

def cmd_extraer(args):
    """Usa Claude para extraer variables jurídicas estructuradas de cada sentencia."""
    if not DATOS_BRUTOS.exists():
        logger.error(
            f"No se encontró '{DATOS_BRUTOS}'. Ejecuta primero: "
            "python jurimetria.py recopilar"
        )
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error(
            "ANTHROPIC_API_KEY no está configurado. "
            "Agrega la variable de entorno o créala en el archivo .env"
        )
        sys.exit(1)

    sentencias = json.loads(DATOS_BRUTOS.read_text(encoding="utf-8"))
    logger.info(f"Fase 2: extrayendo variables de {len(sentencias)} sentencias con IA...")

    from extractor_ia import extraer_lote

    # Si hay texto completo, usarlo; si no, usar el resumen disponible
    campo = "texto_completo" if any(s.get("texto_completo") for s in sentencias) else "resumen"
    enriquecidas = extraer_lote(sentencias, campo_texto=campo, delay=args.delay)

    DATOS_ENRIQUECIDOS.write_text(
        json.dumps(enriquecidas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        f"Fase 2 completa: datos enriquecidos guardados en '{DATOS_ENRIQUECIDOS}'"
    )
    logger.info(
        "Siguiente paso → ejecuta: python jurimetria.py analizar"
    )


# ---------------------------------------------------------------------------
# Fase 3 — Análisis y exportación
# ---------------------------------------------------------------------------

def cmd_analizar(args):
    """Genera estadísticas descriptivas y exporta el CSV."""
    fuente = DATOS_ENRIQUECIDOS if DATOS_ENRIQUECIDOS.exists() else DATOS_BRUTOS
    if not fuente.exists():
        logger.error(
            "No se encontraron datos. Ejecuta primero: "
            "python jurimetria.py recopilar"
        )
        sys.exit(1)

    sentencias = json.loads(fuente.read_text(encoding="utf-8"))
    logger.info(f"Fase 3: analizando {len(sentencias)} sentencias...")

    from analizador import exportar_csv, generar_resumen

    ruta_csv = exportar_csv(sentencias, ruta=str(CSV_SALIDA))
    resumen = generar_resumen(sentencias)

    RESUMEN_SALIDA.write_text(resumen, encoding="utf-8")
    print("\n" + resumen)

    logger.info(f"CSV exportado: {ruta_csv}")
    logger.info(f"Resumen guardado: {RESUMEN_SALIDA}")
    logger.info(
        "Abre el CSV en Excel o Google Sheets para continuar el análisis. "
        "Usa las preguntas del resumen como punto de partida para la discusión jurídica."
    )


# ---------------------------------------------------------------------------
# Flujo completo
# ---------------------------------------------------------------------------

def cmd_completo(args):
    """Ejecuta las tres fases en secuencia."""
    logger.info("Ejecutando flujo completo de jurimetría (Fases 1 → 2 → 3)")
    cmd_recopilar(args)
    cmd_extraer(args)
    cmd_analizar(args)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="jurimetria",
        description="Jurimetría Asistida por IA — Modelo pedagógico de tres fases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # recopilar
    p_rec = subparsers.add_parser("recopilar", help="Fase 1: descargar o cargar sentencias")
    p_rec.add_argument("--max", type=int, default=30,
                       help="Número máximo de sentencias a descargar (default: 30)")
    p_rec.add_argument("--texto", default="",
                       help="Texto de búsqueda para filtrar sentencias")
    p_rec.add_argument("--carpeta", default="",
                       help="Carpeta local con archivos .txt o sentencias.json")
    p_rec.set_defaults(func=cmd_recopilar)

    # extraer
    p_ext = subparsers.add_parser("extraer", help="Fase 2: extraer variables con IA")
    p_ext.add_argument("--delay", type=float, default=0.5,
                       help="Segundos entre llamadas a la API (default: 0.5)")
    p_ext.set_defaults(func=cmd_extraer)

    # analizar
    p_ana = subparsers.add_parser("analizar", help="Fase 3: estadísticas y CSV")
    p_ana.set_defaults(func=cmd_analizar)

    # completo
    p_todo = subparsers.add_parser("completo", help="Ejecutar las tres fases en secuencia")
    p_todo.add_argument("--max", type=int, default=30)
    p_todo.add_argument("--texto", default="")
    p_todo.add_argument("--carpeta", default="")
    p_todo.add_argument("--delay", type=float, default=0.5)
    p_todo.set_defaults(func=cmd_completo)

    args = parser.parse_args()
    logger.info("=" * 60)
    logger.info("Jurimetría Asistida por IA")
    logger.info(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 60)
    args.func(args)


if __name__ == "__main__":
    main()
