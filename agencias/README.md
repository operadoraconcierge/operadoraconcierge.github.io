# Versión para agencias

Plantilla para crear la instalación de otra agencia sin tocar la de Operadora Concierge.

> **Solo para demos internas por ahora.** La app y el publicador parten de código de Nunatak.
> Antes de entregar a un cliente hay que terminar la reescritura original (ver la propuesta para agencias).

## Pasos
1. Copia `agencias/ejemplo/` como `agencias/<agencia>/` y edita `agencia.json`:
   - `nombre`, `corto`, `dominio`, `web`
   - `prefijo_codigo`: 2 a 5 letras para las ligas (ej. `ALT` → `ALT-2611-ORT-x7k2p`)
   - `concierge_nombre`, `concierge_whatsapp` (52 + 10 dígitos), `concierge_telefono`, `concierge_horario`
   - `colores`: `fondo`, `barra`, `acento`, `acento_suave`, `marca` (formato `#RRGGBB`)
   - `tipografia`: cualquier familia de Google Fonts (por defecto `Outfit`)
   - `logo`: PNG con fondo transparente, junto al `agencia.json` (vacío = logo provisional de texto)
   - `github_usuario`: la cuenta de GitHub de la agencia
2. Corre `python3 herramientas/nueva_agencia.py agencias/<agencia>/agencia.json`
   (sale en `../agencia-<prefijo>`, fuera de este repositorio).
3. Sube esa carpeta como repositorio `<cuenta>.github.io` de la agencia y activa GitHub Pages.
   La publicación automática cada hora ya viene incluida (`.github/workflows/publicar.yml`).

## Qué no se copia
- Las fotos de Patagonia (`glaciar`, `eolo`, `bosque`, `campana`) ni la estrella de Operadora Concierge.
- El panel: hoy vive dentro de Claude y no se puede entregar. La versión vendible necesita un panel
  propio con login y base de datos.
