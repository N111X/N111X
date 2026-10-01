"""Avatar 3D ASCII animado (Ruta A, sin navegador): modelo procedural de un chip QFP rotando
en Y. Pipeline: malla de triángulos -> rotación/proyección -> z-buffer con supersampling
-> luminancia por celda -> rampa de caracteres -> frame PIL -> GIF/APNG, y SVG animado (SMIL).
"""
import math, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from svgkit import *
from xml.sax.saxutils import escape

A = CFG["avatar"]
COLS, ROWS, FPX, N, FPS = A["cols"], A["rows"], A["font_px"], A["frames"], A["fps"]
RAMP, SS = A["ramp"], A["supersample"]
ASSETS = HERE.parent / "assets"
FONT = ImageFont.truetype(str(FONT_PATH), FPX)
CW = int(round(FONT.getlength("M")))          # ancho de celda (8 px a 20 px de fuente)
CH = int(round(FPX * 0.8))                   # alto de celda: ratio 1:2 típico de terminal
BASE = int(round(CH * 0.82))                 # baseline dentro de la celda
PADX, PADT, PADB = 28, 44, 22
CANVAS_W, CANVAS_H = PADX * 2 + COLS * CW, PADT + ROWS * CH + PADB
MAT_BODY, MAT_PIN, MAT_DIE, MAT_MARK = 0, 1, 2, 3


