import * as cheerio from "cheerio";
import dns from "node:dns/promises";
import net from "node:net";
import tls from "node:tls";
import { Agent, fetch as fetchUndici } from "undici";

export type Severidad = "alto" | "medio" | "bajo" | "info";

export interface Hallazgo {
  categoria: string;
  severidad: Severidad;
  descripcion: string;
}

export interface ResultadoAuditoria {
  url: string;
  fecha: string;
  hallazgos: Hallazgo[];
}

export class AuditError extends Error {}

// fetch (undici) suele envolver el error real en `.cause` con un mensaje genérico
// como "fetch failed"; esto extrae la causa concreta (ECONNREFUSED, timeout, TLS, etc.).
function describirError(e: unknown): string {
  const err = e as { message?: string; cause?: { message?: string; code?: string } };
  const causa = err.cause?.code || err.cause?.message;
  return causa ? `${err.message} (${causa})` : err.message || "error desconocido";
}

export const SEVERIDAD_ORDEN: Record<Severidad, number> = { alto: 0, medio: 1, bajo: 2, info: 3 };
const FETCH_TIMEOUT_MS = 10_000;

// --- Protección básica contra SSRF: no seguir URLs que apunten a redes internas ---
const BLOCKED_HOSTNAMES = new Set(["localhost", "0.0.0.0"]);

function esIpPrivada(ip: string): boolean {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split(".").map(Number);
    return a === 10 || a === 127 || a === 0 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
  }
  if (net.isIPv6(ip)) {
    const l = ip.toLowerCase();
    return l === "::1" || l.startsWith("fe80:") || l.startsWith("fc") || l.startsWith("fd");
  }
  return false;
}

async function validarUrlPublica(rawUrl: string): Promise<URL> {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    throw new AuditError("La URL no es válida.");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new AuditError("Solo se admiten URLs http:// o https://.");
  }
  const hostname = url.hostname.toLowerCase();
  if (BLOCKED_HOSTNAMES.has(hostname)) {
    throw new AuditError("No se permite auditar direcciones locales.");
  }
  if (net.isIP(hostname)) {
    if (esIpPrivada(hostname)) throw new AuditError("No se permiten direcciones IP privadas.");
    return url;
  }
  let direcciones;
  try {
    direcciones = await dns.lookup(hostname, { all: true });
  } catch {
    throw new AuditError("No se pudo resolver el dominio.");
  }
  if (direcciones.length === 0 || direcciones.some((d) => esIpPrivada(d.address))) {
    throw new AuditError("El dominio no apunta a una dirección pública válida.");
  }
  return url;
}

// --- Base de rastreadores/servicios de terceros conocidos ---
const KNOWN_TRACKERS: Record<string, string> = {
  "google-analytics.com": "Google Analytics",
  "googletagmanager.com": "Google Tag Manager",
  "doubleclick.net": "Google Ads / DoubleClick",
  "connect.facebook.net": "Meta Pixel",
  "facebook.com/tr": "Meta Pixel",
  "hotjar.com": "Hotjar",
  "clarity.ms": "Microsoft Clarity",
  "analytics.tiktok.com": "TikTok Pixel",
  "px.ads.linkedin.com": "LinkedIn Insight",
  "criteo.com": "Criteo",
  "adsrvr.org": "The Trade Desk",
  "mixpanel.com": "Mixpanel",
  "segment.io": "Segment",
  "hs-scripts.com": "HubSpot",
  "hsforms.com": "HubSpot Forms",
  "widget.intercom.io": "Intercom",
  "amplitude.com": "Amplitude",
};

const PRIVACY_LINK_PATTERN =
  /pol[ií]tica.{0,3}(de)?.{0,3}privacidad|aviso.{0,3}de.{0,3}privacidad|tratamiento.{0,3}de.{0,3}datos|protecci[oó]n.{0,3}de.{0,3}datos|privacy.{0,3}policy/i;

