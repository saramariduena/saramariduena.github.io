# Sentencias de la Corte Constitucional del Ecuador sobre derecho digital

Última actualización: datos obtenidos directamente de la API real del
buscador oficial de la Corte Constitucional (`buscador.corteconstitucional.gob.ec`),
vía GitHub Actions (`buscar_sentencias_ia.py` + `.github/workflows/buscar_ia.yml`).
A diferencia de la versión anterior de este documento, esto **no** es
investigación por búsqueda web — son metadatos reales devueltos por el
propio sistema de la Corte (número, fecha, ponente, materia y resumen
oficial de cada sentencia).

**Metodología y su límite:** se buscaron ~35 términos en todo el histórico
de la Corte (desde 2008), en tres tandas: (1) protección de datos
personales, hábeas data, redes sociales, internet, telefonía móvil,
plataforma digital, notificación electrónica, firma electrónica, datos
informáticos; (2) biometría, reconocimiento facial, big data, aprendizaje
automático, ciberseguridad, criptomoneda, blockchain, comercio electrónico,
geolocalización, derecho al olvido, SATJE, aplicación móvil, WhatsApp,
videovigilancia, dron; (3) voto electrónico, software, internet de las
cosas, chatbot, robot, automatización, contrato inteligente, streaming,
cookies, ciberacoso, grooming, pornografía infantil, nombre de dominio,
domicilio electrónico, apuestas en línea, influencer, publicidad digital,
código fuente, delito informático, suplantación de identidad, phishing,
estafa electrónica, vigilancia digital, datos biométricos, huella digital,
correo electrónico, mensajería instantánea. Esto devolvió más de 1500
resultados en total (muchos duplicados entre términos), pero la gran
mayoría son falsos positivos: estos términos aparecen constantemente como
referencias incidentales (p. ej. "Coronavirus", "Terremoto", "Eutanasia",
"prisión preventiva", "Estado de Excepción" también hacen match con
"internet", "redes sociales", "vigilancia digital" o "huella digital"
porque esas palabras aparecen en algún pasaje del texto, sin que el caso
trate sobre eso). La tabla de abajo es una curaduría manual de las que
**sí** tratan sustantivamente sobre derecho digital, según el resumen
oficial de cada sentencia o verificación externa.

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
| 17 | 47-19-JD/22 | 21/12/2022 | Hábeas data — confidencialidad en denuncias disciplinarias | La persona denunciada en un proceso disciplinario **no puede** usar hábeas data para obtener los datos del denunciante (no son sus datos personales), pero **sí puede** acceder a su propia información dentro del expediente. |
| 18 | 29-21-JI/21 | 01/12/2021 | Acceso a información pública — datos de vacunación COVID | La Defensoría del Pueblo pidió al Ministerio de Salud el listado de personas vacunadas (fase 0) y el Ministerio se negó. La Corte, con test de proporcionalidad, determinó que entregar esos datos **no vulnera la privacidad** de los vacunados y que negarlos sí vulneró el acceso a la información pública. Ordenó entregar la data (sin cédulas). |
| 19 | 17-25-TI/26 y 17-25-TI/26A | 22/01/2026 y 19/03/2026 | Tratado internacional Ecuador-Corea del Sur (SECA) — comercio electrónico y cooperación tecnológica | El SECA es el tratado más completo firmado por Ecuador (23 capítulos: bienes, servicios, telecomunicaciones, **comercio electrónico**, propiedad intelectual, y cooperación tecnológica citando a Corea como potencia en microchips, IA y ciberseguridad — de ahí que "algoritmo" e "inteligencia artificial" aparezcan en el texto). La Corte: (1º momento) determinó que requería aprobación de la Asamblea; (2º momento) declaró constitucional todo el contenido. **Importante:** es un control de constitucionalidad integral/formal del tratado — no hay evidencia de que la Corte haya analizado a fondo, de forma separada, las cláusulas de IA o comercio digital en particular. |
| 20 | 0006-17-IN (numerado "6-17-IN/25" en el buscador) | 04/12/2025 | Datos biométricos — sistema de identidad y registro civil | Acción pública de inconstitucionalidad presentada el 20/01/2017 por la Clínica Jurídica de la USFQ (Farith Simon, Daniela Salazar, Hugo Cahueñas, junto con Roberto Eguiguren e Isabel Samaniego) contra los artículos 37, 46, 47, 54, 79 y 94 de la Ley Orgánica de Gestión de la Identidad y Datos Civiles (LOGIDAC) — la ley que regula la captura biométrica de la ciudadanía para la cédula y el registro civil. Resuelta 8 años después. **No pude confirmar el sentido final del fallo** (aceptada/negada/parcial) con fuentes públicas — se incluye por ser un caso real y sustantivo sobre datos biométricos estatales, pendiente de verificar el resultado exacto. |
| 21 | 2172-21-EP/25 | 05/06/2025 | Desnaturalización del hábeas data — reembolso económico | A una clienta del Banco Pichincha le debitaban USD 3.71 mensuales de su cuenta de ahorros a favor de NovaEcuador sin su autorización. Los jueces de instancia usaron el hábeas data para ordenar reparación económica por el uso no autorizado de su información. La Corte declaró que eso **desnaturaliza el hábeas data**: la garantía no procede para exigir reembolsos económicos ni resolver conflictos contractuales — la reparación debe limitarse a la vulneración del dato personal en sí. Declaró vulnerado el derecho a la seguridad jurídica del banco. Se suma a las filas 8 y 9 en la misma línea jurisprudencial de delimitar el ámbito del hábeas data. |

