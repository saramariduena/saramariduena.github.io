# Sentencias de la Corte Constitucional de Colombia sobre derecho digital

Última actualización: datos obtenidos directamente del buscador oficial de
Relatoría de la Corte Constitucional de Colombia
(`corteconstitucional.gov.co/relatoria/buscador_new/`), vía GitHub Actions
(`buscar_sentencias_ia_colombia.py` + `.github/workflows/buscar_ia_colombia.yml`),
más una segunda ronda de verificación puntual por búsqueda externa sobre
las coincidencias que el buscador oficial sí encontró pero que no se
habían revisado, después de que se detectara que **T-184 de 2026**
(un caso real de violencia digital) se había quedado fuera de la primera
versión de este documento por no revisarse individualmente.

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

**Primera corrida — ~44 términos** en todo el histórico de la Corte
(desde 1992), en tres tandas, los mismos ejes que en la búsqueda de
Ecuador adaptados a terminología colombiana: protección de datos y
trámites electrónicos (protección de datos personales, habeas data,
redes sociales, internet, telefonía móvil, plataforma digital,
notificación electrónica, firma electrónica, datos informáticos, derecho
al olvido); tecnologías emergentes, biometría e IA (inteligencia
artificial, algoritmo, chatgpt, sesgo algorítmico, biometría,
reconocimiento facial, big data, aprendizaje automático, ciberseguridad,
criptomoneda, blockchain, comercio electrónico, geolocalización,
aplicación móvil, WhatsApp, videovigilancia, dron); delitos y usos
específicos de internet (voto electrónico, internet de las cosas,
chatbot, robot, automatización, contrato inteligente, streaming, cookies,
ciberacoso, grooming, pornografía infantil, sexting, nombre de dominio,
apuestas en línea, influencer, publicidad digital, delito informático,
suplantación de identidad, phishing, estafa electrónica, vigilancia
digital, huella digital, correo electrónico, mensajería instantánea).
Esto devolvió **989 sentencias únicas**.

**Segunda corrida — 11 términos adicionales**, agregados tras notar (por
verificación externa) que dos sentencias muy relevantes —**T-067 de
2025** (transparencia algorítmica) y **C-212 de 2026** (agravante penal
por IA)— no aparecían en la primera corrida: transparencia algorítmica,
código fuente, falsedad personal, deepfake, decisiones automatizadas,
perfilamiento, ultrafalsificación, neutralidad de red, propiedad
intelectual digital, minería de datos, IA generativa. Esta corrida reveló
un límite adicional del buscador: varios de estos términos (sobre todo
"neutralidad de red") devolvieron coincidencias con sentencias que, tras
verificar, **no tratan de neutralidad de red** — el buscador parece
indexar por palabras sueltas más que por frase exacta, así que "red" (de
"neutralidad de **red**") hace match con textos que mencionan "red**es**
sociales" u otras "redes". Además, ni siquiera con estos términos
adicionales aparecieron T-067/25 ni C-212/26 — probablemente porque el
buscador es sensible a tildes ("algorítmica" ≠ "algoritmica") o porque
esas sentencias usan otro vocabulario ("falsedad personal" es, de hecho,
el nombre legal del delito de suplantación de identidad en el Código
Penal colombiano, lo cual sí permitió encontrar varias sentencias nuevas
sobre ese eje). Ambas sentencias se incluyen igual en la tabla de abajo,
verificadas por fuera del buscador oficial.

Igual que en Ecuador, la gran mayoría de las 989 coincidencias son falsos
positivos: términos de uso cotidiano en cualquier proceso judicial hacen
match masivamente sin que el caso trate sobre derecho digital. Los
términos con más coincidencias en la primera corrida fueron:

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
coincidencias de la primera corrida — o incluso las ~226 encontradas por
al menos un término específico (no genérico) — habría requerido leer
cada providencia completa, lo cual excede el alcance razonable de una
sola corrida. Por eso este documento combina (a) una curaduría manual
verificada externamente sobre una porción representativa de esas
coincidencias, organizada por eje temático, y (b) sentencias encontradas
por búsqueda externa directa que el buscador oficial no capturó con la
terminología probada. **No es una lista exhaustiva**: es razonable
esperar que sigan existiendo casos relevantes sin identificar, sobre todo
dentro de las combinaciones de "pornografía infantil" con otros términos
específicos, que no se revisaron todas.

## Sentencias verificadas, por eje temático

### Inteligencia artificial, algoritmos y automatización

