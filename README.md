# Concierge Operadora · app concierge para viajeros

Copia independiente de la app de concierge (PWA) con la marca de Concierge Operadora.
No comparte nada con la app de Nunatak: repositorio, cuenta de GitHub y panel propios.

## Qué hay aquí
| Carpeta | Para qué |
|---|---|
| `plantilla/app.html`, `plantilla/sw.js` | La app del viajero (itinerario, reservas, equipo, opcionales, más, modo demo). |
| `marca/` | Logo, íconos y `marca.json` (nombre, web y datos del concierge). |
| `fotos/` | Fotos de la biblioteca (`glaciar`, `eolo`, `bosque`, `campana`). |
| `viajes/*.json` | Un archivo por viaje. |
| `OPC-AAMM-XXX-abcde/` | Viaje publicado: esa carpeta es la liga del viajero. |
| `panel/panel-artifact.html` | Código del panel de carga (vive como Artifact de Claude, con su propia base de datos). |
| `herramientas/publicar.py` | Valida y publica los viajes en estado `listo`. |

## Flujo
1. Mariel carga el viaje en el panel (iPad) y toca **Listo para publicar**.
2. La revisión automática (cada hora, 7:00 a 23:00 hora de México) lee los viajes listos del panel,
   les asigna liga si no tienen (`OPC-AAMM-XXX` + 5 letras al azar), guarda `viajes/<liga>.json`,
   corre `python3 herramientas/publicar.py`, sube los cambios y marca el viaje como `publicado` con su liga.
3. La liga se comparte en el grupo de WhatsApp. Cambios posteriores se publican en la misma liga.

## Pendientes
- Número real de WhatsApp del concierge en `marca/marca.json` y en el panel.
- Cuenta de GitHub de la empresa y repositorio (privado con GitHub Pro).
