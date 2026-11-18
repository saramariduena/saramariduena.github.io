"""
Consulta puntual de una o más sentencias por número exacto, con el resumen
completo (hasta 4000 caracteres) impreso en consola — útil para verificar
manualmente un caso puntual encontrado por buscar_sentencias_ia.py sin tener
que descargar el artefacto JSON.

Uso: NUMEROS="580-23-EP/26,3156-22-EP/26" python consultar_sentencia.py
"""

import os
from scraper import buscar_sentencias

numeros = [n.strip() for n in os.environ.get("NUMEROS", "").split(",") if n.strip()]

for numero in numeros:
    print("\n" + "=" * 70)
    print(f"Consultando: {numero}")
    resultados = buscar_sentencias(numero=numero, max_results=5, dias=6500)
    if not resultados:
        print("Sin resultados.")
        continue
    for s in resultados:
        print(f"Número: {s.numero}")
        print(f"Tipo: {s.tipo}")
        print(f"Fecha: {s.fecha}")
        print(f"Ponente: {s.ponente}")
        print(f"Resumen completo:\n{s.resumen}")
        print(f"Ficha: {s.ficha_url}")
