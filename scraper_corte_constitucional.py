"""
Scraper de sentencias sobre Control de Constitucionalidad
Corte Constitucional del Ecuador
Ejecutar desde tu máquina local.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import csv
from urllib.parse import urljoin, urlencode

BASE_PORTAL = "https://portal.corteconstitucional.gob.ec"
BASE_SACC   = "https://esacc.corteconstitucional.gob.ec"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
}

# Tipos de acción relacionados con control de constitucionalidad
# Fuente: Ley Orgánica de Garantías Jurisdiccionales y Control Constitucional
TIPOS_CONTROL = {
    "IN":  "Inconstitucionalidad (control abstracto)",
    "CN":  "Consulta de Norma (control concreto)",
    "RC":  "Control constitucionalidad de referendo",
    "SCN": "Sentencia de consulta de norma",
    "SIN": "Sentencia de inconstitucionalidad",
}

session = requests.Session()
session.headers.update(HEADERS)


def buscar_relatoría(tipo_accion: str, max_paginas: int = 5) -> list[dict]:
    """
    Busca sentencias en el Buscador de Relatoría del portal.
    tipo_accion: 'IN', 'CN', 'RC', etc.
    """
    sentencias = []
    url = f"{BASE_PORTAL}/BuscadorRelatoria.aspx"

    print(f"\n[*] Buscando tipo: {tipo_accion} - {TIPOS_CONTROL.get(tipo_accion, '')}")

    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"    [ERROR] No se pudo acceder al buscador: {e}")
        return sentencias

    soup = BeautifulSoup(r.text, "lxml")

    # Extraer ViewState para formularios ASP.NET
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    eventval  = soup.find("input", {"name": "__EVENTVALIDATION"})

    payload = {
        "__VIEWSTATE":       viewstate["value"] if viewstate else "",
        "__EVENTVALIDATION": eventval["value"]  if eventval  else "",
        "txtTipoAccion":     tipo_accion,
        "btnBuscar":         "Buscar",
    }

    try:
        r2 = session.post(url, data=payload, timeout=20)
        r2.raise_for_status()
    except Exception as e:
        print(f"    [ERROR] POST falló: {e}")
        return sentencias

    soup2 = BeautifulSoup(r2.text, "lxml")
    filas = soup2.find_all("tr")

    for fila in filas:
        celdas = fila.find_all("td")
        if len(celdas) >= 3:
            numero = celdas[0].get_text(strip=True)
            if tipo_accion.upper() in numero.upper() or "CC" in numero:
                enlace_tag = fila.find("a", href=True)
                enlace = urljoin(BASE_PORTAL, enlace_tag["href"]) if enlace_tag else ""
                sentencias.append({
                    "numero":   numero,
                    "tipo":     tipo_accion,
                    "resumen":  celdas[1].get_text(strip=True)[:200] if len(celdas) > 1 else "",
                    "fecha":    celdas[2].get_text(strip=True) if len(celdas) > 2 else "",
                    "enlace":   enlace,
                })

    print(f"    => {len(sentencias)} sentencias encontradas")
    return sentencias


def buscar_ficha_relatoria(num_documento: str) -> dict:
    """
    Obtiene el detalle de una sentencia específica.
    Ejemplo: num_documento = '001-13-SCN-CC'
    """
    url = f"{BASE_PORTAL}/FichaRelatoria.aspx?numdocumento={num_documento}"
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        campos = {}
        for label in soup.find_all(["label", "span", "td"]):
            texto = label.get_text(strip=True)
            if texto and len(texto) > 3:
                campos[texto[:50]] = texto
        return campos
    except Exception as e:
        return {"error": str(e)}


def buscar_en_sacc_publico(termino: str = "control constitucionalidad") -> list[dict]:
    """
    Intenta el buscador público del SACC.
    """
    resultados = []
    url = f"{BASE_SACC}/app/publico/buscar"
    params = {"q": termino, "tipo": "sentencia"}
    try:
        r = session.get(url, params=params, timeout=20)
        if r.status_code == 200:
            ct = r.headers.get("Content-Type", "")
            if "json" in ct:
                data = r.json()
                print(f"[SACC JSON] {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                resultados = data if isinstance(data, list) else [data]
            else:
                soup = BeautifulSoup(r.text, "lxml")
                items = soup.find_all(class_=["resultado", "sentencia", "causa", "item"])
                for item in items:
                    resultados.append({"texto": item.get_text(strip=True)[:200]})
        else:
            print(f"[SACC] Status {r.status_code}")
    except Exception as e:
        print(f"[SACC ERROR] {e}")
    return resultados


def exportar_csv(sentencias: list[dict], archivo: str = "sentencias_cc.csv"):
    if not sentencias:
        print("Sin datos para exportar.")
        return
    campos = list(sentencias[0].keys())
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(sentencias)
    print(f"\n[OK] Exportado: {archivo} ({len(sentencias)} registros)")


def main():
    print("=" * 65)
    print("  Scraper - Sentencias Control de Constitucionalidad")
    print("  Corte Constitucional del Ecuador")
    print("=" * 65)

    todas = []

    # 1. Buscar por cada tipo de acción
    for tipo in TIPOS_CONTROL:
        s = buscar_relatoría(tipo)
        todas.extend(s)
        time.sleep(1.5)

    # 2. Intentar buscador SACC público
    print("\n[*] Intentando buscador SACC público...")
    sacc_results = buscar_en_sacc_publico("control de constitucionalidad")
    if sacc_results:
        print(f"    => {len(sacc_results)} resultados del SACC")

    # 3. Detalle de una sentencia de ejemplo
    print("\n[*] Obteniendo ficha de ejemplo: 001-13-SCN-CC")
    ficha = buscar_ficha_relatoria("001-13-SCN-CC")
    if "error" not in ficha:
        print("    Campos encontrados:")
        for k, v in list(ficha.items())[:15]:
            print(f"      {k}: {v[:80]}")

    # 4. Exportar
    exportar_csv(todas)

    print(f"\n[TOTAL] {len(todas)} sentencias recopiladas")
    print("\nURLs útiles para explorar manualmente:")
    print(f"  {BASE_PORTAL}/BuscadorRelatoria.aspx")
    print(f"  {BASE_PORTAL}/BuscadorSeleccion.aspx")
    print(f"  {BASE_SACC}/app/inicio")


if __name__ == "__main__":
    main()
