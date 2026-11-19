"""Genera banner, cabeceras (folds), about, áreas, tarjetas y pie como ventanas de Vim (elflord)."""
import pyfiglet
from svgkit import *

ASSETS = HERE.parent / "assets"
W = 880  # ancho de página de GitHub (contenido del README)
ART_SIZE = 35  # figlet: 35 px -> avance 14 px y alto de fila 28 px = PITCH (rejilla común)


def write(name, body, w, h, title, text_for_font, desc=""):
    svg = svg_open(w, h, title, desc) + style(text_for_font + "~[]-+:") + body + "</svg>"
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"  {name:22s} {len(svg)/1024:6.1f} KB")


def figlet_art(txt):
    # Cada letra por separado + 3 espacios: sin el "smushing" de figlet, N-I-X quedan legibles.
    blocks = [pyfiglet.figlet_format(ch, font="standard").rstrip("\n").split("\n") for ch in txt]
    rows = max(len(b) for b in blocks)
    wd = [max(len(x) for x in b) for b in blocks]
    blocks = [[l.ljust(w) for l in b] + [" " * w] * (rows - len(b)) for b, w in zip(blocks, wd)]
    return [("   ".join(b[i] for b in blocks)).rstrip() for i in range(rows)]


def banner():
    c = CFG
    art = figlet_art(c["banner_text"])
    rows = [("txt", [(f"// {c['handle']}", P["comment"])]), ("blank",)]
    rows += [("txt", [(l, P["constant"])], ART_SIZE) for l in art]   # Title/Constant: magenta
    rows += [("blank",), ("txt", [(c["tagline"], P["text"])])]
    tags = []
    for i, t in enumerate(c["tags"]):
        if i:
            tags.append((" · ", P["comment"]))
        tags.append((t, P["type"]))                                  # Type: verde
    rows += [("txt", tags), ("tilde",), ("tilde",)]
    h = 8 + len(rows) * PITCH + 4 + STATUS_H
    buf, used = buffer_rows(rows)
    body = window(W, h, f"{c['handle']} [RO]", "1,1          Top") + buf
    write("banner.svg", body, W, h, f"{c['handle']} — banner",
          used + "".join(art) + c["handle"] + " [RO]1,1 Top", c["tagline"] + " · " + " · ".join(c["tags"]))


def header(name, kicker):
    body, s = fold(W, kicker.upper())
    write(f"hdr-{name}.svg", body, W, PITCH, kicker, s)


def about_box(w, h):
    a = CFG["about"]
    cap = (h - STATUS_H - 8) // PITCH
    rows = [("txt", [(s, role_color(r))]) for r, s in a["lines"]]
    rows += [("tilde",)] * max(0, cap - len(rows))
    buf, used = buffer_rows(rows[:cap])
    body = window(w, h, "about.md [RO]", "1,1   All") + buf
    plain = " ".join(s for _, s in a["lines"])
    write("about.svg", body, w, h, "about", used + plain + "about.md [RO]1,1 All", plain)


def areas():
    a = CFG["areas"]
    items = a["items"]
    rows = [("txt", [("$ ", P["special"]), ("tree ", P["white"]), ("./areas", P["constant"])]),
            ("txt", [(".", P["comment"])])]
    rows += [("txt", [("      " + it, P["type"])]) for it in items]
    rows += [("tilde",)]
    h = 8 + len(rows) * PITCH + 4 + STATUS_H
    buf, used = buffer_rows(rows)
    # conectores ├─ └─ dibujados con líneas (VT323 no trae box-drawing), en Comment
    xv = X0 + 6
    top = lambda r: 8 + r * PITCH
    first, last = 2, 1 + len(items)
    conn = [f'<line x1="{xv}" y1="{top(1) + 20}" x2="{xv}" y2="{top(last) + 14}" stroke="{P["comment"]}" stroke-width="2"/>']
    for r in range(first, last + 1):
        conn.append(f'<line x1="{xv}" y1="{top(r) + 14}" x2="{xv + 22}" y2="{top(r) + 14}" stroke="{P["comment"]}" stroke-width="2"/>')
    body = window(W, h, "areas [RO]", f"1,1   All") + buf + "".join(conn)
    write("areas.svg", body, W, h, "areas", used + "$ tree ./areas." + "".join(items) + "areas [RO]1,1 All",
          "areas: " + ", ".join(items))


def cards():
    for i, cd in enumerate(CFG["projects"]["cards"]):
        w, h = 280, 150
        short = cd["url"].replace("https://", "")
        b = [window(w, h, f"{cd['name']} [RO]", "1,1"),
             text(14, 30, "// " + cd["tag"], 18, P["comment"]),
             text(14, 68, cd["name"], 32, P["type"]),
             text(14, 94, cd["desc"], 20, P["text"]),
             text(14, 116, short, 17, P["comment"], extra=' text-decoration="underline"')]   # Underlined
        allt = "// " + cd["tag"] + cd["name"] + cd["desc"] + short + f"{cd['name']} [RO]1,1"
        write(f"card-{i+1}.svg", "".join(b), w, h, cd["name"], allt, f"{cd['name']}: {cd['desc']}")


def footer():
    h = 36
    sig = CFG["footer"]
    b = [f'<rect width="{W}" height="{h}" fill="{P["bg"]}"/>',
         text(8, 24, "-- NORMAL --", SZ, P["text"], extra=f' stroke="{P["text"]}" stroke-width="0.4"'),   # ModeMsg: negrita
         text(W - 8, 24, sig, SZ, P["comment"], anchor="end")]
    write("footer.svg", "".join(b), W, h, "footer", "-- NORMAL --" + sig, sig)


def build_all(about_w, avatar_h_display):
    ASSETS.mkdir(exist_ok=True)
    print("[sections]")
    banner()
    for k in ("about", "stack", "areas", "projects", "snake", "stats"):
        header(k if k != "stack" else "arsenal", CFG[k]["kicker"])
    about_box(about_w, avatar_h_display)
    areas()
    cards()
    footer()
