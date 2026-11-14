#!/usr/bin/env python3
"""Publica los viajes marcados como "listo".

Lee cada archivo de viajes/*.json y, si su publicacion.estado es "listo",
genera la carpeta <ruta>/ con la app del viajero (index.html, manifest,
service worker e íconos). Si el estado es "retirado", borra la carpeta.
Los viajes en "borrador" no se tocan: la liga sigue mostrando la última
versión publicada (o no existe todavía).

Uso:  python3 herramientas/publicar.py            # publica
      python3 herramientas/publicar.py --revisar  # solo valida, no escribe
"""
import base64, hashlib, json, mimetypes, re, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TIPOS = {"vuelo", "traslado", "hotel", "restaurante", "excursion", "opcional", "libre"}
RUTA_OK = re.compile(r"^[A-Z]{2,5}-\d{4}-[A-Z]{2,4}-[a-z0-9]{5,}$")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HORA = re.compile(r"^\d{2}:\d{2}$")


def validar(t):
    """Devuelve (errores, avisos)."""
    err, av = [], []
    v = t.get("viaje") or {}
    for k in ("codigo", "ruta", "programa", "saludo", "inicio", "fin", "zona_casa", "concierge_whatsapp"):
        if not v.get(k):
            err.append(f"Falta viaje.{k}")
    if v.get("ruta") and not RUTA_OK.match(v["ruta"]):
        err.append(f"La ruta '{v['ruta']}' no tiene el formato OPC-AAMM-XXX-abcde")
    if re.sub(r"\D", "", str(v.get("concierge_whatsapp", ""))).endswith("00000000"):
        av.append("El WhatsApp del concierge es genérico (cámbialo por el definitivo)")
    dias = t.get("dias") or []
    if not dias:
        err.append("El viaje no tiene días")
    fechas = set()
    for d in dias:
        if not FECHA.match(d.get("fecha", "")):
            err.append(f"Día con fecha inválida: {d.get('fecha')}")
        if not d.get("zona"):
            err.append(f"El día {d.get('fecha')} no tiene zona horaria")
        fechas.add(d.get("fecha"))
    ids = {c.get("id") for c in t.get("contactos") or []}
    for i, s in enumerate(t.get("servicios") or [], 1):
        etiqueta = f"Servicio {i} ({s.get('titulo') or 'sin título'})"
        if s.get("tipo") not in TIPOS:
            err.append(f"{etiqueta}: tipo '{s.get('tipo')}' desconocido")
        if s.get("fecha") not in fechas:
            err.append(f"{etiqueta}: la fecha {s.get('fecha')} no está entre los días del viaje")
        if not HORA.match(s.get("hora") or ""):
            err.append(f"{etiqueta}: hora inválida '{s.get('hora')}'")
        if s.get("contacto") and s["contacto"] not in ids:
            av.append(f"{etiqueta}: el contacto '{s['contacto']}' no está en el equipo")
    return err, av


def foto_uri(clave, cache={}):
    if not clave or re.match(r"^(https?:|data:)", clave):
        return None
    if clave in cache:
        return cache[clave]
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = RAIZ / "fotos" / f"{clave}.{ext}"
        if p.exists():
            mt = mimetypes.guess_type(p.name)[0] or "image/jpeg"
            cache[clave] = f"data:{mt};base64," + base64.b64encode(p.read_bytes()).decode()
            return cache[clave]
    cache[clave] = None
    return None


def claves_foto(t):
    v = t["viaje"]
    out = {v.get("foto_portada"), v.get("foto_concierge") or "campana"}
    for grupo in ("dias", "hoteles", "contactos"):
        out |= {x.get("foto") for x in t.get(grupo) or []}
    return {k for k in out if k}


def json_html(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def construir(t, marca, plantilla, logo):
    t = dict(t)
    t["marca"] = {k: marca[k] for k in ("nombre", "corto", "dominio", "web") if k in marca}
    for k in ("publicacion", "estado", "liga", "actualizado", "pedido"):
        t.pop(k, None)
    imgs = {k: u for k in sorted(claves_foto(t)) if (u := foto_uri(k))}
    v = t["viaje"]
    html = (plantilla
            .replace("__TRIP__", json_html(t))
            .replace("__IMGS__", json_html(imgs))
            .replace("__LOGO__", logo)
            .replace("__APP_TITLE__", marca["corto"])
            .replace("__TITLE__", f"{marca['nombre']} · {v['programa']}"))
    manifest = {
        "name": f"{marca['corto']} · {v['programa']}",
        "short_name": marca["corto"],
        "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#0B0B0B", "theme_color": "#0B0B0B", "lang": "es",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    version = hashlib.sha1(html.encode()).hexdigest()[:10]
    sw = (RAIZ / "plantilla" / "sw.js").read_text().replace("__CACHE__", f"opc-{v['codigo']}-{version}")
    return {"index.html": html, "manifest.webmanifest": json.dumps(manifest, ensure_ascii=False, indent=1), "sw.js": sw}


def escribir_si_cambia(p, contenido):
    if isinstance(contenido, str):
        contenido = contenido.encode()
    if p.exists() and p.read_bytes() == contenido:
        return False
    p.write_bytes(contenido)
    return True


def main():
    solo_revisar = "--revisar" in sys.argv
    marca = json.loads((RAIZ / "marca" / "marca.json").read_text())
    plantilla = (RAIZ / "plantilla" / "app.html").read_text()
    logo = re.sub(r"<title>.*?</title>", "", (RAIZ / "marca" / "logo.svg").read_text().strip())
    hubo_error = False
    for f in sorted((RAIZ / "viajes").glob("*.json")):
        try:
            t = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            print(f"✗ {f.name}: el archivo no es JSON válido ({e})")
            hubo_error = True
            continue
        # Formato del panel (base de datos): estado arriba; "publicado" se sigue reconstruyendo
        estado = t.get("estado") or (t.get("publicacion") or {}).get("estado", "borrador")
        if estado == "publicado":
            estado = "listo"
        ruta = (t.get("viaje") or {}).get("ruta", "")
        destino = RAIZ / ruta if ruta else None
        if estado == "retirado":
            if destino and destino.exists() and RUTA_OK.match(ruta) and not solo_revisar:
                shutil.rmtree(destino)
                print(f"– {ruta}: retirado")
            continue
        err, av = validar(t)
        for a in av:
            print(f"  ! {f.name}: {a}")
        if err:
            hubo_error = True
            print(f"✗ {f.name}: no se publica")
            for e in err:
                print(f"    · {e}")
            continue
        if estado != "listo":
            print(f"· {ruta}: en borrador, sin cambios")
            continue
        if solo_revisar:
            print(f"✓ {ruta}: listo para publicar")
            continue
        destino.mkdir(exist_ok=True)
        cambios = 0
        for nombre, cont in construir(t, marca, plantilla, logo).items():
            cambios += escribir_si_cambia(destino / nombre, cont)
        for n in (180, 192, 512):
            cambios += escribir_si_cambia(destino / f"icon-{n}.png", (RAIZ / "marca" / f"icon-{n}.png").read_bytes())
        print(f"✓ {ruta}: {'actualizado' if cambios else 'sin cambios'}")
    sys.exit(1 if hubo_error else 0)


if __name__ == "__main__":
    main()
