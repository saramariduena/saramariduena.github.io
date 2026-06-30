import Phaser from 'phaser';

// Generación procedural de escenarios y personajes 2D con aspecto más humano
// (cabeza, rostro, traje/toga, brazos, piernas). Todo por código, sin assets
// con derechos de autor.

export const SCENE_TEX = {
  oficina: 'bg_oficina',
  sala: 'bg_sala',
  juez: 'char_juez',
  tu: 'char_tu',
  tu_f: 'char_tu_f',
  contraparte: 'char_contraparte',
  cliente: 'char_cliente',
  secretario: 'char_secretario',
  testigo: 'char_testigo',
  mediador: 'char_mediador',
};

function make(scene: Phaser.Scene, key: string, w: number, h: number, draw: (g: Phaser.GameObjects.Graphics) => void) {
  if (scene.textures.exists(key)) return;
  const g = scene.add.graphics();
  draw(g);
  g.generateTexture(key, w, h);
  g.destroy();
}

interface PersonOpts {
  skin: number;
  hair: number;
  suit: number;
  shirt: number;
  tie: number;
  robe?: boolean; // toga de juez
  female?: boolean;
}

const PW = 110;
const PH = 180;

function drawPerson(g: Phaser.GameObjects.Graphics, o: PersonOpts) {
  const cx = PW / 2;
  // Sombra base
  g.fillStyle(0x000000, 0.15);
  g.fillEllipse(cx, PH - 6, 70, 14);

  // Piernas / pantalón
  g.fillStyle(o.robe ? 0x1a1a1a : 0x222a38, 1);
  if (o.robe) {
    g.fillRoundedRect(cx - 34, 92, 68, 84, 10);
  } else {
    g.fillRect(cx - 20, 120, 16, 56);
    g.fillRect(cx + 4, 120, 16, 56);
  }
  // Zapatos
  g.fillStyle(0x111111, 1);
  if (!o.robe) {
    g.fillRoundedRect(cx - 22, 168, 20, 10, 3);
    g.fillRoundedRect(cx + 2, 168, 20, 10, 3);
  } else {
    g.fillRoundedRect(cx - 14, 170, 28, 8, 3);
  }

  // Torso (saco o toga)
  g.fillStyle(o.robe ? 0x141414 : o.suit, 1);
  g.fillRoundedRect(cx - 30, 60, 60, 64, 12);
  if (o.robe) {
    // solapas de toga
    g.fillStyle(0x0c0c0c, 1);
    g.fillTriangle(cx - 30, 60, cx, 66, cx - 30, 120);
    g.fillTriangle(cx + 30, 60, cx, 66, cx + 30, 120);
    // bib blanco del juez
    g.fillStyle(0xffffff, 1);
    g.fillRoundedRect(cx - 9, 60, 18, 26, 3);
  } else {
    // camisa en V
    g.fillStyle(o.shirt, 1);
    g.fillTriangle(cx, 60, cx - 12, 60, cx, 92);
    g.fillTriangle(cx, 60, cx + 12, 60, cx, 92);
    // corbata
    g.fillStyle(o.tie, 1);
    g.fillTriangle(cx, 62, cx - 5, 70, cx + 5, 70);
    g.fillRect(cx - 3, 70, 6, 24);
    // solapas del saco
    g.fillStyle(Phaser.Display.Color.IntegerToColor(o.suit).darken(20).color, 1);
    g.fillTriangle(cx - 30, 60, cx - 6, 62, cx - 22, 100);
    g.fillTriangle(cx + 30, 60, cx + 6, 62, cx + 22, 100);
  }

  // Brazos
  g.fillStyle(o.robe ? 0x141414 : o.suit, 1);
  g.fillRoundedRect(cx - 40, 64, 14, 50, 7);
  g.fillRoundedRect(cx + 26, 64, 14, 50, 7);
  // Manos
  g.fillStyle(o.skin, 1);
  g.fillCircle(cx - 33, 116, 7);
  g.fillCircle(cx + 33, 116, 7);

  // Cuello
  g.fillStyle(o.skin, 1);
  g.fillRect(cx - 7, 48, 14, 16);

  // Cabeza
  g.fillStyle(o.skin, 1);
  g.fillCircle(cx, 34, 22);
  // Orejas
  g.fillCircle(cx - 21, 36, 4);
  g.fillCircle(cx + 21, 36, 4);

  // Pelo
  g.fillStyle(o.hair, 1);
  if (o.female) {
    g.fillRoundedRect(cx - 24, 12, 48, 26, 12);
    g.fillRect(cx - 24, 30, 8, 26);
    g.fillRect(cx + 16, 30, 8, 26);
  } else {
    g.fillRoundedRect(cx - 22, 12, 44, 18, 10);
    g.fillRect(cx - 22, 18, 6, 14);
    g.fillRect(cx + 16, 18, 6, 14);
  }

  // Cejas
  g.fillStyle(Phaser.Display.Color.IntegerToColor(o.hair).darken(10).color, 1);
  g.fillRect(cx - 14, 30, 9, 3);
  g.fillRect(cx + 5, 30, 9, 3);
  // Ojos
  g.fillStyle(0xffffff, 1);
  g.fillCircle(cx - 9, 36, 4);
  g.fillCircle(cx + 9, 36, 4);
  g.fillStyle(0x20202a, 1);
  g.fillCircle(cx - 8, 37, 2);
  g.fillCircle(cx + 10, 37, 2);
  // Nariz
  g.fillStyle(Phaser.Display.Color.IntegerToColor(o.skin).darken(12).color, 1);
  g.fillCircle(cx, 42, 2.5);
  // Boca (sonrisa suave)
  g.lineStyle(2, 0x9a4a3a, 1);
  g.beginPath();
  g.arc(cx, 44, 6, Phaser.Math.DegToRad(20), Phaser.Math.DegToRad(160), false);
  g.strokePath();
}

