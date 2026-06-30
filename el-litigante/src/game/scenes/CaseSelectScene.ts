import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
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
    store.ensureProfile();
    title(this, cx, 48, 'Elige tu caso', 40);
    label(this, cx, 88, 'Eres abogado/a. Lleva el caso por las etapas del COGEP y gana la audiencia.', 16, true);

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

    const cardW = 1060;
    const cardH = 110;
    let y = 162;

    slice.forEach((c) => {
      const won = profile.casesWon.includes(c.id);
      this.listLayer.add(this.add.rectangle(cx, y, cardW, cardH, t.panel, 0.96).setStrokeStyle(2, won ? 0xf5d547 : 0x000000, won ? 1 : 0.18));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y - 38, c.titulo, { fontFamily: 'Georgia, serif', fontSize: fs(23), color: t.text, fontStyle: 'bold' }));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y - 6, `${c.materia}  ·  ${c.rol}  ·  ${c.dificultad}`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' }));
      this.listLayer.add(this.add.text(cx - cardW / 2 + 24, y + 18, c.resumen, { fontFamily: 'Segoe UI', fontSize: fs(13), color: t.textDim, wordWrap: { width: 740 } }));
      if (won) this.listLayer.add(this.add.text(cx + cardW / 2 - 250, y - 40, '★ Ganado', { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' }));
      this.listLayer.add(makeButton(this, cx + cardW / 2 - 120, y + 6, '⚖️ Litigar', () => this.scene.start('Audiencia', { caseId: c.id }), { width: 190, height: 54, primary: true }));
      y += cardH + 12;
    });

    this.listLayer.add(this.add.text(cx, 118, `Página ${this.page + 1} / ${total}  ·  ${cases.length} casos`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: t.textDim }).setOrigin(0.5));
  }
}
