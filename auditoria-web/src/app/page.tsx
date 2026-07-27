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

const EXPLICACION_CATEGORIA: Record<string, string> = {
  "Cifrado en tránsito":
    "Indica si la comunicación entre el navegador del usuario y el sitio va cifrada (HTTPS). Sin esto, cualquier persona en la misma red podría leer los datos que se envían.",
  "Certificado TLS":
    "El certificado es el documento digital que confirma la identidad del sitio y habilita el candado del navegador. Aquí se revisa si es válido, si la cadena hasta una entidad de confianza está completa, y cuánto le falta para vencer.",
  "Cabeceras de seguridad":
    "Instrucciones que el servidor envía al navegador para reforzar la seguridad (por ejemplo, forzar HTTPS o bloquear scripts no autorizados). Que falten no es necesariamente grave, pero reduce las protecciones disponibles.",
  Cookies:
    "Pequeños archivos que el sitio guarda en el navegador del usuario, usados por ejemplo para mantener una sesión iniciada. Se revisa cuántas hay, si son de terceros (posible rastreo entre sitios) y si viajan protegidas con el flag \"Secure\" (solo por HTTPS).",
  "Rastreadores de terceros":
    "Scripts de servicios externos (como Google Analytics o Meta Pixel) que recolectan datos sobre el comportamiento de quienes visitan el sitio. Deben estar declarados en la política de privacidad y, salvo excepción legal, requieren el consentimiento previo del usuario.",
  Formularios:
    "Campos donde el usuario ingresa información personal (correo, teléfono, cédula, etc.). Se revisa si el envío viaja por HTTPS y si se pide una casilla de consentimiento antes de enviar los datos.",
  "Política de privacidad":
    "El documento donde el sitio debe explicar qué datos personales recolecta, para qué los usa y qué derechos tiene el usuario (por ejemplo, los derechos ARCO: Acceso, Rectificación, Cancelación y Oposición). Se revisa si existe un enlace visible y si su contenido cubre los puntos exigidos por la LOPDP de Ecuador.",
};

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

  const fechaLegible = resultado
    ? new Date(resultado.fecha).toLocaleString("es-EC", {
        dateStyle: "long",
        timeStyle: "short",
      })
    : "";

  return (
    <main className={styles.main}>
      <div className={`${styles.header} ${styles.noImprimir}`}>
        <h1 className={styles.title}>Auditor de Protección de Datos Personales</h1>
        <p className={styles.subtitle}>
          Pega la URL de un sitio web y revisa indicios sobre su tratamiento de datos
          personales: HTTPS, cookies, rastreadores de terceros, formularios y política de
          privacidad, con referencia a la LOPDP de Ecuador.
        </p>
      </div>

      <form className={`${styles.form} ${styles.noImprimir}`} onSubmit={auditar}>
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
      <p className={`${styles.hint} ${styles.noImprimir}`}>
        Solo se admiten sitios públicos accesibles por HTTP o HTTPS.
      </p>

      {cargando && (
        <p className={`${styles.loading} ${styles.noImprimir}`}>
          Cargando el sitio y analizando su contenido…
        </p>
      )}
      {error && <p className={`${styles.error} ${styles.noImprimir}`}>{error}</p>}

      {resultado && (
        <div className={styles.reporte}>
          <div className={styles.soloImprimir}>
            <h1 className={styles.reporteTitulo}>Informe de Auditoría de Protección de Datos Personales</h1>
            <p>
              <strong>Sitio auditado:</strong> {resultado.url}
            </p>
            <p>
              <strong>Fecha del análisis:</strong> {fechaLegible}
            </p>
            <p>
              <strong>Generado con:</strong> Auditor de Protección de Datos Personales
              (auditoriadatos-web.vercel.app)
            </p>
          </div>

          <div className={`${styles.summaryRow} ${styles.noImprimir}`}>
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
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => window.print()}
            >
              Descargar informe (PDF)
            </button>
          </div>

          {agruparPorCategoria(resultado.hallazgos).map(([categoria, hallazgos]) => (
            <div className={styles.category} key={categoria}>
              <h2 className={styles.categoryTitle}>{categoria}</h2>
              {EXPLICACION_CATEGORIA[categoria] && (
                <p className={styles.categoryExplicacion}>{EXPLICACION_CATEGORIA[categoria]}</p>
              )}
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
        <p>
          Esta auditoría es un apoyo técnico automatizado y no sustituye una revisión legal
          completa bajo la LOPDP (Ecuador) u otras normas de protección de datos que puedan
          aplicar (por ejemplo, en transferencias internacionales). Los niveles de severidad son
          indicadores heurísticos para priorizar la revisión, no un dictamen legal concluyente, y
          deben ser corroborados por un profesional de derecho o protección de datos.
        </p>
        <p>Entre otras cosas, esta herramienta no verifica:</p>
        <ul className={styles.footerList}>
          <li>Contratos con encargados del tratamiento ni cláusulas de confidencialidad.</li>
          <li>El registro de actividades de tratamiento (RAT).</li>
          <li>Evaluaciones de impacto de protección de datos (EIPD) cuando correspondan.</li>
          <li>La designación de un Delegado de Protección de Datos, cuando la ley lo exige.</li>
          <li>Procedimientos internos de respuesta ante incidentes o brechas de seguridad.</li>
          <li>
            Cookies, rastreadores o llamadas a servicios de terceros que un sitio agrega
            dinámicamente por JavaScript (esta versión web solo analiza el HTML y las cabeceras
            de la carga inicial del servidor).
          </li>
          <li>Medidas de seguridad físicas u organizativas, ni la seguridad real de las bases de datos o sistemas backend.</li>
          <li>
            Si las prácticas declaradas en la política de privacidad (plazos de conservación,
            finalidades, etc.) se cumplen realmente en la operación del sitio.
          </li>
          <li>
            Otras páginas, subdominios o aplicaciones móviles del mismo responsable: el análisis
            se limita a la URL exacta ingresada, en el momento en que se ejecutó.
          </li>
        </ul>
      </div>
    </main>
  );
}
