#!/usr/bin/env python3
"""Regenera todos los assets y el README.md de perfil.  Uso: python generator/build.py [--png] [--apng] [--no-svg] [--only sections|avatar|readme]"""
import argparse, sys, urllib.parse
sys.path.insert(0, __import__("pathlib").Path(__file__).parent.as_posix())
from svgkit import CFG, HERE, P
import sections

ROOT = HERE.parent
AV_W = CFG["avatar"]["display_w"]  # ancho con el que se muestra el avatar en el README


def shield(label, logo, color, link=None, logo_color="000000"):
    """Badge shields.io estilo flat-square con colores de la paleta (&color=RRGGBB sin #)."""
    q = {"style": "flat-square", "labelColor": "000000", "logoColor": logo_color}
    if logo:
        q["logo"] = logo
    url = ("https://img.shields.io/badge/" + urllib.parse.quote(label, safe="").replace("-", "--") +
           f"-{color}?" + urllib.parse.urlencode(q))
    img = f'<img src="{url}" alt="{label}">'
    return f'<a href="{link}">{img}</a>' if link else img


def render_readme():
    import avatar
    c = CFG
    badges = "\n".join(shield(l, lg, col) for l, lg, col in c["stack"]["badges"])
    cards = "\n".join(
        f'<td width="33%"><a href="{cd["url"]}"><img src="assets/card-{i+1}.svg" width="280" '
        f'alt="{cd["name"]} — {cd["desc"]}"></a></td>' for i, cd in enumerate(c["projects"]["cards"]))
    h = ""
    if c["stats"]["enabled"]:
        u = c["handle"]
        pal = f"bg_color=000000&title_color=ffd400&text_color=e9e9e9&icon_color=6d9eff&border_color=333333&hide_border=false"
        stats = (f'<img src="https://github-readme-stats.vercel.app/api?username={u}&show_icons=true&{pal}&ring_color=ffd400" '
                 f'height="150" alt="GitHub stats">\n'
                 f'<img src="https://streak-stats.demolab.com/?user={u}&background=000000&border=333333&stroke=333333'
                 f'&ring=ffd400&fire=ffd400&currStreakNum=e9e9e9&currStreakLabel=ffd400&sideNums=e9e9e9&sideLabels=6d9eff'
                 f'&dates=5f7cc0" height="150" alt="GitHub streak">')
        h = ('\n<img src="assets/hdr-stats.svg" width="880" alt="// STATS">\n\n<p align="left">\n' + stats + "\n</p>\n")
    L = c["links"]
    contact = " ".join([shield("X", "x", "ffd400", L["x"]), shield("GitHub", "github", "6d9eff", L["github"]),
                        shield("Mail", "gmail", "c586ff", L["mail"]),
                        shield("Blog " + L["blog"], "", "5f7cc0", None, "ffffff")])
    rep = {"handle": c["handle"], "tagline": c["tagline"], "tags_joined": " · ".join(c["tags"]),
           "avatar_w": AV_W, "about_w": sections.W - AV_W - 56,  # 56 = padding de celdas de tabla de GitHub
           "about_plain": " ".join(s for _, s in c["about"]["lines"]).replace('"', "'"),
           "areas_plain": ", ".join(c["areas"]["items"]), "badges": badges, "cards": cards,
           "stats": h, "contact": contact, "footer": c["footer"]}
    t = (HERE / "README.tmpl.md").read_text(encoding="utf-8")
    for k, v in rep.items():
        t = t.replace("{{" + k + "}}", str(v))
    (ROOT / "README.md").write_text(t, encoding="utf-8")
    print("[readme] README.md")


def export_png():
    """SVG -> PNG con Chromium headless (Playwright). Opcional: solo si pasas --png."""
    from playwright.sync_api import sync_playwright
    names = ["banner", "hdr-about", "hdr-arsenal", "hdr-areas", "hdr-projects", "hdr-stats", "about", "areas",
             "card-1", "card-2", "card-3", "footer"]
    with sync_playwright() as pw:
        exe = __import__("os").environ.get("CHROMIUM_PATH")  # p. ej. /opt/pw-browsers/chromium-1194/chrome-linux/chrome
        b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        for n in names:
            pg = b.new_page(device_scale_factor=2)
            pg.goto((ROOT / "assets" / f"{n}.svg").as_uri())
            pg.wait_for_timeout(150)
            pg.locator("svg").first.screenshot(path=str(ROOT / "assets" / f"{n}.png"))
            pg.close()
        b.close()
    print(f"[png] {len(names)} PNG @2x")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", action="store_true"); ap.add_argument("--apng", action="store_true")
    ap.add_argument("--no-svg", action="store_true"); ap.add_argument("--only", choices=["sections", "avatar", "readme"])
    a = ap.parse_args()
    import avatar
    if a.only in (None, "sections"):
        sections.build_all(sections.W - AV_W - 56, round(AV_W * avatar.CANVAS_H / avatar.CANVAS_W))
    if a.only in (None, "avatar"):
        avatar.build(apng=a.apng, svg=not a.no_svg)
    if a.only in (None, "readme"):
        render_readme()
    if a.png:
        export_png()
