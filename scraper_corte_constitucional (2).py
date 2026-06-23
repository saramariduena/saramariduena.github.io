"""
Scraper de sentencias - Control de Constitucionalidad
Corte Constitucional del Ecuador
Usa el buscador público y Google como fuente alternativa.
"""

import requests
from bs4 import BeautifulSoup
import csv, time, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

session = requests.Session()
session.headers.update(HEADERS)

DOMINIOS = [
    "https://www.corteconstitucional.gob.ec",
    "https://buscador.corteconstitucional.gob.ec",
    "https://esacc.corteconstitucional.gob.ec",
]

TERMINOS = [
    "sentencia control constitucionalidad",
    "inconstitucionalidad abstracto",
    "consulta norma control concreto",
    "referendo control constitucional",
]

def probar_dominios():
    print("Probando acceso a dominios de la Corte Constitucional...\n")
    accesibles = []
    for dominio in DOMINIOS:
        try:
            r = session.get(dominio, timeout=10)
            print(f"  [OK {r.status_code}] {dominio}")
            accesibles.append((dominio, r))
        except Exception as e:
            print(f"  [FALLO] {dominio} => {e}")
    return accesibles


def scrape_buscador_cc(termino: str) -> list[dict]:
    """Busca en el buscador público de la Corte Constitucional."""
    resultados = []
    urls_buscador = [
        f"https://buscador.corteconstitucional.gob.ec/search?q={termino.replace(' ', '+')}",
        f"https://www.corteconstitucional.gob.ec/?s={termino.replace(' ', '+')}",
        f"https://esacc.corteconstitucional.gob.ec/app/publico/sentencias?q={termino.replace(' ', '+')}",
    ]
    for url in urls_buscador:
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                # Buscar cualquier enlace que parezca sentencia
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    texto = a.get_text(strip=True)
                    if any(x in href.lower() or x in texto.lower() for x in
                           ["sentencia", "sc-", "in/", "cn/", "rc/", "scn-cc", "sin-cc"]):
                        resultados.append({
                            "titulo": texto[:150],
                            "enlace": href,
                            "fuente": url,
                            "termino": termino,
                        })
                if resultados:
                    print(f"  [OK] {len(resultados)} resultados en {url}")
                    break
        except Exception as e:
            print(f"  [Error] {url}: {e}")
    return resultados


def scrape_google(termino: str) -> list[dict]:
    """Busca en Google limitado al sitio de la Corte Constitucional."""
    resultados = []
    query = f"site:corteconstitucional.gob.ec {termino}"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=20&hl=es"
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for div in soup.find_all("div", class_=["tF2Cxc", "g", "yuRUbf"]):
                a = div.find("a", href=True)
                h3 = div.find("h3")
                desc = div.find(["span", "div"], class_=["VwiC3b", "aCOpRe", "lEBKkf"])
                if a:
                    resultados.append({
                        "titulo": h3.get_text(strip=True) if h3 else a.get_text(strip=True),
                        "enlace": a["href"],
                        "descripcion": desc.get_text(strip=True)[:200] if desc else "",
                        "fuente": "Google",
                        "termino": termino,
                    })
            print(f"  [Google] {len(resultados)} resultados para: {termino}")
        else:
            print(f"  [Google] Status {r.status_code}")
    except Exception as e:
        print(f"  [Google Error] {e}")
    return resultados


def scrape_bing(termino: str) -> list[dict]:
    """Busca en Bing limitado al sitio de la Corte Constitucional."""
    resultados = []
    query = f"site:corteconstitucional.gob.ec {termino}"
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=20"
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for li in soup.find_all("li", class_="b_algo"):
                a = li.find("a", href=True)
                h2 = li.find("h2")
                p = li.find("p")
                if a:
                    resultados.append({
                        "titulo": h2.get_text(strip=True) if h2 else a.get_text(strip=True),
                        "enlace": a["href"],
                        "descripcion": p.get_text(strip=True)[:200] if p else "",
                        "fuente": "Bing",
                        "termino": termino,
                    })
            print(f"  [Bing] {len(resultados)} resultados para: {termino}")
        else:
            print(f"  [Bing] Status {r.status_code}")
    except Exception as e:
        print(f"  [Bing Error] {e}")
    return resultados


def exportar_csv(datos: list[dict], archivo: str = "sentencias_cc.csv"):
    if not datos:
        print("\nSin datos para exportar.")
        return
    campos = list(datos[0].keys())
    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(datos)
    print(f"\n[OK] Archivo generado: {archivo} ({len(datos)} registros)")


def main():
    print("=" * 65)
    print("  Scraper - Sentencias Control de Constitucionalidad")
    print("  Corte Constitucional del Ecuador")
    print("=" * 65 + "\n")

    # 1. Probar acceso directo
    accesibles = probar_dominios()

    todos = []

    # 2. Intentar scraping directo si hay acceso
    if accesibles:
        print("\n[*] Intentando buscador interno de la Corte...")
        for termino in TERMINOS[:2]:
            r = scrape_buscador_cc(termino)
            todos.extend(r)
            time.sleep(1)

    # 3. Google como fuente principal
    print("\n[*] Buscando en Google (site:corteconstitucional.gob.ec)...")
    for termino in TERMINOS:
        r = scrape_google(termino)
        todos.extend(r)
        time.sleep(2)

    # 4. Bing como fuente secundaria
    print("\n[*] Buscando en Bing (site:corteconstitucional.gob.ec)...")
    for termino in TERMINOS:
        r = scrape_bing(termino)
        todos.extend(r)
        time.sleep(2)

    # Deduplicar por enlace
    vistos = set()
    unicos = []
    for item in todos:
        enlace = item.get("enlace", "")
        if enlace not in vistos:
            vistos.add(enlace)
            unicos.append(item)

    print(f"\n[TOTAL] {len(unicos)} sentencias únicas encontradas")

    # Mostrar en pantalla
    print("\n--- RESULTADOS ---")
    for i, item in enumerate(unicos[:20], 1):
        print(f"\n{i}. {item.get('titulo','')[:80]}")
        print(f"   {item.get('enlace','')[:100]}")
        if item.get("descripcion"):
            print(f"   {item.get('descripcion','')[:100]}")

    exportar_csv(unicos)


if __name__ == "__main__":
    main()
