import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { store } from '../../core/store';
import { grantXp } from '../../core/rpg';
import { evaluateAchievements } from '../../core/achievements';
import { rankIndex, rankName } from '../../core/ranks';
import { SCENE_TEX } from '../systems/courtroom';
import { makeButton, fs } from '../ui/widgets';
import type { LegalCase, Instancia } from '../../core/types';

export class VerdictScene extends Phaser.Scene {
  constructor() {
    super('Verdict');
  }

  create(data: { caseId: string; instancia?: Instancia; conviccion: number; correct: number; answered: number }) {
    const caso = store.content.cases.find((c) => c.id === data.caseId) as LegalCase;
    const instancia: Instancia = data.instancia || 'primera';
    const won = data.conviccion >= caso.meta;
    const isMediacion = caso.tipo === 'mediacion';
    const a = store.ensureProfile();

    // Recompensas y progreso.
    a.stats.trivia += data.correct;
    const oldRank = rankIndex(store.content.ranks, a);
    if (won) {
      if (!a.casesWon.includes(caso.id)) a.casesWon.push(caso.id);
      if (!a.levelsCompleted.includes('case_' + caso.id)) a.levelsCompleted.push('case_' + caso.id);
      a.lex += 100;
      grantXp(a, 150);
    } else {
      a.lex += 20;
      grantXp(a, 40);
    }
    const newRank = rankIndex(store.content.ranks, a);
    const ascendio = won && newRank > oldRank;
    const unlocked = evaluateAchievements(a, store.content);
    store.persistProfiles();

    // Fondo y figura según el tipo de desenlace.
    const bgTex = isMediacion ? SCENE_TEX.oficina : SCENE_TEX.sala;
    const figureTex = isMediacion ? SCENE_TEX.mediador : SCENE_TEX.juez;
    this.add.image(GAME_WIDTH / 2, GAME_HEIGHT / 2, bgTex).setDepth(0);
    this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000000, 0.55).setDepth(1);
    this.add.sprite(GAME_WIDTH / 2, 360, figureTex).setOrigin(0.5, 1).setScale(1.5).setDepth(2);

    const cx = GAME_WIDTH / 2;

    // Título según resultado e instancia.
    let header: string;
    if (isMediacion) header = won ? '🤝 ¡ACUERDO LOGRADO!' : '🤝 SIN ACUERDO';
    else if (won) header = instancia === 'primera' ? '⚖️ ¡CASO GANADO!' : instancia === 'apelacion' ? '⚖️ ¡GANASTE EN APELACIÓN!' : '⚖️ ¡GANASTE EN CASACIÓN!';
    else header = instancia === 'primera' ? '⚖️ CASO PERDIDO' : instancia === 'apelacion' ? '⚖️ APELACIÓN RECHAZADA' : '⚖️ CASACIÓN RECHAZADA';

