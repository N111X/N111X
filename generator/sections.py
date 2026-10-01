"""Genera banner, cabeceras de sección, about, áreas, tarjetas de proyecto y pie (SVG)."""
import pathlib
import pyfiglet
from svgkit import *

ASSETS = HERE.parent / "assets"
W = 880  # ancho de página de GitHub (contenido del README)


def write(name, body, w, h, title, text_for_font, desc=""):
    svg = svg_open(w, h, title, desc) + style(text_for_font) + body + "</svg>"
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"  {name:22s} {len(svg)/1024:6.1f} KB")


def banner():
    c = CFG
    # Cada letra por separado + 3 espacios: sin el "smushing" de figlet las letras N-I-X quedan legibles
    blocks = [pyfiglet.figlet_format(ch, font="standard").rstrip("\n").split("\n") for ch in c["banner_text"]]
    rows = max(len(b) for b in blocks)
    blocks = [[l.ljust(max(len(x) for x in b)) for l in b] + [" " * max(len(x) for x in b)] * (rows - len(b)) for b in blocks]
    art = [("   ".join(b[i] for b in blocks)).rstrip() for i in range(rows)]
    size = 44
    cw = size * CHAR_W
    lh = size * 0.78
    cols = max(len(l) for l in art)
    x0 = (W - cols * cw) / 2
    y0 = 96
    h = int(y0 + len(art) * lh + 6 + 76 + 44)  # alto calculado: arte + regla + tagline + tags
    b = [frame(W, h)]
    b.append(text(34, 44, f"// {c['handle']}", 22, P["blue"], spacing=6))
    for i, l in enumerate(art):
        # el trazo del figlet va en acento (monocromo: más legible que partir las letras en dos colores)
        parts, cur, curc = [], "", None
        for ch in l:
            col = P["accent"]
            if col != curc and cur:
                parts.append((cur, curc)); cur = ""
            cur += ch; curc = col
        if cur: parts.append((cur, curc))
        b.append(runs(x0, y0 + i * lh, parts, size))
    ry = y0 + len(art) * lh + 6
    b.append(rule(120, W - 120, ry))
    b.append(text(W / 2, ry + 40, c["tagline"], 28, P["text"], anchor="middle"))
    tags = []
    for i, t in enumerate(c["tags"]):
        if i: tags.append((" · ", P["accent"]))
        tags.append((t, P["blue"]))
    n = sum(len(s) for s, _ in tags)
    b.append(runs(W / 2 - n * 24 * CHAR_W / 2, ry + 76, tags, 24))
    allt = "".join(art) + c["handle"] + c["tagline"] + " ".join(c["tags"]) + "// "
    write("banner.svg", "".join(b), W, h, f"{c['handle']} — banner", allt, c["tagline"])


def header(name, kicker):
    h = 56
    k = "// " + kicker.upper()
    b = [f'<rect width="{W}" height="{h}" fill="{P["bg"]}"/>',
         text(8, 30, k, 28, P["blue"], spacing=8),
         rule(8, W - 8, 46)]
    write(f"hdr-{name}.svg", "".join(b), W, h, kicker, k)


def about_box(w, h):
    a = CFG["about"]
    size = 22
    b = [frame(w, h)]
    y = 62
    for role, s in a["lines"]:
        b.append(text(34, y, s, size, role_color(role)))
        y += 34
        if role == "comment" and s == "// about":
            y += 6
    allt = "".join(s for _, s in a["lines"])
    plain = " ".join(s for _, s in a["lines"])
    write("about.svg", "".join(b), w, h, "about", allt, plain)


def areas():
    a = CFG["areas"]
    size = 26
    lh = 36
    h = 40 + 36 + lh * (len(a["items"]) + 1) + 24
    b = [frame(W, h)]
    y = 62
    b.append(runs(34, y, [("$ ", P["accent"]), ("tree ", P["text"]), ("./areas", P["purple"])], size))
    y += lh
    b.append(text(34, y, ".", size, P["dim"]))
    x_v = 40
    top = y + 6
    items = a["items"]
    for i, it in enumerate(items):
        y += lh
        last = i == len(items) - 1
        ymid = y - 8
        # conectores ├─ └─ dibujados con líneas (VT323 no trae box-drawing)
        b.append(f'<line x1="{x_v}" y1="{top if i==0 else y-lh-8}" x2="{x_v}" y2="{ymid}" stroke="{P["dim"]}" stroke-width="2"/>')
        if not last:
            b.append(f'<line x1="{x_v}" y1="{ymid}" x2="{x_v}" y2="{ymid+lh}" stroke="{P["dim"]}" stroke-width="2"/>')
        b.append(f'<line x1="{x_v}" y1="{ymid}" x2="{x_v+22}" y2="{ymid}" stroke="{P["dim"]}" stroke-width="2"/>')
        b.append(text(x_v + 34, y, it, size, P["text"]))
    allt = "$ tree ./areas." + "".join(items)
    write("areas.svg", "".join(b), W, h, "areas", allt, "areas: " + ", ".join(items))


def cards():
    for i, cd in enumerate(CFG["projects"]["cards"]):
        w, h = 280, 150
        b = [frame(w, h)]
        b.append(text(28, 44, cd["tag"].upper(), 20, P["blue"], spacing=4))
        b.append(text(28, 84, cd["name"], 36, P["accent"]))
        b.append(text(28, 112, cd["desc"], 20, P["text"]))
        short = cd["url"].replace("https://", "")
        b.append(text(28, 134, "> " + short, 17, P["dim"]))
        allt = cd["tag"].upper() + cd["name"] + cd["desc"] + "> " + short
        write(f"card-{i+1}.svg", "".join(b), w, h, cd["name"], allt, f"{cd['name']}: {cd['desc']}")


def footer():
    h = 72
    sig = CFG["footer"]
    b = [f'<rect width="{W}" height="{h}" fill="{P["bg"]}"/>', rule(8, W - 8, 24),
         text(W / 2, 58, sig, 22, P["dim"], spacing=3, anchor="middle")]
    write("footer.svg", "".join(b), W, h, "footer", sig)


def build_all(about_w, avatar_h_display):
    ASSETS.mkdir(exist_ok=True)
    print("[sections]")
    banner()
    for k in ("about", "stack", "areas", "projects", "stats"):
        header(k if k != "stack" else "arsenal", CFG[k]["kicker"])
    about_box(about_w, avatar_h_display)
    areas()
    cards()
    footer()
