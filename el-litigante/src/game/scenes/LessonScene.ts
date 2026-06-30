import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { grantXp } from '../../core/rpg';
import { evaluateAchievements } from '../../core/achievements';
import type { Lesson, Palette } from '../../core/types';
import { makeButton, theme, fs } from '../ui/widgets';

interface LessonInit {
  lessonId: string;
  palette: Palette;
  unlocked: string[];
  next: { action: string; worldId?: string; index?: number; isBoss?: boolean };
}

export class LessonScene extends Phaser.Scene {
  private initData!: LessonInit;
  private lesson!: Lesson;
  private answered = false;
  private retriesLeft = 0;

  constructor() {
    super('Lesson');
  }

  init(data: LessonInit) {
    this.initData = data;
    this.lesson = store.content.lessons[data.lessonId] || store.content.lessons['principios'];
  }

  create() {
    const t = theme();
    this.cameras.main.setBackgroundColor(t.bg);
    const accent = Phaser.Display.Color.HexStringToColor(this.initData.palette.accent).color;

    this.add.text(GAME_WIDTH / 2, 30, '¿Qué aprendiste?', { fontFamily: 'Georgia, serif', fontSize: fs(34), color: t.text, fontStyle: 'bold' }).setOrigin(0.5, 0);

    // --- Columna izquierda: la lección ---
    const lx = 40;
    this.add.rectangle(lx, 90, 620, 600, t.panel, 1).setOrigin(0, 0).setStrokeStyle(2, accent);
    let y = 104;
    const pad = (txt: string, size: number, color: string, bold = false) => {
      const o = this.add.text(lx + 18, y, txt, {
        fontFamily: 'Segoe UI, sans-serif',
        fontSize: fs(size),
        color,
        fontStyle: bold ? 'bold' : 'normal',
        wordWrap: { width: 584 },
        lineSpacing: 3,
      });
      y += o.height + 8;
      return o;
    };
    pad(this.lesson.titulo, 22, t.text, true);
    pad(this.lesson.explicacion, 15, t.text);
    pad('📜 ' + this.lesson.articulo, 14, '#f5d547', true);
    pad('Resumen: ' + this.lesson.resumen, 14, t.textDim);
    pad('Ejemplo: ' + this.lesson.ejemplo, 14, t.textDim);
    pad('💡 Consejo: ' + this.lesson.consejo, 14, t.text, true);

    // --- Columna derecha: trivia ---
    const rx = 700;
    this.add.rectangle(rx, 90, 540, 470, t.panel, 1).setOrigin(0, 0).setStrokeStyle(2, accent);
    this.add.text(rx + 18, 104, '🧑‍⚖️ Doctor Iuris pregunta:', { fontFamily: 'Segoe UI', fontSize: fs(16), color: '#f5d547', fontStyle: 'bold' });
    this.add.text(rx + 18, 138, this.lesson.trivia.pregunta, { fontFamily: 'Segoe UI', fontSize: fs(18), color: t.text, fontStyle: 'bold', wordWrap: { width: 500 } }).setOrigin(0, 0);

    this.retriesLeft = this.skillRetries();
    const feedback = this.add.text(rx + 18, 470, '', { fontFamily: 'Segoe UI', fontSize: fs(18), color: t.text, fontStyle: 'bold', wordWrap: { width: 500 } });

    this.lesson.trivia.opciones.forEach((opt, i) => {
      const btn = makeButton(this, rx + 270, 230 + i * 56, opt, () => this.answer(i, btn, feedback), { width: 500, height: 46, fontSize: 16 });
    });

    // Logros desbloqueados.
    if (this.initData.unlocked.length) {
      this.add.text(rx + 18, 520, '🏆 ' + this.initData.unlocked.slice(0, 3).join(' · '), { fontFamily: 'Segoe UI', fontSize: fs(14), color: '#f5d547', wordWrap: { width: 500 } });
    }

    // Botón continuar (aparece tras responder).
    this.continueBtn = makeButton(this, GAME_WIDTH / 2, GAME_HEIGHT - 40, 'Continuar ▶', () => this.proceed(), { width: 320, height: 56, primary: true });
    this.continueBtn.setAlpha(0.4);
  }

  private continueBtn!: Phaser.GameObjects.Container;

  private skillRetries(): number {
    let r = 0;
    for (const s of store.content.skills) if (s.effect === 'triviaRetry') r += (store.active!.skills[s.id] || 0) * s.perLevel;
    return r;
  }

  private answer(i: number, btn: Phaser.GameObjects.Container, feedback: Phaser.GameObjects.Text) {
    if (this.answered) return;
    const correct = i === this.lesson.trivia.correcta;
    if (correct) {
      this.answered = true;
      const a = store.active!;
      a.stats.trivia += 1;
      a.lex += 5;
      const diff = store.content.difficulties.find((d) => d.id === a.difficulty);
      grantXp(a, 20 * (diff?.xpMul || 1));
      const unlocked = evaluateAchievements(a, store.content);
      store.persistProfiles();
      feedback.setColor('#3ad07a').setText('¡Correcto! +5 LEX, +XP' + (unlocked.length ? '  🏆 ' + unlocked[0].name : ''));
      (btn.list[0] as Phaser.GameObjects.Rectangle).setFillStyle(0x2e8b57);
      this.enableContinue();
    } else if (this.retriesLeft > 0) {
      this.retriesLeft -= 1;
      feedback.setColor('#f5a623').setText('No es correcta. Te queda ' + this.retriesLeft + ' reintento (habilidad Persuasión).');
      (btn.list[0] as Phaser.GameObjects.Rectangle).setFillStyle(0x8a4b1f);
    } else {
      this.answered = true;
      const right = this.lesson.trivia.opciones[this.lesson.trivia.correcta];
      feedback.setColor('#ff6b6b').setText('La respuesta correcta era: «' + right + '».');
      (btn.list[0] as Phaser.GameObjects.Rectangle).setFillStyle(0x922b21);
      this.enableContinue();
    }
  }

  private enableContinue() {
    this.continueBtn.setAlpha(1);
    this.tweens.add({ targets: this.continueBtn, scale: { from: 0.95, to: 1.05 }, duration: 500, yoyo: true, repeat: -1 });
  }

  private proceed() {
    if (!this.answered) return;
    const n = this.initData.next;
    if (n.action === 'level') this.scene.start('Level', { worldId: n.worldId, index: n.index, isBoss: n.isBoss });
    else if (n.action === 'worldselect') this.scene.start('WorldSelect');
    else this.scene.start('Menu');
  }
}
