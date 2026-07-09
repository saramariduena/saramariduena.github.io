# === Google Drive ===
# JSON con las credenciales de la cuenta de servicio de Google
# Generado en: https://console.cloud.google.com/iam-admin/serviceaccounts
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}

# ID de la carpeta de Google Drive donde se guardarán las sentencias
# Saca el ID de la URL: drive.google.com/drive/folders/ESTE_ES_EL_ID
DRIVE_FOLDER_ID=1ABC...XYZ

# === Alertas por correo (Gmail) ===
# Cuenta Gmail que envía las alertas
GMAIL_USER=tu_correo@gmail.com
# Contraseña de aplicación (no la contraseña normal):
# Ir a: Cuenta Google → Seguridad → Contraseñas de aplicación
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Correo(s) que recibirán las alertas (separados por coma)
NOTIFICATION_EMAILS=sara.mariduena@uees.edu.ec

# === Búsqueda (opcional, ajustar según necesidad) ===
# Texto a buscar en sentencias (vacío = todas las sentencias nuevas)
SEARCH_TEXT=
# Número máximo de sentencias a revisar por ejecución
MAX_SENTENCES=50

# === Búsqueda por juez — Función Judicial (buscar_por_juez.py) ===
# SOLO funciona ejecutado desde una computadora/red con IP ecuatoriana
# (la API del portal bloquea conexiones desde fuera de Ecuador).
# Nombre completo del juez a buscar (o pásalo como argumento del script)
JUEZ_NOMBRE=Oswaldo Sierra Ayora

# === Cómo ejecutar buscar_por_juez.py localmente (Ecuador) ===
# 1. pip install -r requirements.txt
# 2. playwright install chromium
# 3. Crear un archivo .env con GMAIL_USER, GMAIL_APP_PASSWORD y
#    NOTIFICATION_EMAILS (mismo formato que arriba)
# 4. python buscar_por_juez.py "Oswaldo Sierra Ayora"
#
# Genera un CSV local con los procesos encontrados y envía el listado por
# correo. Si no encuentra resultados, revisa fj_juez_resultados_raw.html
# y fj_juez_resultados_screenshot.png (se guardan junto al script) para
# ver qué mostró el portal — puede que la estructura de la página haya
# cambiado y los selectores de scraper_funcion_judicial.py necesiten ajuste.
