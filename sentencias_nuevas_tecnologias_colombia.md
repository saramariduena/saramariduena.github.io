# Sentencias de la Corte Constitucional de Colombia sobre derecho digital

Última actualización: datos obtenidos directamente del buscador oficial de
Relatoría de la Corte Constitucional de Colombia
(`corteconstitucional.gov.co/relatoria/buscador_new/`), vía GitHub Actions
(`buscar_sentencias_ia_colombia.py` + `.github/workflows/buscar_ia_colombia.yml`).
Igual que la versión de Ecuador, esto **no** es investigación por búsqueda
web — son coincidencias reales devueltas por el propio buscador de la
Corte, buscando por texto completo de la providencia.

## Metodología y su límite

El buscador de Relatoría no expone una API JSON documentada como el de
Ecuador: es una página server-side (PHP) que renderiza los resultados en
el HTML de respuesta. Encontrar el endpoint y los parámetros reales
(`searchOption=texto`, `fini`, `ffin`, `verform`, `maxprov`, `buscar_por`,
`accion=search`, `OrderbyOption`) tomó varias rondas de ingeniería inversa
contra el sitio real — un primer intento con nombres de parámetro tomados
de una URL de ejemplo (`finicio`, `ver_formulario`, `cant_providencias`)
devolvió sistemáticamente "sin resultados" porque esos nombres no
coinciden con los campos reales del formulario, y `searchOption` tiene
un valor específico para "número de sentencia" (`prov_sentencia`) que es
distinto del de texto completo (`texto`).

Se buscaron ~44 términos en todo el histórico de la Corte (desde 1992,
año en que entró en funciones), en tres tandas — los mismos ejes que en
la búsqueda de Ecuador, adaptados a terminología colombiana:

1. **Protección de datos y trámites electrónicos**: protección de datos
   personales, habeas data, redes sociales, internet, telefonía móvil,
   plataforma digital, notificación electrónica, firma electrónica, datos
   informáticos, derecho al olvido.
2. **Tecnologías emergentes, biometría e IA**: inteligencia artificial,
   algoritmo, chatgpt, sesgo algorítmico, biometría, reconocimiento
   facial, big data, aprendizaje automático, ciberseguridad,
   criptomoneda, blockchain, comercio electrónico, geolocalización,
   aplicación móvil, WhatsApp, videovigilancia, dron.
3. **Delitos y usos específicos de internet**: voto electrónico, internet
   de las cosas, chatbot, robot, automatización, contrato inteligente,
   streaming, cookies, ciberacoso, grooming, pornografía infantil,
   sexting, nombre de dominio, apuestas en línea, influencer, publicidad
   digital, delito informático, suplantación de identidad, phishing,
   estafa electrónica, vigilancia digital, huella digital, correo
   electrónico, mensajería instantánea.

Esto devolvió **989 sentencias únicas** en total (deduplicadas por número,
con hasta 500 resultados por término). Igual que en Ecuador, la gran
mayoría son falsos positivos: términos de uso cotidiano en cualquier
proceso judicial hacen match masivamente sin que el caso trate sobre
derecho digital. Los términos con más coincidencias fueron:

| Término | Sentencias encontradas |
|---|---|
| habeas data | 250 |
| redes sociales | 196 |
| internet | 195 |
| whatsapp | 179 |
| correo electrónico | 140 |
| protección de datos personales | 131 |
| telefonía móvil | 100 |
| plataforma digital | 78 |
| pornografía infantil | 75 |
| derecho al olvido | 53 |
| suplantación de identidad | 32 |

"WhatsApp", por ejemplo, aparece en 179 sentencias distintas simplemente
porque es el medio por el que se notifican o prueban hechos en procesos
de todo tipo (tutelas por salud, laborales, de familia), no porque el
caso trate sobre derecho digital. Verificar individualmente las ~989
coincidencias — o incluso las ~226 encontradas por al menos un término
específico (no genérico) — habría requerido leer cada providencia
completa, lo cual excede el alcance razonable de esta corrida. Por eso,
igual que en el documento de Ecuador, la tabla de abajo es una curaduría
manual **verificada externamente** (no una lista exhaustiva de matches),
y el resto de las coincidencias queda documentado como pendiente de
verificar, sin afirmar que traten de derecho digital.

**Sobre IA específicamente:** los términos de IA fueron mucho menos
ruidosos que los genéricos — "inteligencia artificial" encontró 12
sentencias, "algoritmo" 17, "chatgpt", "sesgo algorítmico" y "aprendizaje
automático" solo 1 cada uno, "chatbot" y "robot" 2 cada uno. A diferencia
de Ecuador (donde no existe todavía una sentencia centrada en IA), Colombia
**sí tiene** un precedente central sobre IA: la Sentencia T-323 de 2024
(uso de ChatGPT por un juez), que ya era, de hecho, la referencia regional
citada en el documento de Ecuador antes de esta búsqueda.

## Sentencias verificadas

