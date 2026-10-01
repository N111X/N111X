#!/usr/bin/env python3
"""Ruta B: foto -> ASCII con parallax 2.5D en loop perfecto.
Uso:  python generator/avatar_photo.py --photo perfil.jpg [--depth profundidad.png]
 - Con --depth (mapa de profundidad en gris, claro=cerca; p. ej. generado con MiDaS fuera de este repo)
   el parallax usa la profundidad real. Sin él, se usa la luminancia como proxy (aproximación burda:
   funciona razonablemente en retratos con fondo oscuro, pero NO es profundidad real).
 - Salida: assets/avatar-photo.gif (+ .svg). Para usarla, cambia la ruta en generator/README.tmpl.md.
"""
import argparse, math, sys, pathlib
import numpy as np
from PIL import Image, ImageOps
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import avatar as av


def to_gray(path, size):
    im = Image.open(path).convert("L")
    return np.asarray(ImageOps.fit(im, size, Image.Resampling.LANCZOS), float) / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True); ap.add_argument("--depth")
    ap.add_argument("--parallax", type=float, default=0.035, help="amplitud (fracción del ancho)")
    a = ap.parse_args()
    W, H = av.COLS * 4, av.ROWS * 8                       # resolución de trabajo (celda 1:2)
    lum = to_gray(a.photo, (W, H))
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())          # autocontraste
    depth = to_gray(a.depth, (W, H)) if a.depth else lum
    xs = np.arange(W)[None, :].repeat(H, 0)
    ys = np.arange(H)[:, None].repeat(W, 1)
    grids = []
    for i in range(av.N):
        ph = 2 * math.pi * i / av.N                                      # seno: loop exacto
        shift = a.parallax * W * math.sin(ph) * (depth - 0.5)            # near se mueve más que far
        sx = np.clip(xs - shift, 0, W - 1).astype(int)                   # mapeo inverso por fila
        warped = lum[ys, sx]
        d = depth[ys, sx]
        scan = 0.92 + 0.08 * np.sin((np.arange(H)[:, None] / 2.0) + ph)  # scanline sutil que recorre el frame
        small = np.asarray(Image.fromarray((np.clip(warped * scan, 0, 1) * 255).astype(np.uint8))
                           .resize((av.COLS, av.ROWS), Image.Resampling.BOX), float) / 255
        dsm = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).resize((av.COLS, av.ROWS), Image.Resampling.BOX), float) / 255
        idx = np.clip(np.rint(small ** 0.9 * (len(av.RAMP) - 1)), 0, len(av.RAMP) - 1).astype(int)
        mats = np.where(dsm > 0.66, av.MAT_PIN, np.where(dsm < 0.33, av.MAT_DIE, av.MAT_BODY))  # near=amarillo, far=azul
        grids.append((idx, mats))
    frames = [av.render_png_frame(*g) for g in grids]
    av.save_gif(frames, av.ASSETS / "avatar-photo.gif")
    av.save_svg(grids, av.ASSETS / "avatar-photo.svg")
    print("assets/avatar-photo.gif y .svg generados")


if __name__ == "__main__":
    main()