    this.add.text(cx, 64, header, { fontFamily: 'Georgia, serif', fontSize: fs(46), color: won ? '#f5d547' : '#ff6b6b', fontStyle: 'bold', align: 'center' }).setOrigin(0.5).setDepth(5);
    this.add.text(cx, 116, caso.titulo + '  ·  ' + caso.materia, { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#eaf2ff' }).setOrigin(0.5).setDepth(5);

    // Panel de desenlace.
    this.add.rectangle(cx, 470, GAME_WIDTH - 120, 250, 0x0b1d33, 0.92).setStrokeStyle(3, won ? 0x3ad07a : 0xe25555).setDepth(4);
    const tituloPanel = isMediacion ? '🤝 Acta de mediación' : instancia === 'primera' ? '📜 Sentencia del juez' : '📜 Resolución del tribunal';
    this.add.text(cx, 400, tituloPanel, { fontFamily: 'Segoe UI', fontSize: fs(18), color: '#f5d547', fontStyle: 'bold' }).setOrigin(0.5).setDepth(5);

    let cuerpo = won ? caso.veredictoGana : caso.veredictoPierde;
    if (!isMediacion && instancia !== 'primera') {
      cuerpo = (won ? 'El tribunal REVOCA la decisión anterior. ' : 'El tribunal CONFIRMA la decisión anterior. ') + cuerpo;
    }
    this.add.text(cx, 470, cuerpo, { fontFamily: 'Segoe UI', fontSize: fs(19), color: '#ffffff', align: 'center', wordWrap: { width: GAME_WIDTH - 180 }, lineSpacing: 4 }).setOrigin(0.5).setDepth(5);

    this.add.text(cx, 552, `${isMediacion ? 'Acuerdo' : 'Convicción'}: ${data.conviccion}%  (meta ${caso.meta}%)   ·   Aciertos: ${data.correct}/${data.answered}   ·   ${won ? '+100' : '+20'} LEX`, { fontFamily: 'Segoe UI', fontSize: fs(16), color: '#9fb3d1' }).setOrigin(0.5).setDepth(5);

    if (unlocked.length) {
      this.add.text(cx, 582, '🏆 ' + unlocked.slice(0, 3).map((u) => u.name).join(' · '), { fontFamily: 'Segoe UI', fontSize: fs(15), color: '#f5d547', wordWrap: { width: GAME_WIDTH - 180 } }).setOrigin(0.5).setDepth(5);
    }

    if (ascendio) this.showAscenso(newRank);

    this.buildButtons(won, isMediacion, instancia, caso);
  }

  private showAscenso(newRank: number) {
    const a = store.active!;
    const r = store.content.ranks[newRank];
    const nombre = rankName(store.content.ranks, newRank, a.gender);
    const cx = GAME_WIDTH / 2;
    const layer = this.add.container(0, 0).setDepth(200);
    layer.add(this.add.rectangle(cx, 300, GAME_WIDTH - 200, 130, 0x1f5132, 0.96).setStrokeStyle(4, 0xf5d547));
    layer.add(this.add.text(cx, 268, `⭐ ¡ASCENSO!  Ahora eres ${r.icon} ${nombre}`, { fontFamily: 'Georgia, serif', fontSize: fs(30), color: '#f5d547', fontStyle: 'bold', align: 'center' }).setOrigin(0.5));
    layer.add(this.add.text(cx, 318, r.perk, { fontFamily: 'Segoe UI', fontSize: fs(16), color: '#eaffea', align: 'center', wordWrap: { width: GAME_WIDTH - 260 } }).setOrigin(0.5));
    this.tweens.add({ targets: layer, scale: { from: 0.85, to: 1 }, duration: 350, ease: 'Back.out' });
  }

  private buildButtons(won: boolean, isMediacion: boolean, instancia: Instancia, caso: LegalCase) {
    const cx = GAME_WIDTH / 2;
    const y = GAME_HEIGHT - 56;
    const btns: Phaser.GameObjects.Container[] = [];

    if (won) {
      btns.push(makeButton(this, 0, 0, '⚖️ Jugar otro caso', () => this.scene.start('CaseSelect'), { width: 320, height: 60, primary: true, fontSize: 21 }));
      btns.push(makeButton(this, 0, 0, '🏠 Menú', () => this.scene.start('Menu'), { width: 320, height: 60, fontSize: 21 }));
    } else if (!isMediacion && instancia === 'primera') {
      btns.push(makeButton(this, 0, 0, '⚖️ Apelar', () => this.scene.start('Audiencia', { caseId: caso.id, instancia: 'apelacion' }), { width: 300, height: 60, primary: true, fontSize: 20 }));
      btns.push(makeButton(this, 0, 0, '↻ Reintentar', () => this.scene.start('Audiencia', { caseId: caso.id, instancia: 'primera' }), { width: 300, height: 60, fontSize: 19 }));
      btns.push(makeButton(this, 0, 0, '🏠 Menú', () => this.scene.start('Menu'), { width: 240, height: 60, fontSize: 19 }));
    } else if (!isMediacion && instancia === 'apelacion') {
      btns.push(makeButton(this, 0, 0, '⚖️ Recurrir en casación', () => this.scene.start('Audiencia', { caseId: caso.id, instancia: 'casacion' }), { width: 360, height: 60, primary: true, fontSize: 19 }));
      btns.push(makeButton(this, 0, 0, '↻ Reintentar', () => this.scene.start('Audiencia', { caseId: caso.id, instancia: 'primera' }), { width: 260, height: 60, fontSize: 19 }));
      btns.push(makeButton(this, 0, 0, '🏠 Menú', () => this.scene.start('Menu'), { width: 200, height: 60, fontSize: 19 }));
    } else {
      // Casación perdida, o mediación sin acuerdo: no hay más instancias.
      btns.push(makeButton(this, 0, 0, '↻ Reintentar', () => this.scene.start('Audiencia', { caseId: caso.id, instancia: 'primera' }), { width: 320, height: 60, primary: true, fontSize: 20 }));
      btns.push(makeButton(this, 0, 0, '🏠 Menú', () => this.scene.start('Menu'), { width: 320, height: 60, fontSize: 20 }));
    }

    // Distribuir horizontalmente y elevar sobre el velo.
    const gap = 24;
    const widths = btns.map((b) => (b.getData('w') as number) || b.width);
    const totalW = widths.reduce((s, w) => s + w, 0) + gap * (btns.length - 1);
    let x = cx - totalW / 2;
    btns.forEach((b, i) => {
      b.setPosition(x + widths[i] / 2, y);
      b.setDepth(50);
      x += widths[i] + gap;
    });
  }
}
