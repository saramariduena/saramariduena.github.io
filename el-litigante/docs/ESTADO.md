# Estado del proyecto (honesto)

El prompt original describe un juego AAA completo. Esta versión entrega un **cimiento jugable, verificado y profesional**, con la arquitectura dirigida por datos resuelta. Aquí está, sin adornos, lo hecho y lo pendiente.

## ✅ Implementado y verificado
- Motor de plataformas (Phaser 3 + TS): caminar, correr, saltar, doble salto, caída al vacío.
- Enemigos con 3 comportamientos (patrulla, saltador, perseguidor) + jefes con barra de vida.
- Coleccionables (LEX, expedientes), peligros, meta, vidas, escudos, daño con invulnerabilidad.
- **Contenido en JSON**: 15 mundos, lecciones COGEP, 12 tipos de enemigo, 7 habilidades, 4 dificultades, **155 logros**, NPCs.
- Mundo 1 a mano (4 niveles + jefe). Mundos 2–15 con generación procedural determinista.
- Sistema educativo "¿Qué aprendiste?" + trivia con recompensas.
- RPG: LEX, XP, nivel de personaje, árbol de habilidades comprable.
- Guardado en localStorage, múltiples perfiles, autoguardado, estadísticas, ranking local.
- Menús completos: principal, dificultad, mapa de mundos, configuración, logros (paginados), perfil.
- "Salir del juego" con confirmación. Pausa. Game over con reintento.
- Accesibilidad: tema claro/oscuro, escala de fuente, modo daltónico.
- Entrada por teclado, táctil (joystick + botones) y gamepad. Responsive (Scale.FIT).
- Assets generados por código (sin recursos con derechos de autor).
- Build de producción y despliegue Vercel listos. Probado en navegador (Chromium) sin errores.

## 🟡 Parcial / simplificado
- **Niveles 2–15**: jugables vía generación procedural, no diseñados nivel por nivel a mano.
- **Lecciones**: una por mundo (más detalladas en Mundo 1). Falta granularidad por nivel en mundos 2–15.
- **Modo daltónico**: ajusta la paleta de acentos; no recolorea cada sprite.
- **Habilidad "memoria/triviaTime"**: definida en datos; el temporizador de trivia aún no se aplica.

## ⛔ No incluido todavía (trabajo futuro claro)
- **Audio** (música y efectos): hay toggles, faltan pistas. Ver `EXPANSIONES.md`.
- **Backend** (Express + PostgreSQL) y ranking global: la persistencia está desacoplada y lista para migrar.
- **Empaquetado nativo** Windows/macOS/Linux (Electron/Tauri) y Android/iOS (Capacitor): el juego es web y se envuelve fácilmente.
- **Narración por voz, certificados PDF, misiones secundarias con diálogos ramificados.**
- **Gráficos "HD" con iluminación/sombras avanzadas**: el estilo actual es vectorial limpio, no render AAA.

## Sobre el COGEP adjunto
El PDF mencionado en el encargo no estaba disponible en el entorno de desarrollo. El contenido se construyó con la estructura conocida del COGEP (R.O. 506, 2015) y **debe verificarse** contra el texto oficial vigente. Todo está en `public/data/lessons.json` para corregirlo sin tocar código.
