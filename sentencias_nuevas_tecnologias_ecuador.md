# Sentencias de la Corte Constitucional del Ecuador sobre derecho digital

Última actualización: datos obtenidos directamente de la API real del
buscador oficial de la Corte Constitucional (`buscador.corteconstitucional.gob.ec`),
vía GitHub Actions (`buscar_sentencias_ia.py` + `.github/workflows/buscar_ia.yml`).
A diferencia de la versión anterior de este documento, esto **no** es
investigación por búsqueda web — son metadatos reales devueltos por el
propio sistema de la Corte (número, fecha, ponente, materia y resumen
oficial de cada sentencia).

**Metodología y su límite:** se buscaron los términos "protección de datos
personales", "hábeas data", "redes sociales", "internet", "telefonía móvil",
"plataforma digital", "notificación electrónica", "firma electrónica" y
"datos informáticos" en todo el histórico de la Corte (desde 2008). Esto
devolvió **502 sentencias únicas**, pero la gran mayoría son falsos
positivos: estos términos aparecen constantemente como referencias
incidentales (p. ej. "Coronavirus", "Terremoto", "Eutanasia" también hacen
match con "internet" o "redes sociales" porque esas palabras aparecen en
algún pasaje del texto, sin que el caso trate sobre eso). La tabla de abajo
es una curaduría manual de las que **sí** tratan sustantivamente sobre
derecho digital, según el resumen oficial de cada sentencia.

**Sobre IA específicamente:** buscando "inteligencia artificial",
"algoritmo", "alucinación", "chatgpt" y "sesgo algorítmico" en el mismo
histórico, solo aparecieron 8 sentencias con esos términos, y en ninguna es
el tema central (aparecen en el texto de un tratado de comercio, en
metáforas judiciales sobre "algoritmo de razonamiento", etc.). Sigue sin
existir una sentencia ecuatoriana centrada en IA. El precedente regional más
relevante sigue siendo la Sentencia T-323 de 2024 de la Corte Constitucional
de **Colombia** (uso de ChatGPT por un juez).

## Sentencias verificadas