const PII_INPUT_TYPES = new Set(["email", "tel", "password"]);
const PII_NAME_HINTS =
  /cedula|c[eé]dula|dni|pasaporte|direcci[oó]n|tel[eé]fono|telefono|nombre|apellido|fecha.?nac|tarjeta|cvv|rfc|ruc/i;

const LOPDP_KEYWORDS: Record<string, string> = {
  "responsable del tratamiento": "identificación del responsable del tratamiento",
  "derechos arco": "mención de derechos ARCO (Acceso, Rectificación, Cancelación, Oposición)",
  consentimiento: "base de consentimiento del titular de los datos",
  "transferencia internacional": "tratamiento de transferencias internacionales de datos",
  finalidad: "finalidad del tratamiento de los datos",
  conservaci: "plazo o criterio de conservación de los datos",
};

function nuevoResultado(url: string): ResultadoAuditoria {
  return { url, fecha: new Date().toISOString(), hallazgos: [] };
}

function agregar(r: ResultadoAuditoria, categoria: string, severidad: Severidad, descripcion: string) {
  r.hallazgos.push({ categoria, severidad, descripcion });
}

async function fetchConTimeout(url: string, timeoutMs = FETCH_TIMEOUT_MS): Promise<Response> {
  return fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; AuditorProteccionDatos/1.0)" },
    redirect: "follow",
    signal: AbortSignal.timeout(timeoutMs),
  });
}

// Node rechaza por defecto certificados con una cadena incompleta o no verificable
// (código UNABLE_TO_VERIFY_LEAF_SIGNATURE y similares), algo frecuente en sitios reales
// que los navegadores toleran igual. Si la carga falla por eso, reintentamos una sola vez
// sin validar la cadena, para poder seguir analizando el sitio; el problema del certificado
// se reporta aparte en revisarCertificado().
const CODIGOS_ERROR_TLS = new Set([
  "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
  "UNABLE_TO_GET_ISSUER_CERT",
  "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
  "SELF_SIGNED_CERT_IN_CHAIN",
  "DEPTH_ZERO_SELF_SIGNED_CERT",
  "CERT_HAS_EXPIRED",
  "ERR_TLS_CERT_ALTNAME_INVALID",
]);

const agenteTlsRelajado = new Agent({ connect: { rejectUnauthorized: false } });

async function fetchConReintentoTls(url: string, timeoutMs = FETCH_TIMEOUT_MS): Promise<Response> {
  try {
    return await fetchConTimeout(url, timeoutMs);
  } catch (e) {
    const codigo = (e as { cause?: { code?: string } })?.cause?.code;
    if (!codigo || !CODIGOS_ERROR_TLS.has(codigo)) throw e;
    // Node's global fetch validates `dispatcher` against its own internal undici
    // instance, so an Agent from the npm `undici` package is rejected (UND_ERR_INVALID_ARG).
    // Using undici's own fetch() alongside its own Agent keeps them matched.
    const resp = await fetchUndici(url, {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; AuditorProteccionDatos/1.0)" },
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
      dispatcher: agenteTlsRelajado,
    });
    return resp as unknown as Response;
  }
}

function revisarHttps(finalUrl: string, r: ResultadoAuditoria) {
  if (!finalUrl.startsWith("https://")) {
    agregar(
      r,
      "Cifrado en tránsito",
      "alto",
      "El sitio se sirve sin HTTPS. Los datos personales enviados por los usuarios " +
        "(formularios, cookies de sesión) viajan sin cifrar."
    );
  } else {
    agregar(r, "Cifrado en tránsito", "info", "El sitio usa HTTPS.");
  }
}

