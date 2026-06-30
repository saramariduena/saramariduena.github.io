import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { upgradeSkill, skillPrice, xpForLevel } from '../../core/rpg';
import { rankIndex, rankName, nextRankNeed } from '../../core/ranks';
import { evaluateAchievements } from '../../core/achievements';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

export class ProfileScene extends Phaser.Scene {
  private tab: 'stats' | 'skills' | 'ranking' = 'stats';
  private body!: Phaser.GameObjects.Container;

  constructor() {
    super('Profile');
  }

  init(data: { tab?: 'stats' | 'skills' | 'ranking' }) {
    this.tab = data?.tab || 'stats';
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    title(this, cx, 48, 'Perfil del Litigante', 38);

    makeButton(this, cx - 240, 100, 'Estadísticas', () => this.setTab('stats'), { width: 220, height: 46, primary: this.tab === 'stats' });
    makeButton(this, cx, 100, 'Habilidades', () => this.setTab('skills'), { width: 220, height: 46, primary: this.tab === 'skills' });
    makeButton(this, cx + 240, 100, 'Ranking', () => this.setTab('ranking'), { width: 220, height: 46, primary: this.tab === 'ranking' });

    this.body = this.add.container(0, 0);
    this.render();

    makeButton(this, cx, GAME_HEIGHT - 44, 'Volver al menú', () => this.scene.start('Menu'), { width: 260, height: 52 });
  }

  private setTab(tab: 'stats' | 'skills' | 'ranking') {
    this.tab = tab;
    this.scene.restart({ tab });
  }

  private render() {
    if (this.tab === 'stats') this.renderStats();
    else if (this.tab === 'skills') this.renderSkills();
    else this.renderRanking();
  }

  private renderStats() {
    const p = store.active!;
    const t = theme();
    const casesTotal = store.content.cases.length;
    const pct = Math.round((p.casesWon.length / casesTotal) * 100);
    const nextLvl = xpForLevel(p.charLevel + 1);
    const tier = rankIndex(store.content.ranks, p);
    const rk = store.content.ranks[tier];
    const next = nextRankNeed(store.content.ranks, p);
    const lines = [
      `Nombre: ${p.name}`,
      `Rango: ${rk.icon} ${rankName(store.content.ranks, tier, p.gender)}` + (next ? `   ·   Faltan ${Math.max(0, next.need)} caso(s) para ${next.name}` : '   ·   ¡Rango máximo!'),
      `Nivel de personaje: ${p.charLevel}   (XP ${p.xp} / ${nextLvl})`,
      `Monedas LEX: ${p.lex}`,
      `Casos ganados: ${p.casesWon.length} / ${casesTotal}   (${pct}%)`,
      `Decisiones acertadas: ${p.stats.trivia}`,
      `Logros: ${p.achievements.length} / ${store.content.achievements.length}`,
      `Tiempo jugado: ${p.stats.minutes} min`,
    ];
    this.add.rectangle(GAME_WIDTH / 2, 400, 900, 520, t.panel, 1).setStrokeStyle(2, 0xf5d547);
    lines.forEach((l, i) => {
      this.body.add(this.add.text(GAME_WIDTH / 2 - 420, 170 + i * 40, l, { fontFamily: 'Segoe UI', fontSize: fs(20), color: t.text }));
    });
  }

  private renderSkills() {
    const p = store.active!;
    const t = theme();
    this.body.add(this.add.text(GAME_WIDTH / 2, 150, `Tienes ${p.lex} LEX para mejorar habilidades`, { fontFamily: 'Segoe UI', fontSize: fs(20), color: '#f5d547', fontStyle: 'bold' }).setOrigin(0.5));

    store.content.skills.forEach((s, i) => {
      const col = i % 2;
      const rowI = Math.floor(i / 2);
      const x = GAME_WIDTH / 2 + (col === 0 ? -300 : 300);
      const y = 210 + rowI * 110;
      const lvl = p.skills[s.id] || 0;
      const maxed = lvl >= s.maxLevel;
      const price = skillPrice(p, store.content, s.id);
      this.add.rectangle(x, y, 560, 96, t.panel, 1).setStrokeStyle(2, 0x000000, 0.2);
      this.body.add(this.add.text(x - 260, y - 36, `${s.name}  (${lvl}/${s.maxLevel})`, { fontFamily: 'Segoe UI', fontSize: fs(18), color: t.text, fontStyle: 'bold' }));
      this.body.add(this.add.text(x - 260, y - 10, s.desc, { fontFamily: 'Segoe UI', fontSize: fs(13), color: t.textDim, wordWrap: { width: 380 } }));
      const btn = makeButton(this, x + 190, y, maxed ? 'Máx.' : `Mejorar (${price})`, () => {
        if (upgradeSkill(p, store.content, s.id)) {
          evaluateAchievements(p, store.content);
          store.persistProfiles();
          this.scene.restart({ tab: 'skills' });
        }
      }, { width: 180, height: 50, primary: !maxed && p.lex >= price });
      this.body.add(btn);
    });
  }

  private renderRanking() {
    const t = theme();
    const sorted = [...store.profiles].sort((a, b) => b.lex - a.lex || b.charLevel - a.charLevel);
    this.body.add(this.add.text(GAME_WIDTH / 2, 150, 'Ranking local de litigantes (por LEX)', { fontFamily: 'Segoe UI', fontSize: fs(20), color: t.text, fontStyle: 'bold' }).setOrigin(0.5));
    sorted.slice(0, 10).forEach((p, i) => {
      const y = 200 + i * 44;
      const me = p.id === store.activeId;
      this.add.rectangle(GAME_WIDTH / 2, y, 760, 40, me ? 0x1f5132 : t.panel, 1).setStrokeStyle(2, me ? 0xf5d547 : 0x000000, me ? 1 : 0.15);
      this.body.add(this.add.text(GAME_WIDTH / 2 - 360, y, `${i + 1}.`, { fontFamily: 'Segoe UI', fontSize: fs(18), color: t.text, fontStyle: 'bold' }).setOrigin(0, 0.5));
      this.body.add(this.add.text(GAME_WIDTH / 2 - 310, y, p.name, { fontFamily: 'Segoe UI', fontSize: fs(18), color: t.text }).setOrigin(0, 0.5));
      this.body.add(this.add.text(GAME_WIDTH / 2 + 320, y, `${p.lex} LEX · Nv ${p.charLevel}`, { fontFamily: 'Segoe UI', fontSize: fs(16), color: t.textDim }).setOrigin(1, 0.5));
    });
  }
}