| # | Sentencia | Fecha | Tema | Resumen |
|---|-----------|-------|------|---------|
| 1 | [785-20-JP/22](https://www.corteconstitucional.gob.ec/sentencia-785-20-jp-22/) | 19/01/2022 | Internet y redes sociales — libertad de expresión de menores | Estudiante sancionado por Instagram con memes sobre su colegio. La Corte protegió su libertad de expresión en internet y redes sociales y ordenó al MINEDUC una guía de uso responsable para NNA. |
| 2 | 2032-20-JP/25 | 09/01/2025 | Bloqueo de usuarios en redes sociales institucionales | Ciudadano bloqueado en el Facebook oficial del GAD de Lago Agrio. La Corte fijó el estándar de proporcionalidad y transparencia para restricciones en redes oficiales. |
| 3 | [77-16-IN/22](https://www.corteconstitucional.gob.ec/sentencia-77-16-in-22/) | 28/01/2022 | Interceptación de datos informáticos | Constitucionalidad aditiva/condicionada del Reglamento del Subsistema de Interceptación de Comunicaciones o Datos Informáticos de la Fiscalía. Fija el estándar: excepcionalidad, autorización judicial motivada, proporcionalidad. |
| 4 | 23-25-IN/25 | 02/04/2025 | Celulares en recintos electorales | Constitucionalidad condicionada de la prohibición del CNE de usar celulares durante la votación. |
| 5 | 27-24-JD/26 | 04/06/2026 | Hábeas data — acta de matrimonio "inexistente" | Registro Civil negó un acta pese a 50 años de documentos (algunos digitales) que reconocían el matrimonio; le cambiaron el estado civil arbitrariamente. Vulneración de datos personales e identidad. |
| 6 | 2064-14-EP/21 | 27/01/2021 | Protección de datos / hábeas data — fotos íntimas | Fotos íntimas divulgadas sin consentimiento; qué tecnología se usó para acceder/almacenarlas. 7 estándares doctrinales sobre dato personal. |
| 7 | 1868-13-EP/20 | 08/07/2020 | Hábeas data — estándar de motivación judicial | Estándar reforzado de motivación en acciones de hábeas data. |
| 8 | 1913-22-EP/26 | 26/02/2026 | Límites del hábeas data | Fija que el hábeas data (informativo y correctivo) no procede para obtener pronunciamiento sobre propiedad/titularidad de bienes ni para ciertas rectificaciones — delimita su ámbito de protección. |
| 9 | 2033-22-EP/26 | 29/01/2026 | Desnaturalización del hábeas data | El hábeas data no puede usarse para dejar sin efecto medidas cautelares de un proceso coactivo tributario. |
| 10 | 002-11-SIN-CC | 21/06/2011 | Constitucionalidad de la Ley del Sistema Nacional de Registro de Datos Públicos | Revisión de la ley que crea el sistema nacional de registro de datos públicos (base del régimen ecuatoriano de datos personales en el sector público). |
| 11 | 025-15-SEP-CC | 04/02/2015 | Hábeas data — acceso a documentos e información | Precedente sobre citación y acceso a documentos/información vía hábeas data; citado como precedente en la 27-24-JD/26. |
| 12 | [1068-19-JP/25](https://www.arcotel.gob.ec/wp-content/uploads/2025/02/sentencia_caso_1068-19-jp.pdf) | ~2025 | Telefonía móvil — datos de usuarios | OTECEL facturó sin verificar identidad; ARCOTEL debe regular verificación de datos de usuarios. |
| 13 | [106-20-IN/24](https://www.corteconstitucional.gob.ec/la-corte-constitucional-acepta-parcialmente-la-accion-de-inconstitucionalidad-en-el-caso-106-20-in/) | ~2024 | Apps de transporte (Uber, DiDi, Cabify) | Constitucionalidad condicionada de sanciones a conductores sin régimen de autorización. |
| 14 | [456-20-JP/21](https://www.corteconstitucional.gob.ec/sentencia-456-20-jp-21/) | ~2021 | Sexting en contexto educativo | Sanción desproporcionada por sexting escolar; exige justicia restaurativa. |
| 15 | [59-19-IN/24](https://www.corteconstitucional.gob.ec/inconstitucionalidad-con-efectos-diferidos-del-acuerdo-ministerial-que-aprueba-el-uso-de-la-historia-clinica-ocupacional/) | ~2024 | Historia clínica ocupacional electrónica | Inconstitucional exigirla sin consentimiento y con datos irrelevantes. |
| 16 | [2919-19-EP/21](https://www.cijc.org/es/cuadernos/Sentencias/54e7f41e-97cf-48ae-9766-6e5b99fcb6b4.pdf) | ~2021 | Hábeas data / buró de crédito | Orden de eliminar datos crediticios erróneos. |

## Pendiente de verificar con más detalle

- **17-25-TI/26 y 17-25-TI/26A** (control de constitucionalidad del Acuerdo
  Ecuador-Corea del Sur) mencionan "algoritmo" e "inteligencia artificial",
  probablemente en un capítulo de comercio digital del tratado — no
  confirmado si la Corte analiza el fondo de esas cláusulas o solo las cita.
- **3022-23-EP/26** hizo match con los 4 términos principales (hábeas data,
  internet, protección de datos, redes sociales) pero su resumen oficial es
  sobre juez competente/cosa juzgada — no está claro si el caso de origen
  era de datos personales. No se incluye hasta confirmar.

## Pistas descartadas (verificadas pero no aplicables)

- Las sentencias de **telefonía móvil** de tipo "SIN-CC" (017-16, 020-16,
  004-16, 032-16, 052-15, 007-15, 008-15) son disputas tributarias/de
  espectro radioeléctrico entre operadoras (OTECEL, CONECEL) y municipios —
  regulación de telecomunicaciones, no derechos digitales de personas.
- **67-23-IN/24** (eutanasia), **98-23-JH/23** (hábeas corpus penitenciario),
  **751-15-EP/21** y **916-22-JP/24** (discriminación por vestimenta/tatuaje)
  no son casos de tecnología digital pese a aparecer en algunas búsquedas.
- El caso de bloqueo de cuenta de un "rappitendero" y el fallo sobre
  YouTube/Google "no pueden ser jueces" citados por algunos medios son de la
  **Corte Constitucional de Colombia**, no de Ecuador.
- La filtración masiva de datos de **Novaestrat** (2019) no llegó a una
  sentencia de la Corte Constitucional.

## Temas sin sentencia ecuatoriana encontrada

Inteligencia artificial (como tema central), criptomonedas/blockchain,
drones, reconocimiento facial/biometría como eje central, videovigilancia en
espacio público, voto electrónico, neutralidad de red, propiedad intelectual
en entornos digitales, derecho al olvido (hay un caso **389-24-EP** admitido
sobre esto, pero sin sentencia final confirmada).
