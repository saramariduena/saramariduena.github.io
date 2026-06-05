"""
Analizador descriptivo — Fase 2 del modelo pedagógico de jurimetría.
Toma la lista de sentencias enriquecidas con variables y produce:
  - Un archivo CSV listo para abrir en cualquier hoja de cálculo
  - Un resumen de estadísticas descriptivas en texto
El énfasis pedagógico está en leer el resultado y hacerse las preguntas correctas,
no en el dominio del software.
"""

import csv
import io
import logging
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

COLUMNAS_CSV = [
    "numero",
    "tipo",
    "fecha",
    "ponente",
    "numero_causa",
    "tipo_accion",
    "organo_jurisdiccional",
    "fecha_inicio",
    "fecha_resolucion",
    "duracion_dias",
    "decision",
    "derecho_invocado",
    "materia",
    "etapa_prueba_dias",
    "observaciones",
    "resumen",
    "ficha_url",
]


def exportar_csv(sentencias: list[dict], ruta: str = "jurimetria_datos.csv") -> Path:
    """Exporta la lista de sentencias enriquecidas a un CSV."""
    ruta_path = Path(ruta)
    with open(ruta_path, "w", newline="", encoding="utf-8-sig") as f:
        # utf-8-sig garantiza que Excel en Windows abra bien el archivo
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_CSV, extrasaction="ignore")
        escritor.writeheader()
        for s in sentencias:
            fila = {col: _serializar(s.get(col)) for col in COLUMNAS_CSV}
            escritor.writerow(fila)
    logger.info(f"CSV exportado: {ruta_path} ({len(sentencias)} filas)")
    return ruta_path


