"""Primitivas SVG compartidas: fuente embebida y piezas de "ventana de Vim" (elflord)."""
import base64, io, json, pathlib
from xml.sax.saxutils import escape
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = pathlib.Path(__file__).parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
P = CFG["palette"]
FONT_PATH = HERE / CFG["font"]["file"]
FAMILY = CFG["font"]["family"]
CHAR_W = 0.4          # avance de VT323 = 0.4 em (hmtx['M']=400 / upem 1000)
STATUS_H = 24         # alto de la statusline
PITCH, SZ, BASE = 28, 22, 20   # rejilla de filas del buffer: paso, tamaño de fuente, baseline
GX, X0 = 44, 60       # borde derecho de la columna de números y x del texto


def font_face_css(text: str) -> str:
    """@font-face con VT323 subseteada (solo glifos usados) en woff2/base64: un SVG cargado como
    <img> no puede usar fuentes externas, hay que embeberla."""
    opts = subset.Options(flavor="woff2", layout_features=[])
    f = TTFont(str(FONT_PATH), recalcTimestamp=False)  # sin marca de tiempo -> build determinista
    s = subset.Subsetter(opts)
    s.populate(text="".join(sorted(set(text))) + " ")
    s.subset(f)
    f.flavor = "woff2"
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return ("@font-face{font-family:'VT323';src:url(data:font/woff2;base64," + b64 + ") format('woff2');}")


def style(text: str, extra: str = "") -> str:
    return ("<style>" + font_face_css(text) +
            f"text{{font-family:{FAMILY};font-variant-ligatures:none;"
            "font-feature-settings:\"liga\" 0,\"calt\" 0;white-space:pre;}" + extra + "</style>")


def svg_open(w, h, title, desc=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'
            + (f'<desc>{escape(desc)}</desc>' if desc else ""))


def text(x, y, s, size, fill, spacing=0, anchor="start", extra=""):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}{extra}>'
            f'{escape(s)}</text>')


def runs(x, y, parts, size, extra=""):
    """Una línea con tramos de color: parts=[(texto, color), ...]."""
    t = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)
    return f'<text x="{x}" y="{y}" font-size="{size}"{extra}>{t}</text>'


def status_bar(w, h, left, right, sh=STATUS_H, fs=20):
    """StatusLine de elflord: negro sobre cyan, en negrita (stroke fino = negrita falsa en VT323)."""
    y = h - sh
    by = y + sh - (sh - fs) // 2 - 4
    bold = f' stroke="{P["status_fg"]}" stroke-width="0.5"'
    return (f'<rect x="0" y="{y}" width="{w}" height="{sh}" fill="{P["status_bg"]}"/>'
            + text(8, by, left, fs, P["status_fg"], extra=bold)
            + text(w - 8, by, right, fs, P["status_fg"], anchor="end", extra=bold))


def window(w, h, left, right, sh=STATUS_H, fs=20):
    """Ventana de Vim: fondo negro + statusline abajo."""
    return f'<rect width="{w}" height="{h}" fill="{P["bg"]}"/>' + status_bar(w, h, left, right, sh, fs)


def fold(w, label, size=SZ):
    """Cabecera de sección como fold cerrado de Vim: `+-- LABEL ------` cyan sobre gris (Folded)."""
    cols = int(w / (size * CHAR_W))
    s = "+-- " + label + " "
    s += "-" * max(0, cols - len(s))
    return (f'<rect width="{w}" height="{PITCH}" fill="{P["fold_bg"]}"/>'
            + text(0, 20, s, size, P["text"])), s


def tilde(x, y):
    """`~` de fin de buffer (NonText) como onda vectorial: el glifo de VT323 queda ambiguo a ~22 px."""
    return (f'<path d="M{x} {y - 5} q4 -6 8 0 t8 0" fill="none" stroke="{P["nontext"]}" stroke-width="2.2" '
            'stroke-linecap="round"/>')


def buffer_rows(rows, x0=X0, gx=GX, top=8):
    """Dibuja filas de buffer. rows: lista de ("txt", [(s,color)...], size) | ("blank",) | ("tilde",).
    Números de línea amarillos (LineNr) en txt/blank; `~` azul (NonText) en filas vacías de fin de buffer.
    Devuelve (svg, texto_usado)."""
    out, used, n = [], "", 0
    for i, r in enumerate(rows):
        base = top + i * PITCH + BASE
        if r[0] == "tilde":
            out.append(tilde(x0, base))
            continue
        n += 1
        out.append(text(gx, base, str(n), SZ, P["linenr"], anchor="end"))
        used += str(n)
        if r[0] == "txt":
            size = r[2] if len(r) > 2 else SZ
            out.append(runs(x0, base, r[1], size))
            used += "".join(s for s, _ in r[1])
    return "".join(out), used


def role_color(role):
    return {"comment": P["comment"], "plain": P["text"], "kw": P["statement"],
            "value": P["constant"], "dim": P["dim"], "add": P["identifier"]}[role]
