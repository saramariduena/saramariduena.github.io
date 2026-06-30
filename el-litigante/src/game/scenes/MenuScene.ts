import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { evaluateAchievements } from '../../core/achievements';
import { makeButton, title, label, paintBackground, theme, confirmDialog, fs } from '../ui/widgets';

let sessionCounted = false;

export class MenuScene extends Phaser.Scene {
  constructor() {
    super('Menu');
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;

    // Cuenta una sesión de juego (para logros) una vez por carga de página.
    const active = store.active;
    if (active && !sessionCounted) {
      sessionCounted = true;
      active.stats.sessions += 1;
      evaluateAchievements(active, store.content);
      store.persistProfiles();
    }

    title(this, cx, 90, 'EL LITIGANTE', 64);
    label(this, cx, 140, 'Conviértete en el mejor litigante del Ecuador — aprende el COGEP', 20, true);

    // Tarjeta de perfil activo.
    const t = theme();
    if (active) {
      this.add.rectangle(cx, 195, 720, 56, t.panel, 1).setStrokeStyle(2, t.accent);
      this.add
        .text(cx, 195, `👤 ${active.name}   ·   Nivel ${active.charLevel}   ·   ${active.lex} LEX   ·   Modo ${active.difficulty}`, {
          fontFamily: 'Segoe UI, sans-serif',
          fontSize: fs(20),
          color: t.text,
        })
        .setOrigin(0.5);
    } else {
      label(this, cx, 195, 'Crea una partida para comenzar tu carrera.', 18, true);
    }

    // Mentor.
    label(this, cx, 245, '🧑‍⚖️ Doctor Iuris: «El COGEP será tu mejor arma. ¡Adelante!»', 16, true);

    const startY = 300;
    const gap = 64;
    const colL = cx - 190;
    const colR = cx + 190;

    makeButton(this, colL, startY, 'Nueva partida', () => this.newGame(), { primary: true });
    makeButton(this, colR, startY, 'Continuar', () => this.continueGame());
    makeButton(this, colL, startY + gap, 'Seleccionar mundo', () => this.go('WorldSelect'));
    makeButton(this, colR, startY + gap, 'Perfil y habilidades', () => this.go('Profile'));
    makeButton(this, colL, startY + gap * 2, 'Logros', () => this.go('Achievements'));
    makeButton(this, colR, startY + gap * 2, 'Ranking', () => this.go('Profile', { tab: 'ranking' }));
    makeButton(this, colL, startY + gap * 3, 'Configuración', () => this.go('Settings'));
    makeButton(this, colR, startY + gap * 3, 'Salir del juego', () => this.exitGame(), { danger: true });

    label(this, cx, GAME_HEIGHT - 28, 'Contenido educativo basado en el COGEP. No sustituye el estudio del texto oficial vigente.', 13, true);
  }

  private requireProfile(): boolean {
    if (!store.active) {
      const back = confirmDialog(
        this,
        'Aún no tienes una partida. ¿Crear una ahora?',
        () => this.newGame(),
        'Crear',
        'Cancelar'
      );
      void back;
      return false;
    }
    return true;
  }

  private newGame() {
    const name = window.prompt('¿Cómo se llama tu litigante?', store.active?.name || 'Litigante');
    if (name === null) return;
    this.scene.start('Difficulty', { name });
  }

  private continueGame() {
    if (!this.requireProfile()) return;
    this.go('WorldSelect');
  }

  private go(key: string, data?: object) {
    if (key !== 'Settings' && key !== 'Achievements' && !this.requireProfile()) return;
    this.scene.start(key, data);
  }

  private exitGame() {
    confirmDialog(this, '¿Deseas abandonar el litigio?', () => {
      window.close();
      // Si el navegador no permite cerrar la pestaña, mostramos despedida.
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
