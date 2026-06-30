import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { grantXp } from '../../core/rpg';
import { evaluateAchievements } from '../../core/achievements';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, fs } from '../ui/widgets';
import type { LegalCase } from '../../core/types';

export class VerdictScene extends Phaser.Scene {
  constructor() {
    super('Verdict');
  }

  create(data: { caseId: string; conviccion: number; correct: number; answered: number }) {
    const caso = store.content.cases.find((c) => c.id === data.caseId) as LegalCase;
    const won = data.conviccion >= caso.meta;
    const a = store.ensureProfile();

    // Recompensas y progreso.
    a.stats.trivia += data.correct;
    if (won) {
      if (!a.casesWon.includes(caso.id)) a.casesWon.push(caso.id);
      if (!a.levelsCompleted.includes('case_' + caso.id)) a.levelsCompleted.push('case_' + caso.id);
      a.lex += 100;
      grantXp(a, 150);
    } else {
      a.lex += 20;
      grantXp(a, 40);
    }
    const unlocked = evaluateAchievements(a, store.content);
    store.persistProfiles();

    // Escena.
    this.add.image(GAME_WIDTH / 2, GAME_HEIGHT / 2, SCENE_TEX.sala).setDepth(0);
    this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000000, 0.55).setDepth(1);
    this.add.sprite(GAME_WIDTH / 2, 360, SCENE_TEX.juez).setOrigin(0.5, 1).setScale(1.5).setDepth(2);

    const cx = GAME_WIDTH / 2;
    this.add.text(cx, 70, won ? '⚖️ ¡CASO GANADO!' : '⚖️ CASO PERDIDO', {
      fontFamily: 'Georgia, serif',
      fontSize: fs(52),
      color: won ? '#f5d547' : '#ff6b6b',
      fontStyle: 'bold',
    }).setOrigin(0.5).setDepth(5);

    this.add.text(cx, 124, caso.titulo + '  ·  ' + caso.materia, { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#eaf2ff' }).setOrigin(0.5).setDepth(5);

    // Panel de sentencia.
    this.add.rectangle(cx, 470, GAME_WIDTH - 120, 250, 0x0b1d33, 0.92).setStrokeStyle(3, won ? 0x3ad07a : 0xe25555).setDepth(4);
    this.add.text(cx, 400, '📜 Sentencia del juez', { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#f5d547', fontStyle: 'bold' }).setOrigin(0.5).setDepth(5);
    this.add.text(cx, 470, won ? caso.veredictoGana : caso.veredictoPierde, {
      fontFamily: 'Segoe UI',
      fontSize: fs(19),
      color: '#ffffff',
      align: 'center',
      wordWrap: { width: GAME_WIDTH - 180 },
      lineSpacing: 4,
    }).setOrigin(0.5).setDepth(5);

    this.add.text(cx, 552, `Convicción lograda: ${data.conviccion}%  (meta ${caso.meta}%)   ·   Aciertos: ${data.correct}/${data.answered}   ·   ${won ? '+100' : '+20'} LEX`, {
      fontFamily: 'Segoe UI',
      fontSize: fs(16),
      color: '#9fb3d1',
    }).setOrigin(0.5).setDepth(5);

    if (unlocked.length) {
      this.add.text(cx, 582, '🏆 ' + unlocked.slice(0, 3).map((u) => u.name).join(' · '), { fontFamily: 'Segoe UI', fontSize: fs(15), color: '#f5d547', wordWrap: { width: GAME_WIDTH - 180 } }).setOrigin(0.5).setDepth(5);
    }

    makeButton(this, cx - 180, GAME_HEIGHT - 50, won ? 'Otro caso' : 'Reintentar', () => {
      if (won) this.scene.start('CaseSelect');
      else this.scene.start('Audiencia', { caseId: caso.id });
    }, { width: 300, height: 56, primary: true });
    makeButton(this, cx + 180, GAME_HEIGHT - 50, 'Menú', () => this.scene.start('Menu'), { width: 300, height: 56 });
  }
}
