import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { evaluateAchievements } from '../../core/achievements';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, title, label, paintBackground, theme, confirmDialog, fs } from '../ui/widgets';

let sessionCounted = false;

export class MenuScene extends Phaser.Scene {
  constructor() {
    super('Menu');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;

    // Telón de fondo: sala de audiencia atenuada.
    this.add.image(cx, GAME_HEIGHT / 2, SCENE_TEX.sala).setAlpha(0.28).setDepth(0);
    this.add.sprite(cx, GAME_HEIGHT - 4, SCENE_TEX.tu).setOrigin(0.5, 1).setScale(1.3).setAlpha(0.9).setDepth(1);

    const active = store.active;
    if (active && !sessionCounted) {
      sessionCounted = true;
      active.stats.sessions += 1;
      evaluateAchievements(active, store.content);
      store.persistProfiles();
    }

    title(this, cx, 92, 'EL LITIGANTE', 64);
    label(this, cx, 142, 'Simulador de Audiencias — aprende el COGEP litigando casos reales', 20, true);

    const t = theme();
    if (active) {
      this.add.rectangle(cx, 196, 760, 50, t.panel, 0.92).setStrokeStyle(2, t.accent);
      this.add
        .text(cx, 196, `👤 ${active.name}   ·   Nivel ${active.charLevel}   ·   ${active.lex} LEX   ·   Casos ganados: ${active.casesWon.length}`, {
          fontFamily: 'Segoe UI, sans-serif',
          fontSize: fs(19),
          color: t.text,
        })
        .setOrigin(0.5);
    }

    label(this, cx, 242, '🧑‍⚖️ Doctor Iuris: «En la audiencia, quien domina el COGEP, gana. ¡Adelante!»', 16, true);

    const startY = 300;
    const gap = 64;
    makeButton(this, cx, startY, '⚖️  Litigar un caso', () => this.play(), { width: 420, height: 70, primary: true, fontSize: 26 });
    makeButton(this, cx - 190, startY + gap + 16, 'Perfil', () => this.scene.start('Profile'), { width: 360, height: 56 });
    makeButton(this, cx + 190, startY + gap + 16, 'Logros', () => this.scene.start('Achievements'), { width: 360, height: 56 });
    makeButton(this, cx - 190, startY + gap * 2 + 16, 'Configuración', () => this.scene.start('Settings'), { width: 360, height: 56 });
    makeButton(this, cx + 190, startY + gap * 2 + 16, 'Salir del juego', () => this.exitGame(), { width: 360, height: 56, danger: true });

    label(this, cx, GAME_HEIGHT - 24, 'Contenido educativo basado en el COGEP. No sustituye el estudio del texto oficial vigente.', 13, true);
  }

  private play() {
    store.ensureProfile();
    this.scene.start('CaseSelect');
  }

  private exitGame() {
    confirmDialog(this, '¿Deseas abandonar el litigio?', () => {
      window.close();
      this.scene.start('Menu');
      this.time.delayedCall(50, () => {
        paintBackground(this);
        this.add
          .text(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'Gracias por litigar.\nPuedes cerrar esta pestaña cuando quieras.', {
            fontFamily: 'Georgia, serif',
            fontSize: fs(30),
            color: theme().text,
            align: 'center',
          })
          .setOrigin(0.5)
          .setDepth(99999);
      });
    });
  }
}
