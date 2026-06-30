# ⚖️ EL LITIGANTE

**Videojuego educativo de plataformas para aprender el Código Orgánico General de Procesos (COGEP) del Ecuador.**

Encarna a *El Litigante*, un joven abogado que debe convertirse en el mejor del país superando 15 mundos inspirados en las instituciones del proceso civil ecuatoriano: principios, competencia, demanda, citación, prueba, audiencias, procedimientos, ejecución, recursos y medidas cautelares.

> **Aviso académico:** el contenido es **educativo** y **no sustituye** el estudio del texto oficial del COGEP. Los artículos citados deben verificarse contra la versión vigente (incluidas sus reformas). Todo el contenido jurídico está en archivos de datos editables (ver más abajo) para mantenerlo alineado con la normativa.

---

## 🎮 Qué incluye esta versión

- **Motor de plataformas** en Phaser 3 + TypeScript: caminar, correr, saltar y **doble salto**, enemigos con IA (patrulla, saltador, perseguidor), coleccionables, peligros y meta.
- **Arquitectura 100% dirigida por datos**: mundos, niveles, lecciones, enemigos, habilidades, dificultades y logros viven en `public/data/*.json`. Añadir contenido = editar JSON, sin tocar el motor.
- **Mundo 1 hecho a mano** (4 niveles + jefe) y **Mundos 2–15 con generación procedural determinista** a partir de parámetros en datos.
- **Sistema educativo "¿Qué aprendiste?"**: tras cada nivel y jefe aparece una lección estructurada (explicación, artículo, resumen, ejemplo, consejo) + **trivia**.
- **RPG**: monedas **LEX**, experiencia, nivel de personaje y **árbol de 7 habilidades**.
- **Guardado** con múltiples perfiles (localStorage), autoguardado y estadísticas.
- **+155 logros**, ranking local y pantalla de perfil.
- **Mentor Doctor Iuris**, 4 modos de dificultad (Estudiante / Abogado / Experto / Magistrado).
- **Accesibilidad**: tema claro/oscuro, escala de fuente, modo daltónico (paleta Okabe-Ito).
- **Controles**: teclado, **táctil** (joystick + botones) y **gamepad**. Responsive a cualquier pantalla (Phaser Scale.FIT).
- **Assets generados por código** (sin recursos con derechos de autor).

> Lee `docs/ESTADO.md` para saber con honestidad qué está terminado y qué queda como trabajo futuro respecto al prompt original (backend, audio, empaquetado nativo, etc.).

---

## 🚀 Cómo ejecutarlo

Requiere Node.js 18+.

```bash
npm install
npm run dev      # servidor de desarrollo (http://localhost:5173)
npm run build    # build de producción -> carpeta dist/
npm run preview  # sirve el build de producción
```

## ☁️ Despliegue en Vercel

El proyecto está listo para Vercel (incluye `vercel.json`):

1. Sube el repositorio a GitHub.
2. En Vercel: **Add New Project → Import** el repo.
3. Define el **Root Directory** como `el-litigante`.
4. Vercel detecta Vite automáticamente. Build: `npm run build`, Output: `dist`.
5. Deploy. ¡Listo!

Funciona también en Netlify, GitHub Pages o cualquier hosting estático (la salida es `dist/`).

---

## 🧩 Actualizar el contenido jurídico (sin programar)

Toda la materia del COGEP vive en `public/data/`:

| Archivo | Contenido |
|---|---|
| `worlds.json` | Los 15 mundos, sus paletas, jefes y niveles/parámetros |
| `lessons.json` | Lecciones pedagógicas (título, explicación, artículo, resumen, ejemplo, consejo, trivia) |
| `enemies.json` | Errores procesales (enemigos) y su comportamiento |
| `skills.json` | Árbol de habilidades |
| `difficulties.json` | Modos de dificultad |
| `achievements.json` | Logros |
| `npcs.json` | Personajes no jugables y sus diálogos |

Para corregir un artículo tras una reforma, edita el texto en `lessons.json` y vuelve a desplegar. **No se toca código.** Ver `docs/GUIA_CONTENIDO_COGEP.md`.

---

## 📚 Documentación

- `docs/ARQUITECTURA.md` — diseño técnico y estructura del código.
- `docs/MANUAL_JUGADOR.md` — cómo jugar.
- `docs/MANUAL_TECNICO.md` — instalación, build, despliegue y mantenimiento.
- `docs/GUIA_CONTENIDO_COGEP.md` — cómo crear/editar lecciones y mundos.
- `docs/EXPANSIONES.md` — cómo añadir nuevos mundos, niveles, enemigos y mecánicas.
- `docs/ESTADO.md` — estado real frente al prompt original (qué falta).

## Licencia

MIT. Contenido educativo basado en el COGEP del Ecuador.
