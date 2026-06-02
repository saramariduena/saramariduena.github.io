"""
Sube PDFs de sentencias a Google Drive usando una cuenta de servicio.

Pasos para configurar:
1. Crear proyecto en https://console.cloud.google.com/
2. Habilitar Google Drive API
3. Crear cuenta de servicio → Descargar JSON de credenciales
4. Compartir la carpeta de Drive con el email de la cuenta de servicio
5. Poner el JSON en la variable GOOGLE_CREDENTIALS_JSON del entorno
"""

import io
import json
import logging
import os
import tempfile
from pathlib import Path

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _build_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_json:
        raise ValueError("La variable GOOGLE_CREDENTIALS_JSON no está configurada.")

    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _get_or_create_subfolder(service, parent_id: str, name: str) -> str:
    """Retorna el ID de una subcarpeta, creándola si no existe."""
    query = (
        f"'{parent_id}' in parents and "
        f"name='{name}' and "
        "mimeType='application/vnd.google-apps.folder' and "
        "trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    logger.info(f"Carpeta creada en Drive: {name}")
    return folder["id"]


def file_exists_in_drive(service, folder_id: str, filename: str) -> bool:
    """Verifica si ya existe un archivo con ese nombre en la carpeta."""
    query = f"'{folder_id}' in parents and name='{filename}' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    return len(results.get("files", [])) > 0


def upload_pdf_from_url(pdf_url: str, filename: str, folder_id: str) -> str:
    """
    Descarga un PDF desde una URL y lo sube a Google Drive.
    Retorna el ID del archivo en Drive, o "" si falla.
    """
    if not pdf_url:
        return ""

    try:
        service = _build_drive_service()

        if file_exists_in_drive(service, folder_id, filename):
            logger.info(f"Ya existe en Drive: {filename}")
            return "already_exists"

        # Descargar el PDF
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(pdf_url, headers=headers, timeout=60, stream=True)
        resp.raise_for_status()

        # Subir a Drive
        pdf_bytes = io.BytesIO(resp.content)
        media = MediaIoBaseUpload(pdf_bytes, mimetype="application/pdf", resumable=True)
        file_metadata = {"name": filename, "parents": [folder_id]}
        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )
        file_id = uploaded.get("id", "")
        logger.info(f"Subido a Drive: {filename} (id={file_id})")
        return file_id

    except Exception as e:
        logger.error(f"Error al subir {filename}: {e}")
        return ""


def upload_json_summary(data: dict, filename: str, folder_id: str) -> str:
    """Sube un resumen JSON al Drive (para registro histórico)."""
    try:
        service = _build_drive_service()
        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype="application/json", resumable=False
        )
        # Sobreescribir si ya existe
        query = f"'{folder_id}' in parents and name='{filename}' and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        existing = results.get("files", [])

        if existing:
            file_id = existing[0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            metadata = {"name": filename, "parents": [folder_id]}
            uploaded = service.files().create(body=metadata, media_body=media, fields="id").execute()
            file_id = uploaded.get("id", "")

        logger.info(f"Resumen JSON actualizado en Drive: {filename}")
        return file_id
    except Exception as e:
        logger.error(f"Error al subir JSON {filename}: {e}")
        return ""