function revisarCertificado(
  hostname: string,
  puerto: number,
  esHttps: boolean,
  r: ResultadoAuditoria
): Promise<void> {
  if (!esHttps) {
    agregar(r, "Certificado TLS", "medio", "No aplica: el sitio no usa HTTPS.");
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    // rejectUnauthorized:false porque aquí solo queremos inspeccionar el certificado, no
    // decidir si confiar en la conexión; socket.authorized indica si la cadena es válida.
    const socket = tls.connect(
      { host: hostname, port: puerto, servername: hostname, timeout: 8000, rejectUnauthorized: false },
      () => {
        const cert = socket.getPeerCertificate();
        const cadenaValida = socket.authorized;
        const errorCadena = socket.authorizationError;
        socket.end();

        if (!cert || !cert.valid_to) {
          agregar(r, "Certificado TLS", "medio", "No se pudieron obtener los detalles del certificado TLS.");
          return resolve();
        }

        if (!cadenaValida) {
          agregar(
            r,
            "Certificado TLS",
            "alto",
            `La cadena de certificados no se pudo validar (${errorCadena}). El sitio probablemente no está ` +
              "enviando los certificados intermedios necesarios. Algunos navegadores lo toleran (usan una " +
              "copia propia del intermedio), pero otros mostrarán una advertencia de seguridad a los usuarios."
          );
        }

        const expira = new Date(cert.valid_to);
        const diasRestantes = Math.floor((expira.getTime() - Date.now()) / 86_400_000);
        if (diasRestantes < 0) {
          agregar(r, "Certificado TLS", "alto", "El certificado TLS está vencido.");
        } else if (diasRestantes < 15) {
          agregar(r, "Certificado TLS", "medio", `El certificado TLS vence en ${diasRestantes} días.`);
        } else if (cadenaValida) {
          agregar(
            r,
            "Certificado TLS",
            "info",
            `Certificado válido, emitido por ${cert.issuer?.O ?? cert.issuer?.CN ?? "desconocido"}, vence en ${diasRestantes} días.`
          );
        } else {
          agregar(r, "Certificado TLS", "info", `El certificado (cadena no válida) vence en ${diasRestantes} días.`);
        }
        resolve();
      }
    );
    socket.on("error", () => {
      agregar(r, "Certificado TLS", "medio", "No se pudo negociar la conexión TLS para revisar el certificado.");
      resolve();
    });
    socket.on("timeout", () => {
      socket.destroy();
      agregar(r, "Certificado TLS", "medio", "Tiempo de espera agotado al revisar el certificado TLS.");
      resolve();
    });
  });
}

const SECURITY_HEADERS: Record<string, [Severidad, string]> = {
  "strict-transport-security": [
    "medio",
    "Falta la cabecera Strict-Transport-Security (HSTS): el navegador no fuerza HTTPS en " +
      "visitas futuras, permitiendo ataques de downgrade.",
  ],
  "content-security-policy": [
    "medio",
    "Falta Content-Security-Policy: sin esta cabecera es más fácil que un script inyectado " +
      "(XSS) exfiltre datos personales del usuario.",
  ],
  "x-content-type-options": ["bajo", "Falta X-Content-Type-Options: nosniff."],
  "referrer-policy": [
    "bajo",
    "Falta Referrer-Policy: la URL completa (que puede incluir datos personales en query " +
      "params) puede filtrarse a sitios de terceros vía la cabecera Referer.",
  ],
};

function revisarCabeceras(headers: Headers, r: ResultadoAuditoria) {
  const presentes: string[] = [];
  for (const [header, [severidad, descripcion]] of Object.entries(SECURITY_HEADERS)) {
    if (headers.get(header)) {
      presentes.push(header);
    } else {
      agregar(r, "Cabeceras de seguridad", severidad, descripcion);
    }
  }
  if (presentes.length > 0) {
    agregar(r, "Cabeceras de seguridad", "info", `Cabeceras presentes: ${presentes.join(", ")}.`);
  }
}

interface CookieInfo {
  nombre: string;
  dominio: string;
  secure: boolean;
}

function parsearSetCookie(valores: string[], hostnameSolicitado: string): CookieInfo[] {
  return valores.map((valor) => {
    const partes = valor.split(";").map((p) => p.trim());
    const [nombre] = partes[0].split("=");
    const secure = partes.some((p) => p.toLowerCase() === "secure");
    const dominioAttr = partes.find((p) => p.toLowerCase().startsWith("domain="));
    const dominio = dominioAttr ? dominioAttr.split("=")[1].replace(/^\./, "") : hostnameSolicitado;
    return { nombre, dominio, secure };
  });
}

