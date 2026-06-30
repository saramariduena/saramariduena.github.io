import type { Rank, SaveProfile } from './types';

// Carrera por rangos: el rango se deriva de los casos ganados (no se persiste,
// se calcula). Cada rango da más "Preparación" (recurso) y bono de convicción.

export function rankIndex(ranks: Rank[], profile: SaveProfile): number {
  const won = profile.casesWon.length;
  let idx = 0;
  for (let i = 0; i < ranks.length; i++) {
    if (won >= ranks[i].min) idx = i;
  }
  return idx;
}

export function rankName(ranks: Rank[], idx: number, gender: 'f' | 'm'): string {
  const r = ranks[idx];
  if (!r) return 'Pasante';
  return gender === 'f' ? r.f : r.m;
}

/** Casos ganados necesarios para el siguiente rango (o null si es el máximo). */
export function nextRankNeed(ranks: Rank[], profile: SaveProfile): { name: string; need: number } | null {
  const idx = rankIndex(ranks, profile);
  const next = ranks[idx + 1];
  if (!next) return null;
  return { name: gendered(next, profile.gender), need: next.min - profile.casesWon.length };
}

function gendered(r: Rank, gender: 'f' | 'm'): string {
  return gender === 'f' ? r.f : r.m;
}

const DIFFICULTY_TIER: Record<string, number> = {
  Básico: 0,
  Intermedio: 1,
  Avanzado: 2,
  Experto: 3,
};

export function requiredTier(dificultad: string): number {
  return DIFFICULTY_TIER[dificultad] ?? 0;
}

/** Puntos de Preparación (recurso) que da el rango actual. */
export function prepPoints(tier: number): number {
  return 2 + tier;
}

/** Bono de convicción inicial por rango. */
export function convictionBonus(tier: number): number {
  return tier * 2;
}
