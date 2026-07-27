import { NextRequest, NextResponse } from "next/server";
import { AuditError, auditar } from "@/lib/audit";

export const runtime = "nodejs";
export const maxDuration = 30;

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Cuerpo de solicitud inválido." }, { status: 400 });
  }

  const url = (body as { url?: unknown })?.url;
  if (typeof url !== "string" || url.trim().length === 0) {
    return NextResponse.json({ error: "Debes indicar una URL." }, { status: 400 });
  }

  try {
    const resultado = await auditar(url.trim());
    return NextResponse.json(resultado);
  } catch (e) {
    if (e instanceof AuditError) {
      return NextResponse.json({ error: e.message }, { status: 400 });
    }
    console.error(e);
    return NextResponse.json({ error: "Ocurrió un error inesperado al auditar el sitio." }, { status: 500 });
  }
}
