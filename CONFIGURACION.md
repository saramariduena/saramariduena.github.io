# Monitor de Sentencias — Corte Constitucional del Ecuador

Busca automáticamente sentencias nuevas, las descarga en Google Drive y envía alertas por correo.

---

## Configuración inicial (una sola vez)

### 1. Crear credenciales de Google Drive

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo (ej. `monitor-sentencias`)
3. Ir a **APIs y servicios → Biblioteca** → buscar **Google Drive API** → Habilitar
4. Ir a **APIs y servicios → Credenciales → Crear credenciales → Cuenta de servicio**
5. Nombre: `monitor-sentencias`, Rol: `Editor`
6. En la cuenta creada → **Claves → Agregar clave → JSON** → Descargar el archivo
7. El contenido del JSON descargado es el valor de `GOOGLE_CREDENTIALS_JSON`

### 2. Compartir la carpeta de Drive

1. En Google Drive, crear una carpeta (ej. `Sentencias CCE`)
2. Clic derecho → Compartir → Pegar el email de la cuenta de servicio (está dentro del JSON como `client_email`)
3. Darle permiso de **Editor**
4. Copiar el **ID de la carpeta** de la URL: `drive.google.com/drive/folders/`**`ESTE_ES_EL_ID`**

### 3. Crear contraseña de aplicación de Gmail

1. Ir a [Cuenta de Google](https://myaccount.google.com/) → Seguridad
2. Activar **Verificación en 2 pasos** (si no está activa)
3. Ir a **Contraseñas de aplicaciones**
4. Seleccionar app: `Correo`, dispositivo: `Otro (Monitor CCE)` → Generar
5. Guardar la contraseña de 16 caracteres generada

### 4. Configurar los Secrets en GitHub

En tu repositorio → **Settings → Secrets and variables → Actions → New repository secret**:

| Nombre del Secret | Valor |
|---|---|
| `GOOGLE_CREDENTIALS_JSON` | Contenido completo del JSON de la cuenta de servicio |
| `DRIVE_FOLDER_ID` | ID de la carpeta de Drive (ej. `1ABC...XYZ`) |
| `GMAIL_USER` | Tu correo Gmail (ej. `tu@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Contraseña de aplicación (16 caracteres) |
| `NOTIFICATION_EMAILS` | Correo(s) para alertas, separados por coma |

---

## Ejecución

### Automática
El monitor se ejecuta **todos los días a las 08:00 hora Ecuador** (configurado en `.github/workflows/monitor.yml`).

### Manual
1. Ir a **GitHub → Actions → Monitor Sentencias**
2. Clic en **Run workflow**
3. Opcionalmente ingresar texto de búsqueda y número máximo de sentencias

---

## Qué hace el sistema

```
Buscador CCE → Scraper → Comparar con state.json → Nuevas sentencias?
                                                          │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                       Subir PDFs              Enviar email
                                       a Google Drive          con novedades
                                              │
                                              ▼
                                    Actualizar state.json
                                    (commit automático)
```

## Ajustar horario

En `.github/workflows/monitor.yml` modificar la línea `cron`:
```
"0 13 * * *"   → 08:00 Ecuador (diario)
"0 13 * * 1-5" → solo lunes a viernes
"0 13,19 * * *"→ dos veces al día
```

---

## Estructura del proyecto

```
├── main.py              # Orquestador principal
├── scraper.py           # Extrae sentencias del buscador oficial
├── drive_uploader.py    # Sube PDFs a Google Drive
├── notifier.py          # Envía alertas por email
├── state_manager.py     # Gestiona qué sentencias ya se procesaron
├── state.json           # Estado persistente (actualizado automáticamente)
├── requirements.txt
├── .env.example         # Plantilla de variables de entorno (para desarrollo local)
└── .github/
    └── workflows/
        └── monitor.yml  # Automatización con GitHub Actions
```
