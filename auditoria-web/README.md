# Auditor de Protección de Datos Personales (versión web)

Aplicación web (Next.js) donde cualquier persona pega la URL de un sitio y
recibe un reporte automático de indicios sobre su tratamiento de datos
personales, con referencia a la LOPDP de Ecuador. Es la versión en línea de
la herramienta de línea de comandos en `../auditoria-proteccion-datos`.

## Qué revisa

- **HTTPS y certificado TLS** (validez y vencimiento).
- **Cabeceras de seguridad**: HSTS, Content-Security-Policy,
  X-Content-Type-Options, Referrer-Policy.
- **Cookies** establecidas en la respuesta inicial del servidor: cuántas son
  de terceros y cuáles no tienen el flag `Secure`.
- **Rastreadores de terceros** conocidos (Google Analytics, Meta Pixel,
  Hotjar, etc.) presentes en el HTML.
- **Formularios** que piden datos personales (correo, teléfono, cédula...) y
  si muestran una casilla de consentimiento.
- **Política de privacidad**: si existe un enlace visible y si su texto
  menciona responsable del tratamiento, derechos ARCO, consentimiento,
  finalidad y plazo de conservación.

## Diferencia con la versión de línea de comandos

Esta versión **no ejecuta un navegador** (no hay Playwright): analiza
directamente el HTML y las cabeceras que devuelve el servidor. Esto la hace
rápida y fácil de desplegar en Vercel, pero significa que **no detecta
cookies ni rastreadores que un sitio agrega dinámicamente con JavaScript**
(por ejemplo, a través de un gestor de etiquetas). Para un análisis más
profundo de un sitio puntual, usa la versión de línea de comandos.

## Limitaciones

Es un apoyo técnico automatizado, **no un dictamen legal**. No verifica
obligaciones que no son visibles desde el sitio público (contratos con
encargados del tratamiento, registros de actividades de tratamiento,
evaluaciones de impacto, etc.).

## Desarrollo local

```bash
npm install
npm run dev
```

Abre http://localhost:3000, pega una URL y da clic en "Auditar".

## Desplegar en Vercel (paso a paso)

1. Sube este repositorio a GitHub (ya está allí).
2. Entra a [vercel.com](https://vercel.com) e inicia sesión con tu cuenta de
   GitHub.
3. Haz clic en **Add New → Project**.
4. Elige el repositorio `sarimariduena/sarimariduena`.
5. En **Root Directory**, selecciona la carpeta `auditoria-web` (importante:
   el proyecto de Next.js vive en esa subcarpeta, no en la raíz del repo).
6. Deja el resto de opciones por defecto (Vercel detecta Next.js
   automáticamente) y haz clic en **Deploy**.
7. En un par de minutos tendrás una URL pública tipo
   `https://auditoria-web-tuusuario.vercel.app` lista para compartir.

No se necesita ninguna variable de entorno ni base de datos.
