"use client";

import { FormEvent, useState } from "react";
import styles from "./page.module.css";
import type { Hallazgo, ResultadoAuditoria, Severidad } from "@/lib/audit";

const ETIQUETA_SEVERIDAD: Record<Severidad, string> = {
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
  info: "Info",
};

const ORDEN_SEVERIDAD: Record<Severidad, number> = { alto: 0, medio: 1, bajo: 2, info: 3 };

function agruparPorCategoria(hallazgos: Hallazgo[]): [string, Hallazgo[]][] {
  const mapa = new Map<string, Hallazgo[]>();
  for (const h of hallazgos) {
    if (!mapa.has(h.categoria)) mapa.set(h.categoria, []);
    mapa.get(h.categoria)!.push(h);
  }
  for (const lista of mapa.values()) {
    lista.sort((a, b) => ORDEN_SEVERIDAD[a.severidad] - ORDEN_SEVERIDAD[b.severidad]);
  }
  return [...mapa.entries()];
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoAuditoria | null>(null);

  async function auditar(e: FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setCargando(true);
    setError(null);
    setResultado(null);

    try {
      const resp = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.error || "Ocurrió un error al auditar el sitio.");
        return;
      }
      setResultado(data as ResultadoAuditoria);
    } catch {
      setError("No se pudo conectar con el servidor. Intenta de nuevo.");
    } finally {
      setCargando(false);
    }
  }

  const conteo = { alto: 0, medio: 0, bajo: 0, info: 0 };
  for (const h of resultado?.hallazgos ?? []) conteo[h.severidad]++;

  return (
    <main className={styles.main}>
      <div className={styles.header}>
        <h1 className={styles.title}>Auditor de Protección de Datos Personales</h1>
        <p className={styles.subtitle}>
          Pega la URL de un sitio web y revisa indicios sobre su tratamiento de datos
          personales: HTTPS, cookies, rastreadores de terceros, formularios y política de
          privacidad, con referencia a la LOPDP de Ecuador.
        </p>
      </div>

      <form className={styles.form} onSubmit={auditar}>
        <input
          className={styles.input}
          type="text"
          inputMode="url"
          placeholder="https://ejemplo.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={cargando}
          aria-label="URL del sitio a auditar"
        />
        <button className={styles.button} type="submit" disabled={cargando || !url.trim()}>
          {cargando ? "Auditando…" : "Auditar"}
        </button>
      </form>
      <p className={styles.hint}>
        Solo se admiten sitios públicos accesibles por HTTP o HTTPS.
      </p>

      {cargando && <p className={styles.loading}>Cargando el sitio y analizando su contenido…</p>}
      {error && <p className={styles.error}>{error}</p>}

      {resultado && (
        <div>
          <div className={styles.summary}>
            <span
              className={styles.summaryItem}
              style={{ color: "var(--alto)", background: "var(--alto-bg)" }}
            >
              {conteo.alto} alto{conteo.alto === 1 ? "" : "s"}
            </span>
            <span
              className={styles.summaryItem}
              style={{ color: "var(--medio)", background: "var(--medio-bg)" }}
            >
              {conteo.medio} medio{conteo.medio === 1 ? "" : "s"}
            </span>
            <span
              className={styles.summaryItem}
              style={{ color: "var(--bajo)", background: "var(--bajo-bg)" }}
            >
              {conteo.bajo} bajo{conteo.bajo === 1 ? "" : "s"}
            </span>
            <span
              className={styles.summaryItem}
              style={{ color: "var(--info)", background: "var(--info-bg)" }}
            >
              {conteo.info} informativo{conteo.info === 1 ? "" : "s"}
            </span>
          </div>

          {agruparPorCategoria(resultado.hallazgos).map(([categoria, hallazgos]) => (
            <div className={styles.category} key={categoria}>
              <h2 className={styles.categoryTitle}>{categoria}</h2>
              {hallazgos.map((h, i) => (
                <div className={styles.finding} key={i}>
                  <span
                    className={styles.badge}
                    style={{ color: `var(--${h.severidad})`, background: `var(--${h.severidad}-bg)` }}
                  >
                    {ETIQUETA_SEVERIDAD[h.severidad]}
                  </span>
                  <span>{h.descripcion}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <div className={styles.footer}>
        Esta auditoría es un apoyo técnico automatizado y no sustituye una revisión legal
        completa bajo la LOPDP (Ecuador) u otras normas aplicables: no verifica, por ejemplo,
        contratos con encargados del tratamiento, registros de actividades de tratamiento,
        evaluaciones de impacto ni cookies/rastreadores cargados dinámicamente por JavaScript.
      </div>
    </main>
  );
}
