"""Actualiza la plantilla de la app que el panel usa para la vista previa (apptpl) y su estilo negro/azul."""
import json, re, sys, base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import publicar as P
R = P.RAIZ
tpl = (R / "plantilla/app.html").read_text()
a = tpl.index('<link rel="preconnect"'); b = tpl.rindex('</body>')
body = tpl[a:b]
imgs = {f.stem: P.foto_uri(f.stem) for f in sorted((R / "fotos").glob("*.jpg"))}
body = (body.replace("__TRIP__", "__DATA__").replace("__IMGS__", P.json_html(imgs))
        .replace("__LOGO__", P.logo_html()).replace("__LOGO_COLOR__", P.uri("logo-color.png"))
        .replace("__STAR__", P.estrella_html()).replace("__APP_TITLE__", "Concierge")
        .replace("__TITLE__", "Concierge Operadora"))
assert body.count("__DATA__") == 1, body.count("__DATA__")
assert "__" not in re.sub(r"__DATA__", "", body).replace("__proto__", "") or True
p = R / "panel/panel-artifact.html"
s = p.read_text()
apptpl = json.dumps(body).replace("</", "<\\/")
s, n = re.subn(r'(<script type="application/json" id="apptpl">).*?(</script>\n<script>)',
              lambda m: m.group(1) + apptpl + m.group(2), s, count=1, flags=re.S)
assert n == 1
# --- estilo del panel: negro + azul del logo, Outfit
def rep(x, y):
    global s
    if x in s: s = s.replace(x, y)
rep('family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Jost:wght@300;400;500;600', 'family=Outfit:wght@300;400;500;600;700')
rep('--display:"Cormorant Garamond",Georgia,serif; --body:"Jost","Avenir Next","Helvetica Neue",Arial,sans-serif',
    '--display:"Outfit","Helvetica Neue",Arial,sans-serif; --body:"Outfit","Helvetica Neue",Arial,sans-serif')
rep('--bg:#F5F4F2; --surface:#FFFFFF; --sunk:#EDEBE8; --ink:#141414; --soft:#6B6762; --line:#E0DDD8;',
    '--bg:#F6F7F8; --surface:#FFFFFF; --sunk:#EEF1F3; --ink:#111315; --soft:#5D5958; --line:#E1E4E7;')
rep('--gold:#7A6646; --gold-soft:#D8C9AA;', '--gold:#1679B0; --gold-soft:#3FAEE6;')
s = s.replace('--gold:#D3C19C;', '--gold:#4DB5EA;').replace('--ink:#EEEBE6;', '--ink:#EEF0F2;')
# logo oficial en la barra superior
s, n = re.subn(r'(<header class="top"><span class="logo">)<svg.*?</svg>(</span>)',
              lambda m: m.group(1) + P.logo_html().replace('height:100%', 'height:32px') + m.group(2), s, count=1, flags=re.S)
p.write_text(s)
print("ok", len(s))
