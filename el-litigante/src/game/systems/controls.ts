// Estado de control compartido entre el HUD (botones táctiles) y la escena de
// nivel (teclado/gamepad). Cualquier fuente de entrada escribe aquí.
export const controls = {
  left: false,
  right: false,
  jump: false,
  run: false,
};

export function resetControls() {
  controls.left = false;
  controls.right = false;
  controls.jump = false;
  controls.run = false;
}
