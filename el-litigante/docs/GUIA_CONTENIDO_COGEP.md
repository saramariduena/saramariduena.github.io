# Guía de Contenido COGEP

Esta guía explica cómo crear y actualizar el contenido jurídico **sin programar**. Todo vive en `public/data/`.

> **Importante:** verifica siempre los artículos contra el texto oficial **vigente** del COGEP (incluidas reformas). Este juego es material de apoyo, no fuente normativa.

## Editar una lección (`lessons.json`)

Cada lección es un objeto con esta forma:

```json
"prueba": {
  "titulo": "La prueba",
  "explicacion": "Texto pedagógico, sencillo.",
  "articulo": "COGEP Arts. 158 y siguientes",
  "resumen": "Idea central en una línea.",
  "ejemplo": "Caso práctico breve.",
  "consejo": "Recomendación profesional.",
  "trivia": {
    "pregunta": "¿…?",
    "opciones": ["A", "B", "C", "D"],
    "correcta": 1
  }
}
```

- `correcta` es el **índice** (empezando en 0) de la opción correcta.
- La clave del objeto (`"prueba"`) es el `lessonId` que referencian los niveles/jefes.
- Tras una reforma, basta con corregir el texto y `articulo`, y volver a desplegar.

## Asociar lecciones a mundos/niveles (`worlds.json`)

- Cada mundo tiene `lessonId` (lección principal) y un `boss.lessonId`.
- En el **Mundo 1** (hecho a mano) cada nivel tiene su propio `lessonId` y un `layout` (mapa de texto).
- En los mundos con `generator`, todos los niveles usan el `lessonId` del mundo (puedes refinarlo convirtiéndolos en niveles a mano, ver `EXPANSIONES.md`).

### Leyenda de los `layout` (niveles a mano)
```
#  suelo sólido        =  plataforma flotante
c  moneda LEX          d  expediente (documento)
e  enemigo             ^  peligro (pinchos)
P  inicio del jugador  F  meta (bandera)
(espacio) vacío
```
Cada carácter es una celda de 64×64 px. Las filas pueden tener distinta longitud (se rellenan a la derecha).

## Buenas prácticas pedagógicas
- Explica **antes** de citar el artículo: primero la idea, luego la norma.
- Una trivia por lección, con una sola respuesta correcta y distractores plausibles.
- Mantén el `consejo` en clave de práctica profesional.
- Evita copiar literalmente la ley: parafrasea y ejemplifica.
