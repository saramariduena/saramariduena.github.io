"""
Envía alertas por correo electrónico cuando se detectan nuevas sentencias.
Usa Gmail con contraseña de aplicación (App Password).
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

ECU = timezone(timedelta(hours=-5))

logger = logging.getLogger(__name__)


def _build_html_body(sentencias: list[dict]) -> str:
    rows = ""
    for s in sentencias:
        ficha = s.get("ficha_url", "#")
        resumen_raw = s.get('resumen', '').strip()
        resumen = (resumen_raw[:200] + "...") if resumen_raw else "Sin resumen disponible"
        rows += f"""
        <tr>
          <td style="padding:8px;border:1px solid #ddd;font-weight:bold;">
            <a href="{ficha}" style="color:#1a56db;">{s.get('numero','—')}</a>
          </td>
          <td style="padding:8px;border:1px solid #ddd;">{s.get('tipo','—')}</td>
          <td style="padding:8px;border:1px solid #ddd;">{s.get('fecha','—')}</td>
          <td style="padding:8px;border:1px solid #ddd;">{s.get('ponente','—')}</td>
          <td style="padding:8px;border:1px solid #ddd;max-width:300px;">{resumen}</td>
        </tr>"""

    hoy = datetime.now(ECU).strftime('%d/%m/%Y')
    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#333;">
      <div style="max-width:900px;margin:0 auto;padding:20px;">
        <div style="background:#1a56db;color:white;padding:16px;border-radius:8px 8px 0 0;">
          <h2 style="margin:0;">⚖️ Corte Constitucional del Ecuador</h2>
          <p style="margin:4px 0 0;">Reporte de sentencias — {hoy}</p>
        </div>
        <div style="background:#f9fafb;padding:16px;border:1px solid #e5e7eb;">
          <p>¡Hola! Te envío tu reporte de sentencias del <strong>{hoy}</strong>.</p>
          <p>Se encontraron <strong>{len(sentencias)} sentencia(s) nueva(s)</strong>
             que aún no estaban en tu registro.</p>
          <table style="width:100%;border-collapse:collapse;background:white;">
            <thead>
              <tr style="background:#1a56db;color:white;">
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Número</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Tipo</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Fecha</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Ponente</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Resumen</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
          <p style="margin-top:16px;">
            <a href="https://buscador.corteconstitucional.gob.ec/buscador-externo/"
               style="background:#1a56db;color:white;padding:10px 20px;
                      border-radius:6px;text-decoration:none;">
              Ver buscador oficial →
            </a>
          </p>
        </div>
        <div style="padding:12px;font-size:12px;color:#6b7280;border-top:1px solid #e5e7eb;">
          Este correo fue generado automáticamente por el monitor de sentencias.
        </div>
      </div>
    </body>
    </html>"""


def send_alert(sentencias: list[dict]) -> bool:
    """
    Envía una alerta por email con las sentencias nuevas.
    Retorna True si se envió correctamente.
    """
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipients_raw = os.environ.get("NOTIFICATION_EMAILS", gmail_user)

    if not gmail_user or not gmail_password:
        logger.error("GMAIL_USER o GMAIL_APP_PASSWORD no configurados.")
        return False

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    if not recipients:
        logger.error("No hay destinatarios configurados en NOTIFICATION_EMAILS.")
        return False

    count = len(sentencias)
    subject = f"⚖️ [{count} nueva(s)] Sentencias Corte Constitucional Ecuador"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)

    # Versión texto plano
    text_lines = [
        f"Nuevas sentencias detectadas: {count}",
        f"Fecha: {datetime.now(ECU).strftime('%d/%m/%Y %H:%M')}",
        "",
    ]
    for s in sentencias:
        text_lines.append(f"- {s.get('numero','?')} | {s.get('tipo','?')} | {s.get('fecha','?')}")
        text_lines.append(f"  Ponente: {s.get('ponente','?')}")
        text_lines.append(f"  Ficha: {s.get('ficha_url','?')}")
        text_lines.append("")

    msg.attach(MIMEText("\n".join(text_lines), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html_body(sentencias), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
        logger.info(f"Alerta enviada a: {recipients}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar email: {e}")
        return False


def send_error_alert(error_msg: str) -> None:
    """Envía una alerta de error si el scraper falla."""
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipients_raw = os.environ.get("NOTIFICATION_EMAILS", gmail_user)

    if not gmail_user or not gmail_password:
        return

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    msg = MIMEMultipart()
    msg["Subject"] = "⚠️ Error en monitor Corte Constitucional Ecuador"
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)
    body = f"El monitor de sentencias encontró un error:\n\n{error_msg}\n\nRevisa los logs de GitHub Actions."
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipients, msg.as_string())
    except Exception as e:
        logger.error(f"No se pudo enviar alerta de error: {e}")