# ---------------------------------------------------------------- modelo --------------------
def box(cx, cy, cz, sx, sy, sz, mat):
    """Caja alineada a ejes -> 12 triángulos (v0,v1,v2, normal, mat), caras con winding externo."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = np.array([[x, y, z] for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]) + [cx, cy, cz]
    # caras: (índices de 4 vértices, normal)
    quads = [([4, 5, 7, 6], (1, 0, 0)), ([0, 2, 3, 1], (-1, 0, 0)),
             ([2, 6, 7, 3], (0, 1, 0)), ([0, 1, 5, 4], (0, -1, 0)),
             ([1, 3, 7, 5], (0, 0, 1)), ([0, 4, 6, 2], (0, 0, -1))]
    tris = []
    for q, n in quads:
        tris.append((v[q[0]], v[q[1]], v[q[2]], np.array(n, float), mat))
        tris.append((v[q[0]], v[q[2]], v[q[3]], np.array(n, float), mat))
    return tris


def build_chip(pins_per_side=12):
    """Cuerpo 10x1.4x10, tapa (die) azul, marca de pin 1 morada y 4x12 pines amarillos."""
    t = []
    t += box(0, 0, 0, 10, 2.2, 10, MAT_BODY)
    t += box(0, 1.2, 0, 4.6, 0.2, 4.6, MAT_DIE)
    t += box(-3.6, 1.18, 3.6, 0.9, 0.16, 0.9, MAT_MARK)
    pitch, pw = 0.72, 0.38
    span = (pins_per_side - 1) * pitch
    for i in range(pins_per_side):
        o = -span / 2 + i * pitch
        for sgn in (-1, 1):
            t += box(sgn * 5.9, -0.55, o, 1.8, 0.25, pw, MAT_PIN)   # pines laterales (±X)
            t += box(o, -0.55, sgn * 5.9, pw, 0.25, 1.8, MAT_PIN)   # pines frontales/traseros (±Z)
    return t


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


# ---------------------------------------------------------------- rasterizador --------------
LIGHT = np.array([-0.75, 0.55, 0.45]); LIGHT /= np.linalg.norm(LIGHT)


def rasterize(tris, theta, tilt):
    """Devuelve (mat, shade) a resolución de subcelda: mat=-1 fondo; shade en [0,1]."""
    H, W = ROWS * SS, COLS * SS
    zbuf = np.full((H, W), -1e9)
    mat = np.full((H, W), -1, np.int8)
    shade = np.zeros((H, W))
    R = rot_x(tilt) @ rot_y(theta)
    scale = min(CW * COLS, CH * ROWS) * 0.90 / 15.0
    # origen en píxeles del área de glifos; muestras en píxeles -> corrige el aspect de la celda
    cx, cy = COLS * CW / 2, ROWS * CH / 2
    sw, sh = CW / SS, CH / SS
    for v0, v1, v2, n, m in tris:
        nc = R @ n
        if nc[2] <= 0:               # back-face culling
            continue
        P3 = [R @ v for v in (v0, v1, v2)]
        pts = np.array([[cx + scale * p[0], cy - scale * p[1]] for p in P3])
        zs = np.array([p[2] for p in P3])
        lum = 0.12 + 0.88 * max(0.0, float(nc @ LIGHT))
        x0 = max(int(math.floor(pts[:, 0].min() / sw - 0.5)), 0)
        x1 = min(int(math.ceil(pts[:, 0].max() / sw)), W - 1)
        y0 = max(int(math.floor(pts[:, 1].min() / sh - 0.5)), 0)
        y1 = min(int(math.ceil(pts[:, 1].max() / sh)), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid((np.arange(x0, x1 + 1) + 0.5) * sw, (np.arange(y0, y1 + 1) + 0.5) * sh)
        (ax, ay), (bx, by), (qx, qy) = pts
        den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
        if abs(den) < 1e-9:
            continue
        l0 = ((by - qy) * (gx - qx) + (qx - bx) * (gy - qy)) / den
        l1 = ((qy - ay) * (gx - qx) + (ax - qx) * (gy - qy)) / den
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        z = l0 * zs[0] + l1 * zs[1] + l2 * zs[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sub)
        sub[win] = z[win]
        mat[y0:y1 + 1, x0:x1 + 1][win] = m
        shade[y0:y1 + 1, x0:x1 + 1][win] = lum
    # atenuación por profundidad: lo cercano brilla más -> gradiente sobre las caras planas
    zn = np.clip((zbuf + 6) / 12, 0, 1)
    shade = shade * (0.42 + 0.58 * zn)
    return mat, shade


def to_cells(mat, shade):
    """Agrega subceldas -> (índice de rampa, material dominante) por celda."""
    cov = (mat >= 0)
    c = cov.reshape(ROWS, SS, COLS, SS).sum(axis=(1, 3))
    s = (shade * cov).reshape(ROWS, SS, COLS, SS).sum(axis=(1, 3))
    lum = (s / (SS * SS)) ** 0.75                      # gamma suave: aclara medios tonos
    idx = np.clip(np.rint(lum * (len(RAMP) - 1) * 1.15), 0, len(RAMP) - 1).astype(int)
    idx[(c > 0) & (idx == 0)] = 1                      # celda tocada nunca queda vacía
    idx[c == 0] = 0
    counts = np.stack([((mat == k).reshape(ROWS, SS, COLS, SS).sum(axis=(1, 3))) for k in range(4)])
    return idx, counts.argmax(axis=0)


def frame_grid(i):
    th = 2 * math.pi * i / N
    tilt = math.radians(A["tilt_deg"] + 4 * math.sin(2 * math.pi * i / N))  # "asentimiento": loop exacto
    return to_cells(*rasterize(MODEL, th, tilt))


MODEL = build_chip()


# ---------------------------------------------------------------- color por rol -------------
def hex2rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(round(a[k] * (1 - t) + b[k] * t)) for k in range(3))


def cell_color(m, k):
    """Material -> color de la paleta; las celdas tenues (rampa baja) se atenúan hacia 'dim'/fondo."""
    bg = hex2rgb(P["bg"])
    if m == MAT_BODY:
        return hex2rgb(P["text"]) if k >= 4 else hex2rgb(P["dim"])
    base = hex2rgb({MAT_PIN: P["accent"], MAT_DIE: P["blue"], MAT_MARK: P["purple"]}[m])
    return base if k >= 4 else mix(base, bg, 0.45)


# ---------------------------------------------------------------- salida: frames PIL --------
def render_png_frame(idx, mats):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), hex2rgb(P["bg"]))
    d = ImageDraw.Draw(img)
    a, ln = hex2rgb(P["accent"]), hex2rgb(P["line"])
    d.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=a, width=2)          # filete 2px
    d.rectangle([10, 10, CANVAS_W - 11, CANVAS_H - 11], outline=ln, width=1)      # filete 1px a 10px
    for (x, y, dx, dy) in [(5, 5, 1, 1), (CANVAS_W - 5, 5, -1, 1), (5, CANVAS_H - 5, 1, -1),
                           (CANVAS_W - 5, CANVAS_H - 5, -1, -1)]:                  # esquinas en L
        d.line([(x + dx * 18, y), (x, y), (x, y + dy * 18)], fill=a, width=3)
    for j, ch in enumerate(A["label"]):                                            # kicker con tracking
        d.text((PADX + j * (CW + 2), 34), ch, font=FONT, fill=hex2rgb(P["blue"]), anchor="ls")
    for r in range(ROWS):
        for c in range(COLS):
            k = idx[r, c]
            if k:
                d.text((PADX + c * CW, PADT + r * CH + BASE), RAMP[k], font=FONT,
                       fill=cell_color(mats[r, c], k), anchor="ls")
    return img


def build_frames():
    grids = [frame_grid(i) for i in range(N)]
    return grids, [render_png_frame(*g) for g in grids]


def save_gif(frames, path):
    # Una paleta GLOBAL (de un montaje de todos los frames) evita parpadeo de colores entre frames.
    sheet = Image.new("RGB", (CANVAS_W, CANVAS_H * 4))
    for j, f in enumerate(frames[:: max(1, len(frames) // 4)][:4]):
        sheet.paste(f, (0, j * CANVAS_H))
    pal = sheet.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / FPS), loop=0,
              optimize=False, disposal=1)


def save_apng(frames, path):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / FPS), loop=0)


# ---------------------------------------------------------------- salida: SVG animado -------
def save_svg(grids, path):
    """Un <g> por frame; visibilidad conmutada con SMIL (calcMode=discrete). Funciona como <img>."""
    dur = N / FPS
    body, chars = [frame(CANVAS_W, CANVAS_H)], set(A["label"]) | set(RAMP)
    body.append(text(PADX, 34, A["label"], FPX, P["blue"], spacing=2))
    for i, (idx, mats) in enumerate(grids):
        if i == 0:
            vals, kt = "visible;hidden", "0;" + f"{1 / N:.5f}"
        elif i == N - 1:
            vals, kt = "hidden;visible", "0;" + f"{i / N:.5f}"
        else:
            vals, kt = "hidden;visible;hidden", f"0;{i / N:.5f};{(i + 1) / N:.5f}"
        g = [f'<g visibility="hidden"><animate attributeName="visibility" dur="{dur:g}s" '
             f'repeatCount="indefinite" calcMode="discrete" values="{vals}" keyTimes="{kt}"/>']
        for r in range(ROWS):
            row, run, cur = [], "", None
            for c in range(COLS):
                k = idx[r, c]
                col = "#%02x%02x%02x" % cell_color(mats[r, c], k) if k else None
                ch = RAMP[k] if k else " "
                if col != cur and run:
                    row.append((run, cur)); run = ""
                run += ch; cur = col if k else cur if run.strip() == "" and False else (col or cur)
            if run: row.append((run, cur))
            if not "".join(s for s, _ in row).strip():
                continue
            ts = "".join(f'<tspan fill="{c or P["bg"]}">{escape(s)}</tspan>' for s, c in row)
            g.append(f'<text x="{PADX}" y="{PADT + r * CH + BASE}" font-size="{FPX}">{ts}</text>')
        g.append("</g>")
        body.append("".join(g))
    svg = (svg_open(CANVAS_W, CANVAS_H, "avatar ASCII 3D", "chip QFP rotando en Y, ASCII animado")
           + style("".join(chars)) + "".join(body) + "</svg>")
    path.write_text(svg, encoding="utf-8")


def build(apng=False, svg=True):
    print("[avatar]")
    grids, frames = build_frames()
    save_gif(frames, ASSETS / "avatar.gif")
    print(f"  avatar.gif  {(ASSETS/'avatar.gif').stat().st_size/1024:.0f} KB  {CANVAS_W}x{CANVAS_H}  {N} frames @ {FPS} fps")
    if apng:
        save_apng(frames, ASSETS / "avatar.apng")
    if svg:
        save_svg(grids, ASSETS / "avatar.svg")
        print(f"  avatar.svg  {(ASSETS/'avatar.svg').stat().st_size/1024:.0f} KB")
    frames[N // 3].save(HERE / "preview.png")  # solo para inspección local (ignorado por git)