## Pendiente de verificar con más detalle

- **3022-23-EP/26** hizo match con los 4 términos principales (hábeas data,
  internet, protección de datos, redes sociales) pero su resumen oficial es
  sobre juez competente/cosa juzgada — no está claro si el caso de origen
  era de datos personales. No se incluye hasta confirmar.
- El sentido exacto del fallo de **0006-17-IN** (fila 20 de la tabla) — se
  confirmó de qué trata (biometría del registro civil/cédula) pero no qué
  resolvió la Corte.
- Varias sentencias de tipo **"EE" (Estado de Excepción)** — 9-25-EE/25,
  3-25-EE/25, 1-26-EE/26 — hicieron match con "reconocimiento facial" o
  "vigilancia digital". Es plausible que algunos decretos de excepción
  autoricen tecnología de vigilancia/reconocimiento facial para fuerzas de
  seguridad, pero no confirmé el contenido específico de ninguno (uno de
  ellos, 1-26-EE/26, resultó ser sobre conmoción interna/crimen organizado
  sin relación con vigilancia digital). No se incluyen hasta confirmar.

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
- **52-25-IN/25** — confirmado: es la sentencia sobre la Ley Orgánica de
  Integridad Pública (declarada inconstitucional por vicios de forma,
  septiembre 2025). Solo apareció por match difuso con "biometría/comercio
  electrónico/IA"; no tiene relación con derecho digital.
- **1-24-CP/24** — dictamen sobre las 11 preguntas de consulta popular de
  Noboa (2024); la pregunta que hizo match con "apuestas en línea" trata
  sobre regular casinos y casas de apuestas **físicas**, no apuestas en
  línea.
- Los términos "delito informático" (61 resultados), "vigilancia digital"
  (37), "huella digital" (18) y "correo electrónico" (1922, ruido casi
  puro) resultaron ser mayoritariamente acciones extraordinarias de
  protección sobre debido proceso penal donde esos términos aparecen de
  forma incidental (tipificación de un delito entre varios, "huella" como
  evidencia física, motivación judicial, etc.), no casos centrados en
  derecho digital. Ejemplos verificados como falsos positivos: 95-18-EP/24
  (identidad de género en educación), 360-19-JH/25 (prisión preventiva),
  96-21-JP/25 (violencia obstétrica), 4642-22-JP/25 (derecho al agua).
- Se probó la terminología específica de la Ley Orgánica de Protección de
  Datos Personales (LOPDP, 2021): "Superintendencia de Protección de Datos
  Personales", "tratamiento de datos personales", "responsable del
  tratamiento", "elaboración de perfiles", "transferencia internacional de
  datos", "consentimiento del titular", "decisiones automatizadas". Casi
  todo resultó ruido: "ADN" y "prueba genética" son en su enorme mayoría
  juicios de paternidad/filiación (nada que ver con protección de datos);
  "Superintendencia de Protección de Datos Personales" aparece incluso en
  sentencias de 2009-2018, años antes de que esa entidad existiera —
  confirma que es coincidencia de palabras sueltas, no de la frase. La
  única sentencia real que salió de esta tanda fue la 2172-21-EP/25 (fila
  21 de la tabla).

## Temas sin sentencia ecuatoriana encontrada

Inteligencia artificial (como tema central), criptomonedas/blockchain,
drones, reconocimiento facial/biometría como eje central, videovigilancia en
espacio público, voto electrónico, neutralidad de red, propiedad intelectual
en entornos digitales, derecho al olvido (hay un caso **389-24-EP** admitido
sobre esto, pero sin sentencia final confirmada).

**Nota sobre la Ley Orgánica de Inteligencia (2025):** hay una demanda de
inconstitucionalidad muy relevante para vigilancia digital — el caso
**86-25-IN**, con medidas cautelares ya concedidas por la Corte suspendiendo
artículos que permitían a agentes de inteligencia operar con identidades
falsas, usar técnicas de vigilancia en el ciberespacio y pedir datos a
telefónicas sin control judicial suficiente (con amicus curiae de EFF y
Fundación Karisma). No apareció en ninguna de las búsquedas del scraper
(no hizo match con ninguno de los ~35 términos probados) y aún no tiene
sentencia final — solo medidas cautelares. Vale la pena buscarlo
directamente por número de causa en una futura corrida.