export function generateCourtroom(scene: Phaser.Scene) {
  // --- Personajes ---
  make(scene, SCENE_TEX.juez, PW, PH, (g) => drawPerson(g, { skin: 0xe8b98e, hair: 0xcfcfcf, suit: 0x141414, shirt: 0xffffff, tie: 0x222222, robe: true }));
  make(scene, SCENE_TEX.tu, PW, PH, (g) => drawPerson(g, { skin: 0xf1c27d, hair: 0x3a2a1a, suit: 0x1f3a5f, shirt: 0xffffff, tie: 0xc0392b }));
  make(scene, SCENE_TEX.tu_f, PW, PH, (g) => drawPerson(g, { skin: 0xf3c89a, hair: 0x2a1a10, suit: 0x16324f, shirt: 0xffffff, tie: 0xb83b5e, female: true }));
  make(scene, SCENE_TEX.contraparte, PW, PH, (g) => drawPerson(g, { skin: 0xd9a066, hair: 0x20140a, suit: 0x4a2d4a, shirt: 0xf0f0f0, tie: 0x2c3e50 }));
  make(scene, SCENE_TEX.cliente, PW, PH, (g) => drawPerson(g, { skin: 0xe0ac69, hair: 0x4a2f1a, suit: 0x8a6d3b, shirt: 0xfff3d6, tie: 0x6b4f2a, female: true }));
  make(scene, SCENE_TEX.secretario, PW, PH, (g) => drawPerson(g, { skin: 0xe8b98e, hair: 0x2a2a2a, suit: 0x37474f, shirt: 0xffffff, tie: 0x546e7a }));
  make(scene, SCENE_TEX.testigo, PW, PH, (g) => drawPerson(g, { skin: 0xc68642, hair: 0x1a1a1a, suit: 0x5d4037, shirt: 0xeeeeee, tie: 0x795548 }));
  make(scene, SCENE_TEX.mediador, PW, PH, (g) => drawPerson(g, { skin: 0xe0ac69, hair: 0x4a4a4a, suit: 0x2e7d6b, shirt: 0xffffff, tie: 0x1b5e54, female: true }));

  // --- Fondo: oficina ---
  make(scene, SCENE_TEX.oficina, 1280, 720, (g) => {
    g.fillStyle(0xe4ddca, 1);
    g.fillRect(0, 0, 1280, 720);
    // piso
    g.fillStyle(0x8a6b4a, 1);
    g.fillRect(0, 560, 1280, 160);
    g.fillStyle(0x7a5d3f, 1);
    for (let x = 0; x < 1280; x += 80) g.fillRect(x, 560, 4, 160);
    // ventana
    g.fillStyle(0xbfe3ff, 1);
    g.fillRoundedRect(120, 80, 260, 200, 8);
    g.fillStyle(0xffffff, 1);
    g.fillRect(244, 80, 8, 200);
    g.fillRect(120, 174, 260, 8);
    // estantería con libros
    g.fillStyle(0x5b3d27, 1);
    g.fillRect(880, 90, 320, 360);
    const cols = [0x8e3b2e, 0x2e5d8e, 0x2e8e57, 0x8e7d2e, 0x6b2e8e];
    for (let r = 0; r < 4; r++) {
      g.fillStyle(0x3f2a1a, 1);
      g.fillRect(880, 90 + r * 90 + 78, 320, 12);
      for (let b = 0; b < 14; b++) {
        g.fillStyle(cols[(r + b) % cols.length], 1);
        g.fillRect(892 + b * 22, 100 + r * 90, 18, 76);
      }
    }
    // escritorio
    g.fillStyle(0x6e4a30, 1);
    g.fillRoundedRect(420, 470, 460, 110, 10);
    g.fillStyle(0x5a3c26, 1);
    g.fillRect(440, 580, 30, 120);
    g.fillRect(830, 580, 30, 120);
    // balanza sobre el escritorio
    g.fillStyle(0xc9a227, 1);
    g.fillRect(636, 410, 6, 60);
    g.fillRect(600, 408, 80, 5);
    g.fillCircle(605, 430, 12);
    g.fillCircle(675, 430, 12);
  });

  // --- Fondo: sala de audiencia ---
  make(scene, SCENE_TEX.sala, 1280, 720, (g) => {
    g.fillStyle(0x4a3826, 1);
    g.fillRect(0, 0, 1280, 720);
    // pared de madera con paneles
    g.fillStyle(0x6e4a30, 1);
    for (let x = 0; x < 1280; x += 160) g.fillRoundedRect(x + 10, 40, 140, 360, 8);
    // piso
    g.fillStyle(0x7a5d3f, 1);
    g.fillRect(0, 520, 1280, 200);
    g.fillStyle(0x6a4f35, 1);
    for (let x = 0; x < 1280; x += 90) g.fillRect(x, 520, 5, 200);
    // estrado del juez (elevado, al centro/fondo)
    g.fillStyle(0x4e3320, 1);
    g.fillRoundedRect(470, 230, 340, 200, 10);
    g.fillStyle(0x3c2718, 1);
    g.fillRect(470, 410, 340, 30);
    // escudo / balanza grande detrás
    g.fillStyle(0xc9a227, 0.9);
    g.fillRect(637, 90, 6, 90);
    g.fillRect(590, 96, 100, 5);
    g.fillCircle(595, 130, 16);
    g.fillCircle(685, 130, 16);
    g.fillStyle(0xc9a227, 1);
    g.fillCircle(640, 86, 8);
    // franja tricolor (acento ecuatoriano)
    g.fillStyle(0xffd100, 1); g.fillRect(40, 40, 120, 10);
    g.fillStyle(0x0033a0, 1); g.fillRect(40, 50, 120, 6);
    g.fillStyle(0xef3340, 1); g.fillRect(40, 56, 120, 6);
    // mesas de las partes
    g.fillStyle(0x5a3c26, 1);
    g.fillRoundedRect(120, 470, 300, 70, 8);
    g.fillRoundedRect(860, 470, 300, 70, 8);
  });
}
