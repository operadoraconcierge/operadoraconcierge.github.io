#!/usr/bin/env python3
"""Crea la instalación de una agencia nueva a partir de su archivo de marca.

No toca este repositorio ni la demo publicada: escribe todo en una carpeta nueva
que después se sube como repositorio propio de la agencia (GitHub Pages).

Uso:
    python3 herramientas/nueva_agencia.py agencias/ejemplo/agencia.json
    python3 herramientas/nueva_agencia.py agencias/ejemplo/agencia.json --destino ../agencia-altamira

Qué genera:
    marca/      logo (el de la agencia o uno de texto), íconos, marca.json con colores
    fotos/      fotos propias de demostración + fondo líquido en los colores de la agencia
    plantilla/  app del viajero
    herramientas/publicar.py
    viajes/     un viaje de demostración con los datos de la agencia
    .github/workflows/publicar.yml  publicación automática cada hora
    index.html, robots.txt, .nojekyll, README.md

IMPORTANTE: la app y el publicador actuales parten de código de terceros (Nunatak).
Esta salida sirve para demos internas; no se entrega a un cliente hasta terminar
la reescritura original (ver la propuesta para agencias).
"""
import argparse, json, random, re, shutil, string, subprocess, sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
# Solo fotos propias de Operadora Concierge (las de Patagonia no se distribuyen).
FOTOS_DEMO = ("strip", "sphere", "bellagio")
LETRA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OBLIGATORIOS = ("nombre", "corto", "prefijo_codigo", "concierge_nombre", "concierge_whatsapp")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def fuente(tam):
    try:
        return ImageFont.truetype(LETRA, tam)
    except OSError:
        return ImageFont.load_default()


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def validar(a):
    err = [f"Falta '{k}'" for k in OBLIGATORIOS if not a.get(k)]
    if a.get("prefijo_codigo") and not re.match(r"^[A-Z]{2,5}$", a["prefijo_codigo"]):
        err.append("prefijo_codigo debe ser de 2 a 5 letras mayúsculas (ej. ALT)")
    wa = re.sub(r"\D", "", str(a.get("concierge_whatsapp", "")))
    if wa and not (wa.startswith("52") and len(wa) in (12, 13)):
        err.append("concierge_whatsapp debe ser 52 + 10 dígitos (o 521 + 10)")
    for k, v in (a.get("colores") or {}).items():
        if not HEX.match(str(v)):
            err.append(f"colores.{k} debe ser un color #RRGGBB")
    return err


def silueta(img, color):
    """Copia del logo en un solo color, respetando la transparencia."""
    a = img.getchannel("A")
    out = Image.new("RGBA", img.size, color + (0,))
    out.putalpha(a)
    return out


def logo_texto(a, color):
    """Logo provisional de texto cuando la agencia no manda el suyo."""
    f1, f2 = fuente(220), fuente(70)
    t1, t2 = a["corto"], a["nombre"].upper()
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w1 = d.textbbox((0, 0), t1, font=f1)[2]
    w2 = d.textbbox((0, 0), t2, font=f2)[2]
    w = max(w1, w2) + 40
    img = Image.new("RGBA", (w, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20, 0), t1, font=f1, fill=color + (255,))
    d.text((24, 260), t2, font=f2, fill=color + (255,))
    return img.crop(img.getbbox())


def marca_cuadrada(a, fondo, tinta, tam):
    """Ícono: inicial de la agencia sobre su color."""
    img = Image.new("RGB", (tam, tam), fondo)
    d = ImageDraw.Draw(img)
    f = fuente(int(tam * .56))
    t = a["corto"][0].upper()
    x0, y0, x1, y1 = d.textbbox((0, 0), t, font=f)
    d.text(((tam - (x1 - x0)) / 2 - x0, (tam - (y1 - y0)) / 2 - y0), t, font=f, fill=tinta)
    return img


