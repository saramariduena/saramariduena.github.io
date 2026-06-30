import Phaser from 'phaser';
import { TILE } from '../../config/gameConfig';

// Generación procedural de TODOS los assets gráficos por código. No se usa
// ningún sprite, imagen ni recurso con derechos de autor: cada textura se
// dibuja con primitivas y se cachea como textura del motor.

export const TEX = {
  ground: 'tex_ground',
  platform: 'tex_platform',
  player: 'tex_player',
  enemy: 'tex_enemy',
  boss: 'tex_boss',
  lex: 'tex_lex',
  doc: 'tex_doc',
  hazard: 'tex_hazard',
  flag: 'tex_flag',
  heart: 'tex_heart',
  shield: 'tex_shield',
  particle: 'tex_particle',
  cloud: 'tex_cloud',
};

function make(scene: Phaser.Scene, key: string, w: number, h: number, draw: (g: Phaser.GameObjects.Graphics) => void) {
  if (scene.textures.exists(key)) return;
  const g = scene.add.graphics();
  draw(g);
  g.generateTexture(key, w, h);
  g.destroy();
}

export function generateTextures(scene: Phaser.Scene) {
  // Bloque de suelo: relleno con vetas para dar textura de tierra/piedra.
  make(scene, TEX.ground, TILE, TILE, (g) => {
    g.fillStyle(0x3c7d3c, 1);
    g.fillRect(0, 0, TILE, TILE);
    g.fillStyle(0x2a5a2a, 1);
    g.fillRect(0, 0, TILE, 10);
    g.fillStyle(0x2f6630, 1);
    for (let i = 0; i < 6; i++) g.fillRect((i * 11) % TILE, 14 + ((i * 17) % 40), 8, 6);
    g.lineStyle(2, 0x224a22, 1);
    g.strokeRect(1, 1, TILE - 2, TILE - 2);
  });

  // Plataforma flotante de madera.
  make(scene, TEX.platform, TILE, TILE / 2, (g) => {
    g.fillStyle(0xa9744f, 1);
    g.fillRoundedRect(0, 0, TILE, TILE / 2, 6);
    g.fillStyle(0x8a5e3f, 1);
    g.fillRect(0, TILE / 2 - 8, TILE, 8);
    g.lineStyle(2, 0x6e4a30, 1);
    g.strokeRoundedRect(1, 1, TILE - 2, TILE / 2 - 2, 6);
  });

  // El Litigante: traje formal con corbata. Cuerpo 44x60.
  make(scene, TEX.player, 44, 62, (g) => {
    // cabeza
    g.fillStyle(0xf1c27d, 1);
    g.fillCircle(22, 13, 11);
    // pelo
    g.fillStyle(0x3a2a1a, 1);
    g.fillRect(11, 2, 22, 8);
    // cuerpo / saco
    g.fillStyle(0x1f3a5f, 1);
    g.fillRoundedRect(6, 24, 32, 30, 6);
    // camisa
    g.fillStyle(0xffffff, 1);
    g.fillTriangle(22, 24, 14, 24, 22, 40);
    g.fillTriangle(22, 24, 30, 24, 22, 40);
    // corbata
    g.fillStyle(0xc0392b, 1);
    g.fillTriangle(22, 26, 19, 30, 25, 30);
    g.fillRect(20, 30, 4, 12);
    // piernas
    g.fillStyle(0x14253d, 1);
    g.fillRect(10, 54, 9, 8);
    g.fillRect(25, 54, 9, 8);
  });

  // Enemigo (error procesal): mancha con ojos enojados (se tiñe por color).
  make(scene, TEX.enemy, 48, 44, (g) => {
    g.fillStyle(0xffffff, 1);
    g.fillRoundedRect(2, 6, 44, 36, 10);
    g.fillStyle(0x000000, 1);
    g.fillCircle(16, 20, 5);
    g.fillCircle(32, 20, 5);
    g.fillStyle(0xffffff, 1);
    g.fillCircle(17, 19, 2);
    g.fillCircle(33, 19, 2);
    // ceño / boca
    g.fillStyle(0x000000, 1);
    g.fillRect(12, 30, 24, 4);
  });

  // Jefe: versión grande.
  make(scene, TEX.boss, 96, 96, (g) => {
    g.fillStyle(0xffffff, 1);
    g.fillRoundedRect(4, 10, 88, 80, 16);
    g.fillStyle(0x000000, 1);
    g.fillCircle(32, 42, 9);
    g.fillCircle(64, 42, 9);
    g.fillStyle(0xffffff, 1);
    g.fillCircle(34, 40, 3);
    g.fillCircle(66, 40, 3);
    g.fillStyle(0x000000, 1);
    g.fillRect(26, 64, 44, 7);
  });

  // Moneda LEX.
  make(scene, TEX.lex, 32, 32, (g) => {
    g.fillStyle(0xf5d547, 1);
    g.fillCircle(16, 16, 15);
    g.fillStyle(0xd4af2a, 1);
    g.fillCircle(16, 16, 11);
    g.fillStyle(0xfff3b0, 1);
    g.fillCircle(16, 16, 8);
  });

  // Expediente / documento.
  make(scene, TEX.doc, 28, 34, (g) => {
    g.fillStyle(0xfdf6e3, 1);
    g.fillRoundedRect(2, 2, 24, 30, 3);
    g.fillStyle(0x2d6cdf, 1);
    g.fillRect(6, 8, 16, 3);
    g.fillRect(6, 15, 16, 3);
    g.fillRect(6, 22, 12, 3);
    g.fillStyle(0xc0392b, 1);
    g.fillCircle(20, 27, 4);
  });

  // Peligro (error grave): pinchos.
  make(scene, TEX.hazard, TILE, TILE / 2, (g) => {
    g.fillStyle(0x7f1d1d, 1);
    const spikes = 4;
    const w = TILE / spikes;
    for (let i = 0; i < spikes; i++) {
      g.fillTriangle(i * w, TILE / 2, i * w + w / 2, 4, i * w + w, TILE / 2);
    }
    g.fillStyle(0x991b1b, 1);
    g.fillRect(0, TILE / 2 - 6, TILE, 6);
  });

  // Meta (bandera de la justicia).
  make(scene, TEX.flag, 40, 80, (g) => {
    g.fillStyle(0x8a5e3f, 1);
    g.fillRect(4, 0, 6, 80);
    g.fillStyle(0xf5d547, 1);
    g.fillTriangle(10, 6, 38, 16, 10, 30);
    g.fillStyle(0x13294b, 1);
    g.fillCircle(20, 16, 4);
  });

  // Corazón (vida).
  make(scene, TEX.heart, 28, 26, (g) => {
    g.fillStyle(0xe23b3b, 1);
    g.fillCircle(8, 9, 7);
    g.fillCircle(20, 9, 7);
    g.fillTriangle(1, 11, 27, 11, 14, 25);
  });

  // Escudo.
  make(scene, TEX.shield, 28, 30, (g) => {
    g.fillStyle(0x3a8fd6, 1);
    g.fillRoundedRect(2, 2, 24, 20, 6);
    g.fillTriangle(2, 20, 26, 20, 14, 30);
    g.fillStyle(0xbfe3ff, 1);
    g.fillRect(12, 6, 4, 14);
    g.fillRect(7, 11, 14, 4);
  });

  // Partícula simple.
  make(scene, TEX.particle, 8, 8, (g) => {
    g.fillStyle(0xffffff, 1);
    g.fillCircle(4, 4, 4);
  });

  // Nube de fondo.
  make(scene, TEX.cloud, 120, 60, (g) => {
    g.fillStyle(0xffffff, 0.9);
    g.fillCircle(35, 38, 22);
    g.fillCircle(60, 30, 28);
    g.fillCircle(88, 40, 20);
    g.fillRect(35, 38, 53, 20);
  });
}
