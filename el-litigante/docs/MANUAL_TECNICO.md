# Manual Técnico

## Requisitos
- Node.js 18 o superior.
- npm 9+.

## Instalación y scripts
```bash
npm install        # instala dependencias
npm run dev        # desarrollo con HMR (http://localhost:5173)
npm run typecheck  # comprobación de tipos (tsc --noEmit)
npm run build      # typecheck + build de producción -> dist/
npm run preview    # sirve dist/ localmente
```

## Estructura del repositorio
```
el-litigante/
├─ index.html              # punto de entrada
├─ vercel.json             # configuración de despliegue
├─ vite.config.ts          # bundler (base relativa, chunk de Phaser)
├─ tsconfig.json
├─ public/data/*.json      # CONTENIDO editable (COGEP, mundos, logros…)
├─ src/                    # código fuente (ver docs/ARQUITECTURA.md)
└─ docs/                   # documentación
```

## Despliegue

### Vercel (recomendado)
- `vercel.json` ya define `buildCommand`, `outputDirectory` y framework Vite.
- Si el repo contiene varios proyectos, fija **Root Directory = `el-litigante`** en la configuración del proyecto en Vercel.

### Estático genérico
Cualquier hosting que sirva archivos: sube el contenido de `dist/`. La `base` es relativa (`./`), por lo que funciona en subcarpetas (p. ej. GitHub Pages).

## Rendimiento
- Phaser se separa en su propio chunk (`vite.config.ts`) para cachearlo.
- Texturas generadas en runtime (sin descargas de assets).
- `Scale.FIT` mantiene 60 FPS en la mayoría de dispositivos.

## Persistencia
`localStorage` con claves `el_litigante_*`. Para migrar a un backend:
1. Implementa una clase con la misma API pública que `Store` (`src/core/store.ts`).
2. Sustituye lectura/escritura local por llamadas HTTP (Express + PostgreSQL).
3. El resto del juego no cambia: solo consume `store`.

## Pruebas manuales
Flujo mínimo de verificación: Menú → Nueva partida → elegir dificultad → Seleccionar mundo → jugar Mundo 1 Nivel 1 → llegar a la meta → ver lección y trivia → continuar.

## Resolución de problemas
- **Pantalla en negro / "Error al cargar contenido"**: revisa que `public/data/*.json` exista y sea JSON válido.
- **No se ven controles táctiles en escritorio**: es intencional (aparecen tenues); se activan plenos en pantallas pequeñas o táctiles.
