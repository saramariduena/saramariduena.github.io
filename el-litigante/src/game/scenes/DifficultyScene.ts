import Phaser from 'phaser';
import { GAME_WIDTH } from '../../config/gameConfig';
import { store, createProfile } from '../../core/store';
import { makeButton, title, label, paintBackground } from '../ui/widgets';

export class DifficultyScene extends Phaser.Scene {
  private playerName = 'Litigante';

  constructor() {
    super('Difficulty');
  }

  init(data: { name?: string }) {
    this.playerName = data?.name || 'Litigante';
  }

  create() {
    paintBackground(this);
    const cx = GAME_WIDTH / 2;
    title(this, cx, 90, 'Elige tu dificultad', 44);
    label(this, cx, 140, `Litigante: ${this.playerName}`, 22);

    let y = 220;
    for (const d of store.content.difficulties) {
      makeButton(
        this,
        cx,
        y,
        `${d.name}  —  ${d.lives} vidas`,
        () => this.choose(d.id),
        { width: 620, height: 60, primary: d.id === 'abogado' }
      );
      label(this, cx, y + 32, d.desc, 14, true);
      y += 88;
    }

    makeButton(this, cx, y + 10, 'Volver', () => this.scene.start('Menu'), { width: 220, height: 52 });
  }

  private choose(difficulty: string) {
    const profile = createProfile(this.playerName, difficulty);
    store.addProfile(profile);
    this.scene.start('WorldSelect');
  }
}
