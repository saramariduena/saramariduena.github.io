# Arquitectura

El proyecto separa estrictamente **motor/lógica** de **contenido jurídico**. El contenido vive en JSON (`public/data`) y el motor lo consume sin conocer detalles del COGEP. Así la materia legal se actualiza sin recompilar lógica.

## Capas

```
public/data/*.json        → CONTENIDO (mundos, lecciones, enemigos, logros, habilidades…)
src/core/                 → DOMINIO puro (tipos, persistencia, RPG, logros) — sin Phaser
src/content/              → Carga de contenido (fetch de JSON)
src/game/systems/         → Sistemas de juego (assets, controles, niveles, progresión, bus)
src/game/scenes/          → Escenas Phaser (UI y gameplay)
src/game/ui/              → Widgets reutilizables de interfaz
src/config/               → Constantes y temas
src/main.ts               → Composición y arranque
```

### `src/core` (independiente del motor)
- `types.ts` — tipos del dominio (World, Lesson, SaveProfile, etc.).
- `store.ts` — repositorio de guardado en `localStorage` con perfiles, ajustes y estado activo. La clase `Store` es la **frontera de persistencia**: cambiarla por un backend (Express + PostgreSQL) no afecta al resto.
- `rpg.ts` — XP, nivel de personaje y efectos/compra de habilidades.
- `achievements.ts` — evaluación idempotente de los 155 logros contra el estado del perfil.

### `src/game/systems`
- `assets.ts` — **generación procedural** de todas las texturas (sin imágenes externas).
- `levelBuilder.ts` — `parseLayout()` (niveles a mano) y `generateLayout()` (PRNG determinista por semilla).
- `progression.ts` — qué niveles tiene un mundo, construcción del nivel y desbloqueo/avance.
- `controls.ts` — estado de entrada táctil compartido.
- `bus.ts` — `EventEmitter` que desacopla HUD ↔ nivel.

### Escenas (`src/game/scenes`)
`Preload → Menu → Difficulty → WorldSelect → Level (+ Hud) → Lesson → …`
Más `Settings`, `Achievements`, `Profile`.

- **LevelScene** es el corazón jugable: construye el mundo desde datos, física arcade, colisiones, enemigos, jefe, daño/vidas, pausa y fin de nivel.
- **HudScene** corre en paralelo: vidas, LEX, nivel, barra de jefe y controles táctiles.
- **LessonScene** muestra la enseñanza COGEP + trivia y decide el siguiente paso (`next`).

## Flujo de datos de una partida

1. `Preload` carga `public/data/*.json` → `store.init()`.
2. El jugador crea un perfil (`createProfile`) que se guarda en `localStorage`.
3. `WorldSelect` calcula desbloqueos (`isWorldUnlocked`) y el punto de entrada (`entryStep`).
4. `LevelScene` construye el nivel (`buildParsedLevel`) y al terminar actualiza el perfil, evalúa logros y persiste.
5. `LessonScene` refuerza el aprendizaje y reanuda la progresión.

## Decisiones de diseño

- **Phaser 3 + Arcade Physics**: suficiente para un plataformas 2D y excelente rendimiento en móvil/escritorio.
- **Scale.FIT + CENTER_BOTH**: responsive automático a monitor, laptop, tablet y celular.
- **Sin backend obligatorio**: el guardado local hace el juego desplegable como sitio estático (Vercel). La interfaz de `Store` permite migrar a servidor cuando se requiera ranking global o sincronización.
- **Contenido en JSON**: cumple el requisito de actualizar el COGEP sin reescribir el juego.
