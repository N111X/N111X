"""Primitivas SVG compartidas: fuente embebida, marco de doble filete, reglas, texto."""
import base64, io, json, pathlib
from xml.sax.saxutils import escape
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
P = CFG["palette"]
FONT_PATH = HERE / CFG["font"]["file"]
FAMILY = CFG["font"]["family"]
CHAR_W = 0.4  # avance de VT323 = 0.4 em (verificado: hmtx['M']=400 / upem 1000)


def font_face_css(text: str) -> str:
    """@font-face con VT323 subseteada (solo los glifos usados) en woff2 base64.
    Un SVG servido como <img> NO puede cargar fuentes externas: hay que embeberla."""
    opts = subset.Options(flavor="woff2", layout_features=[])
    f = TTFont(str(FONT_PATH))
    s = subset.Subsetter(opts)
    s.populate(text="".join(sorted(set(text))) + " ")
    s.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return ("@font-face{font-family:'VT323';src:url(data:font/woff2;base64," + b64 +
            ") format('woff2');}")


def style(text: str, extra: str = "") -> str:
    return ("<style>" + font_face_css(text) +
            f"text{{font-family:{FAMILY};font-variant-ligatures:none;"
            "font-feature-settings:\"liga\" 0,\"calt\" 0;white-space:pre;}"
            + extra + "</style>")


def svg_open(w, h, title, desc=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title>' + (f'<desc>{escape(desc)}</desc>' if desc else ""))


def frame(w, h, corners=True):
    """Caja de terminal: fondo negro, filete exterior 2px (acento), interior 1px a 10px
    (línea) y cuatro marcas de esquina en L (acento)."""
    a, ln = P["accent"], P["line"]
    out = [f'<rect width="{w}" height="{h}" fill="{P["bg"]}"/>',
           f'<rect x="1" y="1" width="{w-2}" height="{h-2}" fill="none" stroke="{a}" stroke-width="2"/>',
           f'<rect x="10.5" y="10.5" width="{w-21}" height="{h-21}" fill="none" stroke="{ln}" stroke-width="1"/>']
    if corners:
        L = 18
        for (x, y, dx, dy) in [(5, 5, 1, 1), (w-5, 5, -1, 1), (5, h-5, 1, -1), (w-5, h-5, -1, -1)]:
            out.append(f'<path d="M{x+dx*L} {y} H{x} V{y+dy*L}" fill="none" stroke="{a}" stroke-width="3"/>')
    return "".join(out)


def rule(x1, x2, y, color=None):
    """Regla  ──────  ◆  ──────  dibujada con primitivas (VT323 no trae ─ ni ◆)."""
    c = color or P["accent"]
    mid = (x1 + x2) / 2
    gap = 14
    return (f'<line x1="{x1}" y1="{y}" x2="{mid-gap}" y2="{y}" stroke="{c}" stroke-width="2"/>'
            f'<line x1="{mid+gap}" y1="{y}" x2="{x2}" y2="{y}" stroke="{c}" stroke-width="2"/>'
            f'<path d="M{mid} {y-6} L{mid+6} {y} L{mid} {y+6} L{mid-6} {y} Z" fill="{c}"/>')


def text(x, y, s, size, fill, spacing=0, anchor="start", extra=""):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}{extra}>'
            f'{escape(s)}</text>')


def runs(x, y, parts, size):
    """Una línea con tramos de color: parts=[(texto, color), ...] -> <text><tspan/></text>."""
    t = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)
    return f'<text x="{x}" y="{y}" font-size="{size}">{t}</text>'


def role_color(role):
    return {"comment": P["blue"], "plain": P["text"], "kw": P["accent"],
            "value": P["purple"], "dim": P["dim"], "add": P["blue_light"]}[role]
