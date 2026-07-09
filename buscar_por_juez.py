"""
Busca los procesos judiciales resueltos por un juez específico en el portal
de la Función Judicial del Ecuador y envía el listado por correo.

USO LOCAL ÚNICAMENTE (desde una computadora/red con IP ecuatoriana):
    la API real del portal bloquea conexiones desde fuera de Ecuador. Ver
    scraper_funcion_judicial.py para el detalle. Este script NO funcionará
    en GitHub Actions ni en entornos en la nube fuera de Ecuador.

Configuración (.env, ver env.example):
    GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFICATION_EMAILS

Ejecución:
    python buscar_por_juez.py "Oswaldo Sierra Ayora"
    (o definir JUEZ_NOMBRE en el .env y correr sin argumentos)
"""

import csv
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from scraper_funcion_judicial import buscar_procesos_por_juez
from notifier import send_listado_procesos_juez

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def guardar_csv(procesos: list[dict], nombre_juez: str) -> str:
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(c if c.isalnum() else "_" for c in nombre_juez).strip("_")
    archivo = f"procesos_{slug}_{fecha}.csv"
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["numero_causa", "texto_completo"])
        w.writeheader()
        w.writerows(procesos)
    logger.info(f"CSV guardado: {archivo} ({len(procesos)} filas)")
    return archivo


def run(nombre_juez: str):
    logger.info("=" * 60)
    logger.info(f"Búsqueda de procesos por juez: {nombre_juez}")
    logger.info("=" * 60)

    procesos = buscar_procesos_por_juez(nombre_juez, headless=True)

    if not procesos:
        logger.warning(
            "No se extrajo ningún proceso. Revisa fj_juez_resultados_raw.html "
            "y fj_juez_resultados_screenshot.png para ver qué devolvió el portal "
            "(puede que no haya resultados, o que la estructura de la página "
            "cambió y los selectores del scraper necesiten ajuste)."
        )
        send_listado_procesos_juez(nombre_juez, [])
        return

    csv_path = guardar_csv(procesos, nombre_juez)
    enviado = send_listado_procesos_juez(nombre_juez, procesos, csv_path=csv_path)
    if enviado:
        logger.info("Correo con el listado enviado correctamente.")
    else:
        logger.warning(
            "No se pudo enviar el correo (revisa GMAIL_USER/GMAIL_APP_PASSWORD "
            f"en tu .env). El listado quedó guardado en {csv_path}."
        )


if __name__ == "__main__":
    juez = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("JUEZ_NOMBRE", "")
    if not juez:
        print('Uso: python buscar_por_juez.py "Nombre del juez"')
        print("(o define JUEZ_NOMBRE en tu archivo .env)")
        sys.exit(1)
    run(juez)