function revisarCookies(headers: Headers, hostname: string, r: ResultadoAuditoria) {
  const crudas: string[] =
    typeof (headers as unknown as { getSetCookie?: () => string[] }).getSetCookie === "function"
      ? (headers as unknown as { getSetCookie: () => string[] }).getSetCookie()
      : (() => {
          const single = headers.get("set-cookie");
          return single ? [single] : [];
        })();

  if (crudas.length === 0) {
    agregar(r, "Cookies", "info", "No se detectaron cookies en la respuesta inicial del servidor.");
    return;
  }

  const cookies = parsearSetCookie(crudas, hostname);
  const terceros = cookies.filter((c) => c.dominio !== hostname && !hostname.endsWith("." + c.dominio) && !c.dominio.endsWith("." + hostname));
  const inseguras = cookies.filter((c) => !c.secure);

  agregar(
    r,
    "Cookies",
    "info",
    `El servidor estableció ${cookies.length} cookie(s) en la respuesta inicial ` +
      `(${cookies.length - terceros.length} propias, ${terceros.length} de terceros).`
  );

  if (terceros.length > 0) {
    agregar(
      r,
      "Cookies",
      "medio",
      "Cookies de terceros detectadas en dominios: " +
        [...new Set(terceros.map((c) => c.dominio))].join(", ") +
        ". Requieren informar al usuario y, salvo excepción legal, contar con su consentimiento."
    );
  }

  if (inseguras.length > 0) {
    agregar(
      r,
      "Cookies",
      "medio",
      `${inseguras.length} cookie(s) sin el flag Secure (${inseguras.map((c) => c.nombre).slice(0, 8).join(", ")}).`
    );
  }

  agregar(
    r,
    "Cookies",
    "info",
    "Nota: solo se analizan las cookies enviadas en la respuesta HTML inicial; cookies " +
      "establecidas luego por JavaScript (ej. vía un gestor de etiquetas) no se detectan en esta versión."
  );
}

function revisarRastreadores(html: string, r: ResultadoAuditoria) {
  const detectados = new Map<string, string>();
  for (const [fragmento, nombre] of Object.entries(KNOWN_TRACKERS)) {
    if (html.includes(fragmento)) {
      detectados.set(nombre, fragmento);
    }
  }

  if (detectados.size === 0) {
    agregar(r, "Rastreadores de terceros", "info", "No se detectaron rastreadores de terceros conocidos en la lista base.");
    return;
  }

  for (const [nombre, fragmento] of detectados) {
    agregar(
      r,
      "Rastreadores de terceros",
      "medio",
      `Se detectó ${nombre} (${fragmento}). Debe estar declarado en la política de privacidad y, ` +
        "si no es estrictamente necesario para el servicio, requiere consentimiento previo del usuario."
    );
  }
}

function revisarFormularios($: cheerio.CheerioAPI, r: ResultadoAuditoria) {
  const forms = $("form");
  if (forms.length === 0) {
    agregar(r, "Formularios", "info", "No se encontraron formularios en la página.");
    return;
  }

  forms.each((i, form) => {
    const $form = $(form);
    const camposPii: string[] = [];

    $form.find("input, textarea, select").each((_, el) => {
      const $el = $(el);
      const tipo = ($el.attr("type") || "text").toLowerCase();
      const etiqueta = [$el.attr("name"), $el.attr("id"), $el.attr("placeholder")].filter(Boolean).join(" ");
      if (PII_INPUT_TYPES.has(tipo) || PII_NAME_HINTS.test(etiqueta)) {
        camposPii.push(etiqueta || tipo);
      }
    });

    if (camposPii.length === 0) return;

    const action = $form.attr("action") || "";
    const accionHttps = action === "" || action.startsWith("https://") || action.startsWith("/");
    const tieneCheckbox = $form.find('input[type="checkbox"]').length > 0;

    let severidad: Severidad;
    let detalle: string;
    if (!accionHttps) {
      severidad = "alto";
      detalle = "envía los datos a una URL no-HTTPS";
    } else if (!tieneCheckbox) {
      severidad = "medio";
      detalle = "no muestra una casilla de consentimiento junto al envío";
    } else {
      severidad = "bajo";
      detalle = "incluye una casilla de consentimiento";
    }

    agregar(
      r,
      "Formularios",
      severidad,
      `Formulario #${i + 1} recolecta datos personales (${camposPii.slice(0, 5).join(", ")}) y ${detalle}.`
    );
  });
}

