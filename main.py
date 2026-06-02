"""
Orquestador principal del monitor de sentencias de la Corte Constitucional del Ecuador.

Flujo:
1. Buscar sentencias nuevas en el buscador oficial
2. Comparar con el estado previo (state.json)
3. Subir PDFs nuevos a Google Drive
4. Enviar alerta por email si hay novedades
5. Actualizar el estado
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from scraper import buscar_sentencias, sentencias_to_dicts
from drive_uploader import upload_pdf_from_url, upload_json_summary
from notifier import send_alert, send_error_alert
from state_manager import load_state, save_state, find_new_sentencias, update_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run():
    logger.info("=" * 60)
    logger.info("Monitor de Sentencias — Corte Constitucional del Ecuador")
    logger.info(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("=" * 60)

    # Parámetros de búsqueda desde entorno
    search_text = os.environ.get("SEARCH_TEXT", "")
    max_results = int(os.environ.get("MAX_SENTENCES", "50"))
    drive_folder_id = os.environ.get("DRIVE_FOLDER_ID", "")

    try:
        # 1. Cargar estado previo
        state = load_state()
        logger.info(f"Estado previo: {len(state.get('seen_sentences', []))} sentencias conocidas")

        # 2. Scraping del buscador
        logger.info(f"Buscando sentencias (texto='{search_text}', max={max_results})...")
        sentencias = buscar_sentencias(texto=search_text, max_results=max_results)
        sentencias_dicts = sentencias_to_dicts(sentencias)

        if not sentencias_dicts:
            logger.warning("No se encontraron sentencias. Puede ser un problema temporal del sitio.")
            save_state(state)
            return

        logger.info(f"Sentencias obtenidas del buscador: {len(sentencias_dicts)}")

        # 3. Detectar novedades
        nuevas = find_new_sentencias(sentencias_dicts, state)
        logger.info(f"Sentencias NUEVAS detectadas: {len(nuevas)}")

        if not nuevas:
            logger.info("Sin novedades. No se envía alerta.")
            state = update_state(state, [])
            save_state(state)
            return

        # 4. Subir PDFs nuevos a Drive
        if drive_folder_id:
            for s in nuevas:
                if s.get("pdf_url"):
                    numero_safe = s["numero"].replace("/", "-").replace(" ", "_")
                    filename = f"Sentencia_{numero_safe}.pdf"
                    logger.info(f"Subiendo {filename} a Drive...")
                    upload_pdf_from_url(s["pdf_url"], filename, drive_folder_id)
                else:
                    logger.debug(f"Sin URL de PDF para {s.get('numero')}")

            # Subir resumen JSON actualizado
            summary = {
                "ultima_actualizacion": datetime.now().isoformat(),
                "total_sentencias": len(state.get("seen_sentences", [])) + len(nuevas),
                "nuevas_este_ciclo": nuevas,
            }
            upload_json_summary(summary, "resumen_sentencias.json", drive_folder_id)
        else:
            logger.warning("DRIVE_FOLDER_ID no configurado. No se subirá nada a Drive.")

        # 5. Enviar alerta por email
        sent = send_alert(nuevas)
        if sent:
            logger.info("Alerta de email enviada correctamente.")
        else:
            logger.warning("No se pudo enviar la alerta por email.")

        # 6. Actualizar estado
        state = update_state(state, nuevas)
        save_state(state)

        logger.info(f"Proceso completado. Total acumulado: {state['total_processed']} sentencias.")

    except Exception as e:
        logger.error(f"Error crítico: {e}", exc_info=True)
        send_error_alert(str(e))
        sys.exit(1)


if __name__ == "__main__":
    run()
