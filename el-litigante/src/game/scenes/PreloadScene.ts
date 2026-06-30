import Phaser from 'phaser';
import { GAME_WIDTH, GAME_HEIGHT } from '../../config/gameConfig';
import { loadContent } from '../../content/ContentLoader';
import { store } from '../../core/store';
import { generateTextures } from '../systems/assets';

export class PreloadScene extends Phaser.Scene {
  constructor() {
    super('Preload');
  }

  create() {
    this.cameras.main.setBackgroundColor('#0b1d33');
    const cx = GAME_WIDTH / 2;
    const cy = GAME_HEIGHT / 2;

    this.add
      .text(cx, cy - 80, 'EL LITIGANTE', {
        fontFamily: 'Georgia, serif',
        fontSize: '64px',
        color: '#f5d547',
        fontStyle: 'bold',
      })
      .setOrigin(0.5);
    this.add
      .text(cx, cy - 20, 'Aprende el COGEP jugando', {
        fontFamily: 'Segoe UI, sans-serif',
        fontSize: '22px',
        color: '#9fb3d1',
      })
      .setOrigin(0.5);

    const bar = this.add.rectangle(cx, cy + 40, 10, 16, 0xf5d547).setOrigin(0, 0.5);
    bar.x = cx - 200;
    this.add.rectangle(cx, cy + 40, 400, 16).setStrokeStyle(2, 0x9fb3d1).setFillStyle(0x13294b);
    this.add.rectangle(bar.x, cy + 40, 0, 16, 0xf5d547).setOrigin(0, 0.5);
    const fill = this.add.rectangle(cx - 200, cy + 40, 0, 12, 0xf5d547).setOrigin(0, 0.5);

    const status = this.add
      .text(cx, cy + 80, 'Cargando contenido jurídico…', {
        fontFamily: 'Segoe UI, sans-serif',
        fontSize: '16px',
        color: '#9fb3d1',
      })
      .setOrigin(0.5);

    this.tweens.add({ targets: fill, width: 400, duration: 600, ease: 'Sine.inOut' });

    generateTextures(this);

    loadContent()
      .then((content) => {
        store.init(content);
        status.setText('¡Listo!');
        this.time.delayedCall(300, () => this.scene.start('Menu'));
      })
      .catch((err) => {
        console.error(err);
        status.setColor('#ff6b6b');
        status.setText('Error al cargar el contenido. Revisa la carpeta /data.');
      });
  }
}
