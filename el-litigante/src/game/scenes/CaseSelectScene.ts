import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { rankIndex, rankName, requiredTier } from '../../core/ranks';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

const PER_PAGE = 4;

export class CaseSelectScene extends Phaser.Scene {
  private page = 0;
  private listLayer!: Phaser.GameObjects.Container;

  constructor() {
    super('CaseSelect');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    const profile = store.ensureProfile();
    const tier = rankIndex(store.content.ranks, profile);
    const rIcon = store.content.ranks[tier].icon;
    title(this, cx, 44, 'Elige tu caso', 38);
    label(this, cx, 84, `${rIcon} ${rankName(store.content.ranks, tier, profile.gender)}  ·  Gana casos para ascender y desbloquear casos más difíciles.`, 16, true);

    this.listLayer = this.add.container(0, 0);
    this.renderPage();

    const total = Math.ceil(store.content.cases.length / PER_PAGE);
    makeButton(this, cx - 240, GAME_HEIGHT - 40, '◀ Anterior', () => {
      this.page = (this.page - 1 + total) % total;
      this.renderPage();
    }, { width: 210, height: 50 });
    makeButton(this, cx + 240, GAME_HEIGHT - 40, 'Siguiente ▶', () => {
      this.page = (this.page + 1) % total;
      this.renderPage();
    }, { width: 210, height: 50 });
    makeButton(this, cx, GAME_HEIGHT - 40, 'Menú', () => this.scene.start('Menu'), { width: 180, height: 50 });
  }

  private renderPage() {
    this.listLayer.removeAll(true);
    const cx = GAME_WIDTH / 2;
    const t = theme();
    const profile = store.active!;
    const cases = store.content.cases;
    const total = Math.ceil(cases.length / PER_PAGE);
    const start = this.page * PER_PAGE;
    const slice = cases.slice(start, start + PER_PAGE);

    const playerTier = rankIndex(store.content.ranks, profile);
    const cardW = 1060;
    const cardH = 110;
    let y = 162;

    slice.forEach((c) => {
      const won = profile.casesWon.includes(c.id);
      const reqTier = requiredTier(c.dificultad);
      const locked = playerTier < reqTier;
      this.listLayer.add(this.add.rectangle(cx, y, cardW, cardH, t.panel, locked ? 0.6 : 0.96).setStrokeStyle(2, won ? 0xf5d547 : 0x000000, won ? 1 : 0.18));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y - 38, (locked ? '🔒 ' : '') + c.titulo, { fontFamily: 'Georgia, serif', fontSize: fs(23), color: locked ? t.textDim : t.text, fontStyle: 'bold' }));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y - 6, `${c.materia}  ·  ${c.rol}  ·  ${c.dificultad}`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' }));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y + 18, c.resumen, { fontFamily: 'Segoe UI', fontSize: fs(13), color: t.textDim, wordWrap: { width: 740 } }));
      if (won) this.listLayer.add(this.add.text(cx + cardW / 2 - 250, y - 40, '★ Ganado', { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' }));

      if (locked) {
        this.listLayer.add(this.add.text(cx + cardW / 2 - 120, y + 6, `Requiere:\n${rankName(store.content.ranks, reqTier, profile.gender)}`, { fontFamily: 'Segoe UI', fontSize: fs(13), color: '#9fb3d1', align: 'center' }).setOrigin(0.5));
      } else {
        this.listLayer.add(makeButton(this, cx + cardW / 2 - 120, y + 6, '⚖️ Litigar', () => this.scene.start('Audiencia', { caseId: c.id }), { width: 190, height: 54, primary: true }));
      }
      y += cardH + 12;
    });

    this.listLayer.add(this.add.text(cx, 118, `Página ${this.page + 1} / ${total}  ·  ${cases.length} casos`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: t.textDim }).setOrigin(0.5));
  }
}
