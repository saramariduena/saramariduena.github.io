# Auditoría de protección de datos personales

Herramienta técnica en Python que analiza una página web pública y genera
un reporte de indicios sobre su tratamiento de datos personales, con
referencia a la Ley Orgánica de Protección de Datos Personales (LOPDP) de
Ecuador.

## Qué revisa

- **Cifrado en tránsito**: si el sitio se sirve por HTTPS.
- **Certificado TLS**: validez y días para el vencimiento.
- **Cabeceras de seguridad**: `Strict-Transport-Security`,
  `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`.
- **Cookies**: cuántas se establecen, cuáles son de terceros y cuáles no
  tienen el flag `Secure`.
- **Rastreadores de terceros**: coincidencias contra una lista base de
  servicios conocidos (Google Analytics, Meta Pixel, Hotjar, etc.).
- **Formularios**: detecta campos que piden datos personales (correo,
  teléfono, cédula, dirección, etc.) y si el formulario usa HTTPS y
  muestra una casilla de consentimiento.
- **Política de privacidad**: busca un enlace visible y revisa si el
  texto menciona responsable del tratamiento, derechos ARCO,
  consentimiento, finalidad y plazo de conservación.

Cada hallazgo se clasifica como `ALTO`, `MEDIO`, `BAJO` o `INFO`.

## Limitaciones

Es un apoyo técnico automatizado, **no un dictamen legal**. No verifica
obligaciones que no son visibles desde el sitio público, como contratos
con encargados del tratamiento, registros de actividades de tratamiento,
evaluaciones de impacto (EIPD) o los procedimientos internos ante una
brecha de seguridad.

## Instalación

```bash
cd auditoria-proteccion-datos
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python auditor.py https://ejemplo.com
python auditor.py https://ejemplo.com --output reporte.md
python auditor.py https://ejemplo.com --timeout 45
```

El reporte se imprime en la terminal en formato Markdown y, con
`--output`, también se guarda en un archivo.