| Sentencia | Año | Resumen |
|-----------|-----|---------|
| [T-323 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-323-24.htm) | 2024 | Un juez de segunda instancia usó ChatGPT para fundamentar una decisión sobre exoneración de copagos médicos de un niño con TEA. La Corte no prohibió el uso de IA generativa en la redacción de decisiones judiciales, pero advirtió sobre riesgos de alucinaciones y sesgos discriminatorios, y ordenó al Consejo Superior de la Judicatura divulgar en 4 meses una guía sobre el uso de IA generativa en la Rama Judicial. Es el precedente central de la región sobre IA y justicia. |
| [T-067 de 2025](https://www.corteconstitucional.gov.co/relatoria/2025/T-067-25.htm) | 2025 | Un ciudadano (profesor Juan Carlos Upegui) pidió acceso al código fuente de CoronApp, la app de vigilancia epidemiológica del gobierno durante la pandemia. La Corte tuteló el derecho, revocó los fallos que negaron el amparo, y estableció que **la transparencia algorítmica es parte del derecho de acceso a la información pública**: las entidades estatales deben avanzar hacia código abierto, auditoría algorítmica y sistemas explicables. Precedente fundacional sobre transparencia de sistemas automatizados del Estado. |
| [C-212 de 2026](https://www.corteconstitucional.gov.co/relatoria/2026/C-212-26.htm) | 2026 | Control de constitucionalidad del agravante penal del art. 296 del Código Penal (incorporado por la Ley 2502 de 2025), que aumenta la pena de falsedad personal (suplantación de identidad) cuando se comete usando inteligencia artificial. Se cuestionaba que la ley no define "IA", lo que abriría la puerta a interpretaciones arbitrarias; la Corte encontró parámetros técnicos y legales suficientes y avaló el agravante, citando estándares de la OCDE, UNESCO y el Reglamento europeo de IA. |

### Protección de datos, habeas data y vigilancia

| Sentencia | Año | Resumen |
|-----------|-----|---------|
| [T-360 de 2022](https://www.corteconstitucional.gov.co/relatoria/2022/T-360-22.htm) | 2022 | Banco Davivienda reportó al accionante en centrales de riesgo (Datacrédito) por obligaciones crediticias que nunca adquirió, obtenidas mediante suplantación de identidad. Resolvió sobre la protección del habeas data financiero frente al reporte negativo originado en fraude de identidad. |
| [T-294 de 2023](https://www.corteconstitucional.gov.co/relatoria/2023/T-294-23.htm) | 2023 | La periodista Claudia Julieta Duque, bajo esquema de protección de la Unidad Nacional de Protección (UNP), cuestionó que la entidad recolectara y almacenara datos de su geolocalización de forma más propia de labores de inteligencia/vigilancia que de protección. La Corte ordenó eliminar la información recopilada sobre ella, con ciertas excepciones. |
| [C-413 de 2025](https://www.corteconstitucional.gov.co/relatoria/2025/C-413-25.htm) | 2025 | Control previo de constitucionalidad del Proyecto de Ley Estatutaria 190/2022 (Cámara) – 303/2023 (Senado), que protege a las víctimas de suplantación de identidad digital frente a reportes negativos y cobros por deudas que no contrajeron: bancos y operadores de información deben suspender cobros y eliminar reportes negativos a víctimas de fraude digital. La Corte declaró inconstitucionales algunas expresiones del art. 5 y condicionó otras partes. |

### Redes sociales, plataformas y libertad de expresión

| Sentencia | Año | Resumen |
|-----------|-----|---------|
| [T-277 de 2015](https://www.corteconstitucional.gov.co/relatoria/2015/T-277-15.htm) | 2015 | Primer pronunciamiento de la Corte sobre el derecho al olvido en internet. Ordenó a El Tiempo bloquear el acceso de buscadores a un artículo antiguo que vinculaba a una persona con un delito ya prescrito. Sitios y buscadores pueden ser responsables del tratamiento de datos y sujetos al habeas data; las bases periodísticas quedan excluidas y se rigen por libertad de expresión. |
| [T-179 de 2019](https://www.corteconstitucional.gov.co/relatoria/2019/T-179-19.htm) | 2019 | La libertad de expresión tiene carácter preferente con cuatro presunciones a su favor; quien busca limitarla tiene la carga de la prueba. Convocó como amicus a organizaciones de derechos digitales (Centro de Internet y Sociedad U. Rosario, Fundación Karisma, FLIP, Relatoría CIDH) sobre límites a la opinión en plataformas digitales y redes sociales. |
| [T-229 de 2020](https://www.corteconstitucional.gov.co/relatoria/2020/T-229-20.htm) | 2020 | Tutela contra Google Inc. y el MinTIC. La Corte determinó que los intermediarios de internet no son responsables por el contenido publicado por sus usuarios y no deben ser sometidos a obligaciones de supervisión/filtrado para detectar contenido ilícito — precedente colombiano sobre responsabilidad de intermediarios. |
| [T-453 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-453-24.htm) | 2024 | TikTok bloqueó la cuenta de un influencer/abogado mayor de edad alegando que tenía menos de 13 años; pese a que envió su cédula para corregir el error, la plataforma mantuvo el bloqueo. La Corte concedió el amparo (debido proceso, habeas data) y ordenó a TikTok restablecer o corregir los datos. |
| [T-475 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-475-24.htm) | 2024 | Un periodista fue bloqueado sin explicación de la cuenta oficial de X del Gobierno del Cesar; la entidad alegó que incurrió en ciberacoso a funcionarios. Su tutela fue negada en ambas instancias. La sentencia fija la definición jurisprudencial de ciberacoso: publicación repetida y sistemática de humillaciones, insultos o expresiones desproporcionadas en redes/medios digitales, con intención dañina/ofensiva. |
| [T-256 de 2025](https://www.corteconstitucional.gov.co/relatoria/2025/T-256-25.htm) | 2025 | La creadora de contenido Esperanza Gómez demandó a Facebook/Meta por el borrado de su cuenta (+5 millones de seguidores) tras eliminar contenido y luego la cuenta completa por presuntas violaciones a normas sobre desnudez/servicios sexuales. La Corte se declaró competente por la conexión territorial del servicio con Colombia, reconoció la actividad de influencer como trabajo independiente legítimo, y fijó límites sustantivos y procesales al poder de moderación de contenido de las plataformas privadas — precedente de "constitucionalismo digital". |
| [T-176 de 2026](https://www.corteconstitucional.gov.co/relatoria/2026/T-176-26.htm) | 2026 | Suspensión de las cuentas de Facebook, Instagram y WhatsApp de un usuario colombiano. Las plataformas tienen el deber de combatir contenido ilícito (en particular de explotación sexual infantil), pero también deben garantizar mínimas garantías de debido proceso al tomar esas decisiones. |
| [T-372 de 2023](https://www.corteconstitucional.gov.co/relatoria/2023/T-372-23.htm) | 2023 | Durante el Paro Nacional de 2021 en Cali, el Gobierno no informó con claridad sobre apagones de internet y el presunto uso de inhibidores de señal por la fuerza pública. La Corte determinó que esto violó la libertad de expresión, asociación y reunión, y fijó límites desde derechos humanos al uso estatal de tecnología para controlar comunicaciones en contextos de protesta social. |
| [T-561 de 2023](https://www.corteconstitucional.gov.co/relatoria/2023/T-561-23.htm) | 2023 | Un usuario publicó en redes sociales un artículo que vinculaba a otra persona con la muerte de una joven en Bucaramanga, afectando su intimidad, buen nombre, honra y dignidad. La Corte resolvió la tensión entre libertad de expresión y protección de derechos fundamentales en publicaciones de redes sociales. |

### Violencia digital, menores y contenido íntimo

| Sentencia | Año | Resumen |
|-----------|-----|---------|
| [T-280 de 2022](https://www.corteconstitucional.gov.co/relatoria/2022/T-280-22.htm) | 2022 | Grabación y difusión no consentida de videos íntimos. La tutela es el mecanismo principal, idóneo y eficaz para proteger imagen e intimidad frente a la difusión no consentida de contenido íntimo; reconoció un vacío legal y llamó a regularlo. Precedente directo de la T-184 de 2026. |
| [T-245A de 2022](https://www.corteconstitucional.gov.co/relatoria/2022/T-245A-22.htm) | 2022 | Un padre demandó a la madre de su hijo menor por publicar imágenes del niño en una cuenta de redes sociales pública y asociada a una plataforma de contenido para adultos, buscando proteger intimidad, buen nombre, libre desarrollo de la personalidad y prevalencia de los derechos del niño. |
| [T-249 de 2024](https://www.corteconstitucional.gov.co/relatoria/2024/T-249-24.htm) | 2024 | Protección de un menor víctima de acoso escolar y ciberacoso simultáneos; la Corte usó nombres ficticios en el fallo para proteger su privacidad. |
| [T-184 de 2026](https://www.corteconstitucional.gov.co/relatoria/2026/T-184-26.htm) | 2026 | "Paola" grabó contenido íntimo con "Lucas" para difundirlo en redes bajo la condición de bloquearlo en Colombia; él lo difundió sin esa restricción y permitió que siguiera circulando. La Corte calificó la difusión no consentida de contenido íntimo como violencia digital/de género, fijó que el consentimiento es revocable, exhortó al Congreso a legislar y ordenó a la Defensoría del Pueblo y al MinTIC crear una guía de prevención digital. |

### Economía y comercio digital

| Sentencia | Año | Resumen |
|-----------|-----|---------|
| [T-584 de 2023](https://www.corteconstitucional.gov.co/relatoria/2023/T-584-23.htm) | 2023 | Un usuario de la app de préstamos digitales Lukiao App, en mora, recibió mensajes amenazantes e intimidatorios en la cobranza. La Corte exhortó a la Superintendencia de Industria y Comercio a hacer seguimiento a quejas contra apps de préstamo de dinero. |

## Pendiente de verificar / casos con verificación parcial

- **T-190 de 2024** — tutela por libertad de expresión y protección de menores contra Fucks News S.A.S. y, subsidiariamente, contra Google, Meta, ByteDance/TikTok por contenido algorítmico; **declarada improcedente** por falta de legitimación y subsidiariedad — no hubo pronunciamiento de fondo sobre algoritmos.
- **T-450 de 2025**, **T-186 de 2026**, **T-457 de 2025** — match en "inteligencia artificial"/"algoritmo", sin verificación externa disponible.
- **T-234 de 2024**, **T-304 de 2023** — "internet de las cosas"; sin verificar.
- **T-227 de 2025**, **T-203 de 2022**, **T-242 de 2022**, **T-260 de 2012**, **T-310 de 2022**, **T-342 de 2020**, **T-356 de 2021**, **T-362 de 2020** — combinaciones de "pornografía infantil" con otro término específico (ciberacoso, grooming, sexting, phishing, dron, suplantación de identidad); dado que T-184/26, T-280/22 y T-245A/22 confirmaron que este patrón sí puede señalar casos reales de violencia digital (no solo explotación sexual infantil), es plausible que algunas de estas también lo sean, pero no se verificaron individualmente.
- Sentencias encontradas por "perfilamiento" en la segunda corrida (T-202-24, T-208-26, T-236-21, T-270-24 nota: año probablemente mal capturado por un bug de parseo, revisar, T-310-22, T-365-22, T-388-25, T-391-25, T-397-25, T-491-25, T-560-16, T-594-16) — no se verificó ninguna individualmente; "perfilamiento" es un concepto legítimo de habeas data (Ley 1581/2012) así que el patrón amerita revisión futura.

## Pistas descartadas (verificadas pero no aplicables)

- **T-500 de 2011** — "Apuestas en Línea S.A." es el nombre propio de la empresa concesionaria del juego de Chance en Bogotá/Cundinamarca: contrato de concesión, no regulación de apuestas/juego en internet.
- **T-388 de 2013** y **T-762 de 2015** — sentencias que declaran y hacen seguimiento al Estado de Cosas Inconstitucional del sistema penitenciario y carcelario colombiano por hacinamiento; match incidental con varios términos, sin relación con derecho digital.
- **T-760 de 2008** — sentencia histórica y extensa sobre el sistema de salud (unificación del POS); match incidental con "inteligencia artificial", "algoritmo" y "minería de datos" dado el tamaño y alcance del fallo.

## Temas sin sentencia colombiana encontrada con estos términos

**Blockchain**, **voto electrónico**, **contrato inteligente** y
**alucinación** (como término aislado) no aparecieron en ninguna de las
989 sentencias de la primera corrida — no significa que no exista
jurisprudencia sobre esos temas, solo que no hizo match con la
terminología exacta probada.

## Nota metodológica final

A diferencia del documento de Ecuador (que usa la API JSON real y
devuelve metadatos estructurados — ponente, resumen oficial, fecha exacta
de decisión), el buscador de Colombia solo permite extraer con
confiabilidad el **número de sentencia** desde el HTML de resultados; no
se intentó extraer fecha de decisión exacta, ponente ni resumen oficial
por sentencia de forma automatizada (el año se infiere del propio número
de sentencia, p. ej. "24" en T-323-24 → 2024, con al menos un caso de
parseo erróneo detectado — T-270 de "20024"). Cada sentencia de la tabla
verificada sí se confirmó individualmente por fuera del buscador. Una
futura iteración podría usar la ficha individual de cada sentencia
(`/relatoria/<año>/<TIPO>-<num>-<yy>.htm`) para extraer esos metadatos de
forma automática y ampliar la cobertura de verificación más allá de la
curaduría manual hecha aquí.