def generar_resumen(sentencias: list[dict]) -> str:
    """
    Calcula estadísticas descriptivas básicas y devuelve un informe en texto.
    Diseñado para que un estudiante de Derecho pueda leerlo sin formación estadística previa.
    """
    n = len(sentencias)
    if n == 0:
        return "Sin datos para analizar."

    lineas = [
        "=" * 60,
        "RESUMEN DE ANÁLISIS JURIMÉTRICO",
        f"Total de decisiones analizadas: {n}",
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "=" * 60,
        "",
    ]

    # Distribución por tipo de acción
    tipos = Counter(s.get("tipo_accion") or s.get("tipo") or "No identificado" for s in sentencias)
    lineas.append("DISTRIBUCIÓN POR TIPO DE ACCIÓN")
    lineas.append("-" * 40)
    for tipo, cnt in tipos.most_common():
        pct = cnt / n * 100
        lineas.append(f"  {tipo:<40} {cnt:>4}  ({pct:.1f}%)")
    lineas.append("")

    # Distribución por órgano jurisdiccional
    organos = Counter(
        s.get("organo_jurisdiccional") or "No identificado" for s in sentencias
    )
    lineas.append("DISTRIBUCIÓN POR ÓRGANO JURISDICCIONAL")
    lineas.append("-" * 40)
    for organo, cnt in organos.most_common(10):
        pct = cnt / n * 100
        lineas.append(f"  {organo:<40} {cnt:>4}  ({pct:.1f}%)")
    if len(organos) > 10:
        lineas.append(f"  … y {len(organos) - 10} órganos más")
    lineas.append("")

    # Distribución por decisión
    decisiones = Counter(s.get("decision") or "no determinado" for s in sentencias)
    lineas.append("DISTRIBUCIÓN POR DECISIÓN")
    lineas.append("-" * 40)
    for decision, cnt in decisiones.most_common():
        pct = cnt / n * 100
        lineas.append(f"  {decision:<40} {cnt:>4}  ({pct:.1f}%)")
    lineas.append("")

    # Distribución por materia
    materias = Counter(s.get("materia") or "No identificada" for s in sentencias)
    lineas.append("DISTRIBUCIÓN POR MATERIA")
    lineas.append("-" * 40)
    for materia, cnt in materias.most_common():
        pct = cnt / n * 100
        lineas.append(f"  {materia:<40} {cnt:>4}  ({pct:.1f}%)")
    lineas.append("")

    # Estadísticas de duración
    duraciones = [
        int(s["duracion_dias"])
        for s in sentencias
        if s.get("duracion_dias") is not None
        and str(s["duracion_dias"]).lstrip("-").isdigit()
    ]
    if duraciones:
        duraciones_pos = [d for d in duraciones if d >= 0]
        lineas.append("DURACIÓN DE LOS PROCESOS (días)")
        lineas.append("-" * 40)
        lineas.append(f"  Procesos con dato de duración: {len(duraciones_pos)} de {n}")
        if duraciones_pos:
            lineas.append(f"  Promedio:  {statistics.mean(duraciones_pos):.0f} días")
            lineas.append(f"  Mediana:   {statistics.median(duraciones_pos):.0f} días")
            lineas.append(f"  Mínimo:    {min(duraciones_pos)} días")
            lineas.append(f"  Máximo:    {max(duraciones_pos)} días")
            if len(duraciones_pos) > 1:
                lineas.append(f"  Desv. est: {statistics.stdev(duraciones_pos):.0f} días")
        lineas.append("")

    # Estadísticas de etapa de prueba
    pruebas = [
        int(s["etapa_prueba_dias"])
        for s in sentencias
        if s.get("etapa_prueba_dias") is not None
        and str(s["etapa_prueba_dias"]).lstrip("-").isdigit()
        and int(s["etapa_prueba_dias"]) >= 0
    ]
    if pruebas:
        lineas.append("DURACIÓN DE LA ETAPA DE PRUEBA (días)")
        lineas.append("-" * 40)
        lineas.append(f"  Procesos con dato de etapa de prueba: {len(pruebas)} de {n}")
        lineas.append(f"  Promedio:  {statistics.mean(pruebas):.0f} días")
        lineas.append(f"  Mediana:   {statistics.median(pruebas):.0f} días")
        lineas.append(f"  Mínimo:    {min(pruebas)} días")
        lineas.append(f"  Máximo:    {max(pruebas)} días")
        # Desglose por órgano si hay suficientes datos
        por_organo = {}
        for s in sentencias:
            if s.get("etapa_prueba_dias") is not None:
                try:
                    dias = int(s["etapa_prueba_dias"])
                    if dias >= 0:
                        organo = s.get("organo_jurisdiccional") or "No identificado"
                        por_organo.setdefault(organo, []).append(dias)
                except (ValueError, TypeError):
                    pass
        if len(por_organo) > 1:
            lineas.append("")
            lineas.append("  Promedio por órgano jurisdiccional:")
            for organo, vals in sorted(por_organo.items(), key=lambda x: -statistics.mean(x[1])):
                lineas.append(
                    f"    {organo:<36} {statistics.mean(vals):.0f} días (n={len(vals)})"
                )
        lineas.append("")

    # Aviso metodológico (Phase 3 seed questions)
    lineas += [
        "=" * 60,
        "PREGUNTAS PARA LA DISCUSIÓN JURÍDICA (Fase 3)",
        "=" * 60,
        "",
        "1. ¿Qué explica el patrón de distribución por tipo de acción?",
        "   ¿Refleja la realidad del sistema o sesgos de la muestra?",
        "",
        "2. ¿Qué casos quedaron fuera de esta muestra y por qué?",
        "   (ej: sentencias sin texto digitalizado, períodos no cubiertos)",
        "",
        "3. ¿Qué variables relevantes NO captura este modelo?",
        "   (ej: calidad de la argumentación, complejidad del caso,",
        "    recursos de las partes, representación legal)",
        "",
        "4. ¿Qué riesgos éticos plantea extrapolar estos promedios",
        "   a un caso individual concreto?",
        "",
        "5. Si encontraste variación de duración por órgano,",
        "   ¿qué explicaciones jurídicas (no solo estadísticas) puedes ofrecer?",
        "",
        "Recuerda: el valor de la jurimetría no está en predecir sentencias,",
        "sino en formular preguntas empíricas verificables sobre el sistema.",
        "",
    ]

    return "\n".join(lineas)


def _serializar(valor) -> str:
    """Convierte cualquier valor a string apto para CSV."""
    if valor is None:
        return ""
    if isinstance(valor, list):
        return "; ".join(str(v) for v in valor)
    return str(valor)
