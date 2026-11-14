#!/usr/bin/env python3
"""Arma la página web: web/index.html (con rutas relativas) y web/index.embebido.html (todo incrustado, para vista previa)."""
import base64
from pathlib import Path
R = Path(__file__).resolve().parent.parent
src = (R / "web" / "index.src.html").read_text()
assets = {"LOGO": "marca/logo-negro.png", "STAR": "marca/estrella-negro.png", "F1": "web/img/vegas-f1.jpg",
          "SPHERE": "web/img/vegas-sphere.jpg", "APP": "web/img/app.jpg"}
rel = {"LOGO": "../marca/logo-negro.png", "STAR": "../marca/estrella-negro.png", "F1": "img/vegas-f1.jpg",
       "SPHERE": "img/vegas-sphere.jpg", "APP": "img/app.jpg"}
emb, out = src, src
for k, p in assets.items():
    b = (R / p).read_bytes()
    mt = "image/png" if p.endswith(".png") else "image/jpeg"
    emb = emb.replace("{{%s}}" % k, f"data:{mt};base64," + base64.b64encode(b).decode())
    out = out.replace("{{%s}}" % k, rel[k])
head = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" '
        'content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="icon" href="../marca/icon-192.png"></head><body>\n')
(R / "web" / "index.html").write_text(head + out + "\n</body></html>\n")
(R / "web" / "index.embebido.html").write_text(emb)
print("ok", len(emb))
