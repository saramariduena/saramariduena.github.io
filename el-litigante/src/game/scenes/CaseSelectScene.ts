import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { makeButton, title, label, paintBackground, theme, fs } from '../ui/widgets';

export class CaseSelectScene extends Phaser.Scene {
  constructor() {
    super('CaseSelect');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    const profile = store.ensureProfile();
    title(this, cx, 56, 'Elige tu caso', 42);
    label(this, cx, 98, 'Eres abogado. Lleva el caso por las etapas del COGEP y gana la audiencia.', 17, true);

    const t = theme();
    const cases = store.content.cases;
    const cardW = 1040;
    const cardH = 118;
    let y = 168;

    cases.forEach((c) => {
      const won = profile.casesWon.includes(c.id);
      this.add.rectangle(cx, y, cardW, cardH, t.panel, 1).setStrokeStyle(2, won ? 0xf5d547 : 0x000000, won ? 1 : 0.18);
      this.add.text(cx - cardW / 2 + 24, y - 40, c.titulo, { fontFamily: 'Georgia, serif', fontSize: fs(24), color: t.text, fontStyle: 'bold' });
      this.add.text(cx - cardW / 2 + 24, y - 8, `${c.materia}  ·  ${c.rol}  ·  Dificultad: ${c.dificultad}`, { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' });
      this.add.text(cx - cardW / 2 + 24, y + 16, c.resumen, { fontFamily: 'Segoe UI', fontSize: fs(14), color: t.textDim, wordWrap: { width: 720 } });
      if (won) this.add.text(cx - cardW / 2 + 24, y - 40, '', {});
      this.add.text(cx + cardW / 2 - 150, y - 44, won ? '★ Ganado' : '', { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547' });

      makeButton(this, cx + cardW / 2 - 110, y + 16, '⚖️ Litigar', () => this.scene.start('Audiencia', { caseId: c.id }), {
        width: 180,
        height: 56,
        primary: true,
      });
      y += cardH + 16;
    });

    makeButton(this, cx, GAME_HEIGHT - 44, 'Volver al menú', () => this.scene.start('Menu'), { width: 260, height: 52 });
  }
}
