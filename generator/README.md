# Generador del README de perfil

Todo lo visual (banner, cabeceras, tarjetas, avatar) y el `README.md` raíz se generan desde
`config.json` + `README.tmpl.md`. **No edites `README.md` ni `assets/*` a mano**: se sobrescriben.

## Uso

```bash
pip install -r generator/requirements.txt      # Python 3.11, Pillow, numpy, pyfiglet, fonttools(+brotli)
make build-readme                              # o: npm run build-readme / python3 generator/build.py
make png                                       # opcional: PNG @2x de los SVG + avatar.apng (necesita Chromium de Playwright)
```

Si Playwright no encuentra su Chromium: `CHROMIUM_PATH=/ruta/a/chrome make png`.
Flags de `build.py`: `--only sections|avatar|readme`, `--png`, `--apng`, `--no-svg`.

## Qué genera

| Archivo | Origen |
|---|---|
| `assets/banner.svg` | figlet "Standard" (letra a letra, 3 espacios de separación) + tagline + tags |
| `assets/hdr-*.svg` | kicker azul `// X` + regla amarilla `──◆──` (dibujada con primitivas) |
| `assets/about.svg`, `areas.svg`, `card-N.svg`, `footer.svg` | `sections.py` |
| `assets/avatar.gif` / `avatar.svg` | `avatar.py` (Ruta A: chip QFP 3D procedural) |
| `README.md` | `README.tmpl.md` + `config.json` (badges de shields.io, tablas) |

## Avatar

**Ruta A (por defecto, `avatar.py`)**: modelo procedural (cuerpo, tapa, marca pin-1, 48 pines) → rotación Y 360°
con "asentimiento" sinusoidal → z-buffer con supersampling 3×3 → luminancia → rampa `" .:-=+*#%@"` → PIL → GIF.
No usa three.js ni navegador (decisión: reproducible con solo Python; `AsciiEffect` de three.js
mapea luminancia con el mismo principio). Loop perfecto por construcción: el frame `N` ≡ frame `0` (verificado).
Material → color: cuerpo=crema (tenue=`dim`), pines=acento, die=azul, marca=morado.

**Ruta B (`avatar_photo.py`)**: `python generator/avatar_photo.py --photo perfil.jpg [--depth depth.png]`.
Parallax 2.5D con oscilación sinusoidal (loop exacto). Sin `--depth` usa la luminancia como proxy de profundidad:
es una aproximación, no profundidad real. Para profundidad real genera el mapa con MiDaS fuera de este repo
(no se añade torch como dependencia). Salida: `assets/avatar-photo.{gif,svg}`; cambia la ruta en `README.tmpl.md`.
**Estado**: probada solo con una imagen sintética; falta probarla con tu foto real.

**GIF vs SVG**: los dos son frames discretos, así que la suavidad es la misma. El SVG (SMIL como `<img>`,
fuente embebida) es vectorial y pesa distinto; el GIF es el formato más robusto (apps móviles, visores sin SMIL).
Recomendado: GIF en el README. Tamaños actuales: ver salida de `make build-readme`.

## Personalizar

- **Textos, links, tags, áreas, proyectos**: `config.json`. Los `[PENDIENTE]` son datos sin rellenar.
- **Paleta**: `config.json → palette` (afecta SVG, GIF y badges generados por rol; los badges de shields
  llevan los hex en `stack.badges` y en `build.py`).
- **Fuente**: `config.json → font.file` (por defecto `fonts/VT323-Regular.ttf`, licencia OFL en `fonts/OFL.txt`).
  VT323 **no** trae `─ │ ├ └ ◆ →`; por eso reglas y árbol se dibujan con líneas/polígonos SVG.
  Cada SVG embebe la fuente subseteada en woff2/base64 (un SVG cargado como `<img>` no puede usar fuentes externas).
- **Modelo del avatar**: edita `build_chip()` en `avatar.py` (lista de `box(...)`). Para un `.obj`, sustituye
  `MODEL` por los triángulos `(v0,v1,v2,normal,material)` leídos del archivo.
- **Parámetros del avatar**: `config.json → avatar` (`cols`, `rows`, `frames`, `fps`, `tilt_deg`, `display_w`).

## Supuestos y límites

- Datos tomados del README anterior del perfil (handle, X, mail, nombres de repos); descripciones de repos y blog: `[PENDIENTE]`.
- Las tablas de GitHub dibujan bordes de celda propios: no se pueden quitar desde el README.
- Imágenes con fondo negro propio → se ven igual en tema claro y oscuro; no hace falta `<picture>`.
- Stats (github-readme-stats / streak) dependen de instancias públicas de terceros que pueden estar caídas o limitadas;
  desactívalo con `"stats.enabled": false`.