def preparar_marca(a, base_json, dest):
    m = dest / "marca"
    m.mkdir(parents=True)
    col = a.get("colores") or {}
    acento = hex_rgb(col.get("acento", "#4DB5EA"))
    barra = hex_rgb(col.get("barra", "#0B0B0B"))
    if a.get("logo"):
        logo = Image.open(base_json.parent / a["logo"]).convert("RGBA")
        logo = logo.crop(logo.getbbox())
        color = logo
    else:
        logo = logo_texto(a, (0, 0, 0))
        color = silueta(logo, acento)
    silueta(logo, (0, 0, 0)).save(m / "logo-negro.png")
    silueta(logo, (255, 255, 255)).save(m / "logo-blanco.png")
    color.save(m / "logo-color.png")
    # "estrella": marca pequeña que usa la app; para la agencia, su inicial
    est = Image.new("RGBA", (734, 734), (0, 0, 0, 0))
    d = ImageDraw.Draw(est)
    f = fuente(560)
    t = a["corto"][0].upper()
    x0, y0, x1, y1 = d.textbbox((0, 0), t, font=f)
    d.text(((734 - (x1 - x0)) / 2 - x0, (734 - (y1 - y0)) / 2 - y0), t, font=f, fill=(0, 0, 0, 255))
    est.save(m / "estrella-negro.png")
    silueta(est, (255, 255, 255)).save(m / "estrella-blanco.png")
    for n in (180, 192, 512):
        marca_cuadrada(a, barra, acento, n).save(m / f"icon-{n}.png")
    datos = {k: a[k] for k in ("nombre", "corto", "dominio", "web", "prefijo_codigo", "concierge_nombre",
                               "concierge_whatsapp", "concierge_telefono", "concierge_horario",
                               "colores", "tipografia") if a.get(k)}
    (m / "marca.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n")


def fondo_liquido(a, dest):
    """Recolorea el fondo líquido (generado por nosotros) con los colores de la agencia."""
    col = a.get("colores") or {}
    src = RAIZ / "fotos" / "fondo-liquido.jpg"
    if not src.exists():
        return
    gris = ImageOps.grayscale(Image.open(src))
    oscuro = tuple(int(c * .35) for c in hex_rgb(col.get("marca", "#1C93CE")))
    img = ImageOps.colorize(gris, black=oscuro, mid=col.get("marca", "#1C93CE"),
                            white=col.get("acento_suave", "#EEF4FF"))
    img.save(dest / "fotos" / "fondo-liquido.jpg", quality=78, optimize=True, progressive=True)


def viaje_demo(a, dest):
    t = json.loads((RAIZ / "viajes" / "OPC-2611-ORT-zlkhx.json").read_text())
    v = t["viaje"]
    clave = "".join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(5))
    codigo = f"{a['prefijo_codigo']}-{v['inicio'][2:4]}{v['inicio'][5:7]}-ORT"
    v.update({
        "codigo": codigo, "ruta": f"{codigo}-{clave}", "agencia": a["nombre"],
        "concierge_nombre": a["concierge_nombre"], "concierge_whatsapp": a["concierge_whatsapp"],
        "concierge_horario": a.get("concierge_horario", "24/7 durante su viaje"),
        "nota": "Viaje de demostración. Nombres, teléfonos y confirmaciones son ficticios.",
    })
    for k in ("liga", "actualizado"):
        t.pop(k, None)
    t["estado"] = "listo"
    for g in ("dias", "hoteles", "contactos"):
        for x in t.get(g) or []:
            if x.get("foto") and x["foto"] not in FOTOS_DEMO:
                x["foto"] = ""
    if v.get("foto_portada") not in FOTOS_DEMO:
        v["foto_portada"] = "strip"
    texto = json.dumps(t, ensure_ascii=False, indent=2)
    base = json.loads((RAIZ / "marca" / "marca.json").read_text())
    texto = texto.replace(base["nombre"], a["nombre"]).replace("Operadora Concierge", a["nombre"])
    (dest / "viajes" / f"{v['ruta']}.json").write_text(texto + "\n")
    return v["ruta"]