| # | Sentencia | Año | Tema | Resumen |
|---|-----------|-----|------|---------|
| 1 | [T-323 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-323-24.htm) | 2024 | Inteligencia artificial en la administración de justicia | Un juez de segunda instancia usó ChatGPT para fundamentar una decisión sobre exoneración de copagos médicos de un niño con TEA. La Corte no prohibió el uso de IA generativa en la redacción de decisiones judiciales, pero advirtió sobre riesgos de alucinaciones y sesgos discriminatorios, y ordenó al Consejo Superior de la Judicatura divulgar en 4 meses una guía sobre el uso de IA generativa (particularmente ChatGPT) en la Rama Judicial. Es el precedente central de la región sobre IA y justicia. |
| 2 | [T-277 de 2015](https://www.corteconstitucional.gov.co/relatoria/2015/T-277-15.htm) | 2015 | Derecho al olvido en internet | Primer pronunciamiento de la Corte sobre el derecho al olvido en internet (ponente María Victoria Calle Correa). Ordenó al diario El Tiempo bloquear el acceso de buscadores a un artículo antiguo que vinculaba a una persona con un delito ya prescrito. Fijó el estándar: sitios de internet y buscadores pueden ser responsables del tratamiento de datos personales y sujetos al habeas data, pero las bases de datos periodísticas quedan excluidas y se rigen por libertad de expresión; el derecho al olvido aplica a casos penales, no a figuras públicas. |
| 3 | [T-453 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-453-24.htm) | 2024 | Debido proceso en plataformas digitales — bloqueo de cuenta | TikTok bloqueó la cuenta de un influencer/abogado mayor de edad alegando que tenía menos de 13 años; pese a que el usuario envió su cédula para corregir el error, la plataforma mantuvo el bloqueo. La Corte concedió el amparo (debido proceso, habeas data, derechos laborales) y ordenó a TikTok restablecer o corregir los datos del usuario. |
| 4 | [T-176 de 2026](https://www.corteconstitucional.gov.co/relatoria/2026/T-176-26.htm) | 2026 | Moderación de contenido y debido proceso en redes sociales | Suspensión de las cuentas de Facebook, Instagram y WhatsApp de un usuario colombiano. La Corte concluyó que, si bien las plataformas tienen el deber de combatir contenido ilícito (en particular de explotación sexual infantil), también están obligadas a garantizar garantías mínimas de debido proceso al tomar esas decisiones. |
| 5 | [T-360 de 2022](https://www.corteconstitucional.gov.co/relatoria/2022/T-360-22.htm) | 2022 | Habeas data — suplantación de identidad y fraude crediticio | Banco Davivienda reportó al accionante en centrales de riesgo (Datacrédito) por obligaciones crediticias que nunca adquirió, obtenidas mediante suplantación de identidad. La Sala Sexta de Revisión resolvió sobre la protección del habeas data financiero frente al reporte negativo originado en fraude de identidad. |

## Pendiente de verificar con más detalle

Sentencias encontradas por al menos un término **específico** de IA o
tecnologías emergentes (no genérico), pero cuyo contenido no se pudo
confirmar externamente en esta corrida — no se incluyen en la tabla
anterior hasta verificar que el caso trata sustantivamente sobre el tema,
y no es una mención incidental:

- **T-190 de 2024** (algoritmo, ciberacoso, inteligencia artificial,
  pornografía infantil) — tutela de protección de NNA contra un medio
  digital (Fucks News S.A.S.) con MinTIC e ICBF vinculados; no se pudo
  confirmar si el algoritmo/IA es el tema central o incidental.
- **T-256 de 2025**, **T-450 de 2025**, **T-475 de 2024**, **T-186 de
  2026**, **T-249 de 2024**, **T-457 de 2025** — todas con match en
  "inteligencia artificial" y/o "algoritmo"/"chatbot", sin verificación
  externa disponible.
- **T-760 de 2008** — sentencia histórica y extensa sobre el sistema de
  salud (unificación de POS); hizo match con "inteligencia artificial" y
  "algoritmo", casi con certeza de forma incidental dado el tamaño y
  alcance del fallo.
- **T-234 de 2024**, **T-304 de 2023** — "internet de las cosas"; sin
  verificar.
- **T-453 de 2024** — confirmada arriba, pero su conexión específica con
  "sesgo algorítmico" (el término que la encontró) no se pudo verificar
  con precisión; se incluyó por el caso TikTok en sí (debido proceso
  digital), no por sesgo algorítmico.

## Pistas descartadas (verificadas pero no aplicables)

- **T-500 de 2011** — hizo match con "apuestas en línea", pero es un
  falso positivo: "Apuestas en Línea S.A." es el nombre propio de la
  empresa concesionaria del juego de Chance en Bogotá/Cundinamarca: el
  caso trata sobre un contrato de concesión, no sobre regulación de
  apuestas/juego en internet.

## Temas sin sentencia colombiana encontrada con estos términos

**Blockchain**, **voto electrónico**, **contrato inteligente** y
**alucinación** (como término aislado) no aparecieron en ninguna de las
989 sentencias encontradas por los ~44 términos buscados — no significa
que no exista jurisprudencia sobre esos temas, solo que no hizo match con
la terminología exacta probada en esta corrida.

## Nota metodológica final

A diferencia del documento de Ecuador (que usa la API JSON real y
devuelve metadatos estructurados — ponente, resumen oficial, fecha exacta
de decisión), el buscador de Colombia solo permite extraer con
confiabilidad el **número de sentencia** desde el HTML de resultados; no
se intentó extraer fecha de decisión exacta, ponente ni resumen oficial
por sentencia en esta corrida (el año se infiere del propio número de
sentencia, p. ej. "24" en T-323-24 → 2024). Una futura iteración podría
usar la ficha individual de cada sentencia
(`/relatoria/<año>/<TIPO>-<num>-<yy>.htm`) para extraer esos metadatos.
