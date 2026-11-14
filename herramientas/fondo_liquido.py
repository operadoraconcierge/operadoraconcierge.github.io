"""Genera el fondo líquido holográfico de la app (azules Concierge) → fotos/fondo-liquido.jpg"""
import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path

W, H = 900, 1800
rng = np.random.default_rng(7)


def value_noise(w, h, cell):
    gw, gh = w // cell + 3, h // cell + 3
    g = rng.random((gh, gw))
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:h, :w] / 255


def fbm(w, h, base, octaves=4):
    out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(octaves):
        out += amp * value_noise(w, h, max(4, base // (2 ** o))); tot += amp; amp *= .5
    return out / tot


y, x = np.mgrid[0:H, 0:W].astype(np.float32)
# pliegues diagonales tipo tela/metal líquido
wx = fbm(W, H, 700, 2) * 520
wy = fbm(W, H, 650, 2) * 520
u = (x + wx) * 0.0034 + (y + wy) * 0.0026
hgt = np.sin(u * 3.0) * .6 + np.sin((x * .0016 - y * .0024 + fbm(W, H, 600, 2) * 2.0) * 3.4) * .4
def blur(a, sig):
    fy = np.fft.fftfreq(a.shape[0])[:, None]; fx = np.fft.fftfreq(a.shape[1])[None, :]
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.exp(-2 * (np.pi * sig) ** 2 * (fx ** 2 + fy ** 2)))).astype(np.float32)
P = 60
hgt = blur(np.pad(hgt, P, mode='reflect'), 14)[P:-P, P:-P]

# normales y luz especular
gy, gx = np.gradient(hgt * 70)
n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)
L = np.array([-.4, -.6, .7]); L /= np.linalg.norm(L)
diff = np.clip((n * L).sum(-1), 0, 1)
Hv = L + np.array([0, 0, 1]); Hv /= np.linalg.norm(Hv)
spec = np.clip((n * Hv).sum(-1), 0, 1) ** 24

# paleta: azul profundo → azul Concierge → cian → lila pálido
t = (hgt * .5 + .5) * .6 + fbm(W, H, 800, 2) * .4
stops = np.array([[.00, 60, 110, 190], [.25, 28, 147, 206], [.45, 110, 200, 240], [.62, 176, 190, 245],
                  [.78, 214, 196, 240], [.90, 170, 230, 236], [1.0, 236, 244, 255]], np.float32)
col = np.zeros((H, W, 3), np.float32)
for c in range(3):
    col[..., c] = np.interp(t, stops[:, 0], stops[:, c + 1])
col *= (.66 + .36 * diff)[..., None]
col += spec[..., None] * 255 * .4
col += rng.normal(0, 1.2, col.shape)  # grano fino contra bandas
# viñeta hacia abajo para legibilidad

img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
out = Path(__file__).resolve().parent.parent / "fotos" / "fondo-liquido.jpg"
img.save(out, quality=78, optimize=True, progressive=True)
print(out, out.stat().st_size)