async function revisarPoliticaPrivacidad($: cheerio.CheerioAPI, urlBase: string, r: ResultadoAuditoria) {
  let enlace: string | null = null;
  $("a[href]").each((_, a) => {
    if (enlace) return;
    const $a = $(a);
    const texto = $a.text().trim();
    const href = $a.attr("href") || "";
    if (PRIVACY_LINK_PATTERN.test(texto) || PRIVACY_LINK_PATTERN.test(href)) {
      try {
        enlace = new URL(href, urlBase).toString();
      } catch {
        /* href inválido, se ignora */
      }
    }
  });

  if (!enlace) {
    agregar(
      r,
      "Política de privacidad",
      "alto",
      "No se encontró un enlace visible a una política de privacidad o aviso de tratamiento de datos."
    );
    return;
  }

  agregar(r, "Política de privacidad", "info", `Enlace a política de privacidad encontrado: ${enlace}`);

  try {
    const urlValidada = await validarUrlPublica(enlace);
    const resp = await fetchConReintentoTls(urlValidada.toString(), 8000);
    const textoHtml = await resp.text();
    const textoPolitica = cheerio.load(textoHtml)("body").text().toLowerCase();

    const faltantes = Object.entries(LOPDP_KEYWORDS)
      .filter(([palabraClave]) => !textoPolitica.includes(palabraClave))
      .map(([, requisito]) => requisito);

    if (faltantes.length > 0) {
      agregar(
        r,
        "Política de privacidad",
        "medio",
        `La política de privacidad no menciona explícitamente: ${faltantes.join("; ")}.`
      );
    } else {
      agregar(
        r,
        "Política de privacidad",
        "info",
        "La política de privacidad cubre los elementos clave revisados (responsable, derechos ARCO, consentimiento, finalidad, conservación)."
      );
    }
  } catch (e) {
    agregar(
      r,
      "Política de privacidad",
      "bajo",
      `No se pudo descargar la política de privacidad para revisar su contenido (${(e as Error).message}).`
    );
  }
}

export async function auditar(rawUrl: string): Promise<ResultadoAuditoria> {
  const urlValidada = await validarUrlPublica(rawUrl.startsWith("http") ? rawUrl : `https://${rawUrl}`);

  let resp: Response;
  try {
    resp = await fetchConReintentoTls(urlValidada.toString());
  } catch (e) {
    throw new AuditError(`No se pudo cargar el sitio: ${describirError(e)}`);
  }

  const html = await resp.text();
  const finalUrl = resp.url || urlValidada.toString();
  const urlFinalParseada = new URL(finalUrl);
  const hostname = urlFinalParseada.hostname;
  const puerto = urlFinalParseada.port ? Number(urlFinalParseada.port) : 443;
  const esHttps = finalUrl.startsWith("https://");

  const r = nuevoResultado(finalUrl);
  const $ = cheerio.load(html);

  revisarHttps(finalUrl, r);
  await revisarCertificado(hostname, puerto, esHttps, r);
  revisarCabeceras(resp.headers, r);
  revisarCookies(resp.headers, hostname, r);
  revisarRastreadores(html, r);
  revisarFormularios($, r);
  await revisarPoliticaPrivacidad($, finalUrl, r);

  return r;
}
