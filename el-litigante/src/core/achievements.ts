import type { Achievement, Content, SaveProfile } from './types';

// Evalúa todas las condiciones de logros contra el estado acumulado del
// perfil. Es idempotente: se puede llamar tras cualquier cambio y solo
// devuelve los logros recién desbloqueados.

function isMet(a: Achievement, p: SaveProfile, content: Content): boolean {
  const { type, value } = a.condition;
  switch (type) {
    case 'levels':
      return p.levelsCompleted.length >= value;
    case 'lex':
      return p.lex >= value;
    case 'documents':
      return p.stats.documents >= value;
    case 'enemies':
      return p.stats.enemies >= value;
    case 'trivia':
      return p.stats.trivia >= value;
    case 'perfectLevels':
      return p.stats.perfectLevels >= value;
    case 'minutes':
      return p.stats.minutes >= value;
    case 'sessions':
      return p.stats.sessions >= value;
    case 'bossPerfect':
      return p.stats.bossPerfect >= value;
    case 'charLevel':
      return p.charLevel >= value;
    case 'worldComplete':
      return p.worldsCompleted.includes(value);
    case 'worldsComplete':
      return (value as string[]).every((w) => p.worldsCompleted.includes(w));
    case 'bossDefeat':
      return p.bossesDefeated.includes(value);
    case 'lessonRead':
      return p.lessonsRead.includes(value);
    case 'difficultyWorld':
      return p.difficultyWorldsDone.includes(value);
    case 'skillUp':
      return (p.skills[value] || 0) > 0;
    case 'skillsMaxed':
      return content.skills.every((s) => (p.skills[s.id] || 0) >= s.maxLevel);
    default:
      return false;
  }
}

export function evaluateAchievements(p: SaveProfile, content: Content): Achievement[] {
  const unlocked: Achievement[] = [];
  for (const a of content.achievements) {
    if (p.achievements.includes(a.id)) continue;
    if (isMet(a, p, content)) {
      p.achievements.push(a.id);
      unlocked.push(a);
    }
  }
  return unlocked;
}