def portada(a, dest):
    col = a.get("colores") or {}
    barra, acento = col.get("barra", "#0B0B0B"), col.get("acento", "#4DB5EA")
    web = a.get("web", "")
    enlace = f'<p><a href="{web}">{a.get("dominio") or web}</a></p>' if web else ""
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow"><title>{a['nombre']}</title>
<link rel="icon" href="marca/icon-192.png"><link rel="apple-touch-icon" href="marca/icon-180.png">
<style>html,body{{margin:0;height:100%;background:{barra};color:#fff;font-family:system-ui,Arial,sans-serif}}
main{{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:24px;box-sizing:border-box}}
img{{width:220px;max-width:70vw}}h1{{font-weight:500;font-size:30px;margin:28px 0 8px}}p{{max-width:30em;opacity:.85;line-height:1.5}}a{{color:{acento}}}</style></head>
<body><main><img src="marca/logo-blanco.png" alt="{a['nombre']}"><h1>Su viaje, en el bolsillo</h1>
<p>App de concierge para viajeros de {a['nombre']}. Abra la liga personal que le compartimos en su grupo de WhatsApp.</p>
{enlace}</main></body></html>
"""
    (dest / "index.html").write_text(html)


WORKFLOW = """name: Publicar viajes
on:
  push:
    paths: ["viajes/**", "plantilla/**", "marca/**", "fotos/**"]
  schedule:
    - cron: "0 13-23,0-5 * * *"   # cada hora, 7:00 a 23:00 hora de CDMX
  workflow_dispatch:
permissions:
  contents: write
jobs:
  publicar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python3 herramientas/publicar.py
      - name: Subir cambios
        run: |
          git config user.name "publicador"
          git config user.email "publicador@users.noreply.github.com"
          git add -A
          git diff --cached --quiet || (git commit -m "Publicar viajes" && git push)
"""


def leeme(a, ruta):
    usuario = a.get("github_usuario", "<cuenta-de-la-agencia>")
    return f"""# {a['nombre']} · app concierge para viajeros

Instalación generada con `herramientas/nueva_agencia.py` desde la plantilla de Operadora Concierge.

## Publicar por primera vez
1. Crear el repositorio `{usuario}.github.io` en la cuenta de GitHub de la agencia.
2. Subir esta carpeta completa a la rama `main`.
3. En el repositorio: Settings → Pages → Source: rama `main`, carpeta raíz.
4. (Opcional) Dominio propio: Settings → Pages → Custom domain, y un registro CNAME en el DNS.
5. Viaje de demostración: https://{usuario}.github.io/{ruta}/

## Día a día
- Cada viaje es un archivo en `viajes/`. Con `"estado": "listo"` se publica en la siguiente hora
  (o al instante al subir el cambio). `"retirado"` borra la liga.
- Los colores, la letra y los datos del concierge están en `marca/marca.json`.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("agencia", help="ruta al agencia.json")
    ap.add_argument("--destino", help="carpeta de salida (por defecto ../agencia-<prefijo>)")
    args = ap.parse_args()
    archivo = Path(args.agencia).resolve()
    a = json.loads(archivo.read_text())
    err = validar(a)
    if err:
        print("✗ El archivo de la agencia tiene errores:")
        for e in err:
            print("   ·", e)
        sys.exit(1)
    dest = Path(args.destino or RAIZ.parent / f"agencia-{a['prefijo_codigo'].lower()}").resolve()
    if dest == RAIZ or RAIZ in dest.parents:
        sys.exit("✗ El destino no puede estar dentro de este repositorio.")
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"✗ {dest} ya existe y no está vacía.")
    for sub in ("fotos", "viajes", "herramientas", ".github/workflows"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    shutil.copytree(RAIZ / "plantilla", dest / "plantilla")
    shutil.copy2(RAIZ / "herramientas" / "publicar.py", dest / "herramientas" / "publicar.py")
    for f in FOTOS_DEMO:
        shutil.copy2(RAIZ / "fotos" / f"{f}.jpg", dest / "fotos" / f"{f}.jpg")
    preparar_marca(a, archivo, dest)
    fondo_liquido(a, dest)
    ruta = viaje_demo(a, dest)
    portada(a, dest)
    (dest / ".nojekyll").write_text("")
    (dest / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (dest / ".github/workflows/publicar.yml").write_text(WORKFLOW)
    (dest / "README.md").write_text(leeme(a, ruta))
    r = subprocess.run([sys.executable, str(dest / "herramientas" / "publicar.py")], cwd=dest)
    print(f"\n✓ Agencia lista en {dest}\n  Viaje de demostración: {ruta}/")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
