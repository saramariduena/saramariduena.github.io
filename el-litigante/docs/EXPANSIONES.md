# Guía de Expansión

Cómo crecer el juego. Casi todo es **datos**; el código solo cambia para mecánicas nuevas.

## Añadir un mundo
En `worlds.json` agrega un objeto con `id`, `order`, `title`, `palette`, `boss` y **o bien** `levels` (a mano) **o** `generator` (procedural). Súbele el `order` para que aparezca al final del mapa.

## Convertir un mundo procedural en niveles a mano
Sustituye `generator` por `levels: [...]`, cada uno con `id`, `title`, `lessonId` y `layout` (ver leyenda en `GUIA_CONTENIDO_COGEP.md`). El desbloqueo y la progresión funcionan igual.

## Añadir un enemigo (error procesal)
En `enemies.json`:
```json
{ "id": "nuevo", "name": "Nombre", "color": "#aa3333", "behavior": "patrol", "speed": 70 }
```
`behavior` admite `patrol`, `jumper` o `chaser` (ya implementados). Para un comportamiento nuevo, añade un caso en `LevelScene.updateEnemies()`.

## Añadir una habilidad
En `skills.json` define `id`, `name`, `desc`, `maxLevel`, `cost`, `effect`, `perLevel`. Si el `effect` es nuevo, conéctalo donde corresponda (p. ej. en `LevelScene` vía `skillEffect(profile, content, 'tuEfecto')`).

## Añadir logros
En `achievements.json` añade `{ id, name, desc, condition: { type, value } }`. Los `type` soportados están en `src/core/achievements.ts` (`levels`, `lex`, `enemies`, `worldComplete`, `bossDefeat`, etc.). Para una condición nueva, añade un `case` en `isMet()`.

## Audio (trabajo futuro)
Coloca pistas en `public/audio/` y cárgalas en `PreloadScene` con `this.load.audio(...)`. Respeta los toggles `settings.music` / `settings.sfx`.

## Empaquetado nativo (trabajo futuro)
Al ser web, se puede envolver con:
- **Capacitor** (Android / iOS): `npx cap add android ios`, `webDir: 'dist'`.
- **Electron / Tauri** (Windows / macOS / Linux).
Ver `docs/ESTADO.md`.

## Backend opcional
Implementa la API de `Store` contra Express + PostgreSQL para ranking global y sincronización entre dispositivos. El juego ya está desacoplado de la persistencia.
