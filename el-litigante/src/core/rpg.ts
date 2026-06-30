import type { SaveProfile, Content } from './types';

// Sistema RPG: experiencia, nivel de personaje y efectos de habilidades.

/** XP acumulada necesaria para alcanzar cierto nivel. Curva creciente suave. */
export function xpForLevel(level: number): number {
  // Nivel 1 = 0 XP; cada nivel cuesta 150*(n-1).
  let total = 0;
  for (let i = 2; i <= level; i++) total += 150 * (i - 1);
  return total;
}

export function levelFromXp(xp: number): number {
  let lvl = 1;
  while (xp >= xpForLevel(lvl + 1)) lvl++;
  return lvl;
}

/** Añade XP, recalcula el nivel y devuelve cuántos niveles subió. */
export function grantXp(profile: SaveProfile, amount: number): number {
  const before = profile.charLevel;
  profile.xp += Math.max(0, Math.round(amount));
  profile.charLevel = levelFromXp(profile.xp);
  return profile.charLevel - before;
}

/** Valor total de un efecto de habilidad para el perfil. */
export function skillEffect(profile: SaveProfile, content: Content, effect: string): number {
  let value = 0;
  for (const skill of content.skills) {
    if (skill.effect !== effect) continue;
    const lvl = profile.skills[skill.id] || 0;
    value += lvl * skill.perLevel;
  }
  return value;
}

/** Sube una habilidad si hay LEX suficiente y no está al máximo. */
export function upgradeSkill(profile: SaveProfile, content: Content, skillId: string): boolean {
  const skill = content.skills.find((s) => s.id === skillId);
  if (!skill) return false;
  const current = profile.skills[skillId] || 0;
  if (current >= skill.maxLevel) return false;
  const price = skill.cost * (current + 1);
  if (profile.lex < price) return false;
  profile.lex -= price;
  profile.skills[skillId] = current + 1;
  return true;
}

export function skillPrice(profile: SaveProfile, content: Content, skillId: string): number {
  const skill = content.skills.find((s) => s.id === skillId)!;
  const current = profile.skills[skillId] || 0;
  return skill.cost * (current + 1);
}
