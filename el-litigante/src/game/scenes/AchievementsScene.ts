import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

const PER_PAGE = 9;

export class AchievementsScene extends Phaser.Scene {
  private page = 0;
  private listLayer!: Phaser.GameObjects.Container;

  constructor() {
    super('Achievements');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    const all = store.content.achievements;
    const profile = store.active;
    const unlocked = profile ? profile.achievements.length : 0;

    title(this, cx, 50, 'Logros', 40);
    label(this, cx, 92, `${unlocked} / ${all.length} desbloqueados`, 20, true);

    this.listLayer = this.add.container(0, 0);
    this.renderPage();

    makeButton(this, cx - 220, GAME_HEIGHT - 44, '◀ Anterior', () => {
      this.page = Math.max(0, this.page - 1);
      this.renderPage();
    }, { width: 200, height: 50 });
    makeButton(this, cx + 220, GAME_HEIGHT - 44, 'Siguiente ▶', () => {
      const max = Math.ceil(all.length / PER_PAGE) - 1;
      this.page = Math.min(max, this.page + 1);
      this.renderPage();
    }, { width: 200, height: 50 });
    makeButton(this, cx, GAME_HEIGHT - 44, 'Menú', () => this.scene.start('Menu'), { width: 160, height: 50 });
  }

  private renderPage() {
    this.listLayer.removeAll(true);
    const t = theme();
    const all = store.content.achievements;
    const profile = store.active;
    const start = this.page * PER_PAGE;
    const slice = all.slice(start, start + PER_PAGE);
    const maxPage = Math.ceil(all.length / PER_PAGE);

    slice.forEach((a, i) => {
      const y = 130 + i * 56;
      const has = profile ? profile.achievements.includes(a.id) : false;
      const bg = this.add.rectangle(GAME_WIDTH / 2, y, 980, 50, has ? 0x1f5132 : t.panel, 1).setStrokeStyle(2, has ? 0xf5d547 : 0x000000, has ? 1 : 0.15);
      const icon = this.add.text(GAME_WIDTH / 2 - 470, y, has ? '🏆' : '🔒', { fontSize: fs(22) }).setOrigin(0, 0.5);
      const name = this.add.text(GAME_WIDTH / 2 - 430, y - 12, a.name, { fontFamily: 'Segoe UI', fontSize: fs(17), color: t.text, fontStyle: 'bold' });
      const desc = this.add.text(GAME_WIDTH / 2 - 430, y + 8, a.desc, { fontFamily: 'Segoe UI', fontSize: fs(13), color: t.textDim });
      this.listLayer.add([bg, icon, name, desc]);
    });

    const pageInfo = this.add.text(GAME_WIDTH / 2, 108, `Página ${this.page + 1} / ${maxPage}`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: t.textDim }).setOrigin(0.5);
    this.listLayer.add(pageInfo);
  }
}
