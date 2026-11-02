// Facial features in /images/goethe-campagna.jpg (920×920 crop of Tischbein's painting), in image pixels.
export const FACE_IMAGE = "/images/goethe-campagna.jpg";
const MOUTH = { x0: 432, x1: 508, y: 472 };
const CHIN_Y = 560;
const EYE = { x0: 386, x1: 456, lid: 337, lower: 366 };
const BROW = { x0: 392, x1: 505, top: 290, bottom: 342 };

export interface Expression {
  open: number; // jaw, 0..1
  blink: number; // eyelid, 0..1
  brow: number; // brow raise, 0..1
}

// Redraws columns x0..x1 of the source band [top, bottom] into [top + dTop, bottom + dBottom],
// weighted by a bell across x (flatter for smaller `falloff`) so the warp blends into the painting.
function stretch(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  x0: number,
  x1: number,
  top: number,
  bottom: number,
  dTop: number,
  dBottom: number,
  falloff = 2,
) {
  for (let x = x0; x < x1; x++) {
    const w = Math.sin((Math.PI * (x - x0)) / (x1 - x0)) ** falloff;
    const y = top + dTop * w;
    ctx.drawImage(img, x, top, 1, bottom - top, x, y, 1, bottom + dBottom * w - y);
  }
}

export function drawFace(ctx: CanvasRenderingContext2D, img: HTMLImageElement, e: Expression) {
  ctx.drawImage(img, 0, 0);

  const gap = e.open * 14;
  if (gap > 0.5) {
    ctx.fillStyle = "#3a1712";
    ctx.beginPath();
    ctx.ellipse((MOUTH.x0 + MOUTH.x1) / 2, MOUTH.y + gap / 2, (MOUTH.x1 - MOUTH.x0) * 0.38, gap / 2, 0, 0, 2 * Math.PI);
    ctx.fill();
    stretch(ctx, img, MOUTH.x0 - 20, MOUTH.x1 + 10, MOUTH.y, CHIN_Y, gap, 0);
  }
  if (e.brow > 0) stretch(ctx, img, BROW.x0, BROW.x1, BROW.top, BROW.bottom, -e.brow * 12, 0);
  if (e.blink > 0) stretch(ctx, img, EYE.x0, EYE.x1, EYE.lid - 8, EYE.lid, 0, e.blink * (EYE.lower - EYE.lid), 0.5);
}
