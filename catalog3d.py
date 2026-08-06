#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  Catálogo 3D  -  Galería local de tus diseños .3mf
============================================================
Lee tus proyectos .3mf de Bambu Studio y muestra en el navegador:
  - Miniatura de cada diseño (la que ya trae el .3mf)
  - Peso en gramos (leído del laminado del propio archivo)
  - Costo estimado (peso x precio por kg, ajustable en vivo)
  - Renombrar el archivo REAL en disco desde la galería
  - Eliminar el archivo REAL en disco desde la galería
  - Muestra también los .3mf de todas las subcarpetas
  - Pestaña "Descargas": ve los .3mf que tienes en ~/Downloads y
    muévelos con un botón a tu carpeta de diseños

No requiere instalar nada: solo Python 3 (stdlib).

USO:
  1) Pon este archivo donde quieras.
  2) Ejecuta:   python3 catalogo3d.py
     (por defecto busca la carpeta ~/Desktop/own design 3d)
     Para otra carpeta:  python3 catalogo3d.py "/ruta/a/mi/carpeta"
  3) Se abre solo en el navegador. Para cerrar: Ctrl+C en la terminal.
============================================================
"""

import os
import re
import sys
import json
import base64
import shutil
import zipfile
import threading
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

# ----------------------------------------------------------
#  CONFIGURACIÓN
# ----------------------------------------------------------
PUERTO            = 8770
PRECIO_KG_DEFECTO = 179      # MXN por kg si el .3mf no trae costo
MONEDA            = "MXN"

# Carpeta por defecto (se puede pasar otra como argumento)
CARPETA_DEFECTO   = Path.home() / "Desktop" / "own design 3d"
CARPETA_DESCARGAS = Path.home() / "Downloads"


# ----------------------------------------------------------
#  LECTURA DE .3mf
# ----------------------------------------------------------
def _leer_miniatura(z):
    """Devuelve (bytes_png, nombre) de la mejor miniatura del .3mf."""
    candidatos = [n for n in z.namelist()
                  if n.lower().endswith(".png") and "metadata/" in n.lower()]
    if not candidatos:
        candidatos = [n for n in z.namelist() if n.lower().endswith(".png")]
    if not candidatos:
        return None
    # Preferir la vista de plato grande y con luz sobre las miniaturas chicas
    def rank(n):
        low = n.lower()
        score = 0
        if "plate_1.png" in low: score += 100
        if "plate_no_light" in low: score -= 40
        if "small" in low: score -= 60
        if "top_" in low or "pick_" in low: score -= 80
        # a mayor tamaño de archivo, mejor calidad
        try: score += z.getinfo(n).file_size / 5000.0
        except Exception: pass
        return score
    mejor = max(candidatos, key=rank)
    try:
        return z.read(mejor)
    except Exception:
        return None


def _leer_peso_g(z):
    """Suma los gramos de filamento del slice_info.config (todos los platos)."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("slice_info.config")), None)
    if not nombre:
        return None
    try:
        root = ET.fromstring(z.read(nombre))
    except Exception:
        return None
    total = 0.0
    encontrado = False
    # Los gramos vienen como atributo used_g en cada <filament>
    for el in root.iter():
        val = el.attrib.get("used_g")
        if val:
            try:
                total += float(val)
                encontrado = True
            except ValueError:
                pass
    return round(total, 1) if encontrado else None


def _leer_material(z):
    """Devuelve (tipo, color_hex) del primer filamento, si existe."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("slice_info.config")), None)
    if not nombre:
        return (None, None)
    try:
        root = ET.fromstring(z.read(nombre))
    except Exception:
        return (None, None)
    for el in root.iter("filament"):
        return (el.attrib.get("type"), el.attrib.get("color"))
    # fallback: cualquier elemento con atributo type
    for el in root.iter():
        if "used_g" in el.attrib:
            return (el.attrib.get("type"), el.attrib.get("color"))
    return (None, None)


def _leer_precio_kg(z):
    """Intenta leer el costo por kg de project_settings.config (JSON)."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("project_settings.config")), None)
    if not nombre:
        return None
    try:
        data = json.loads(z.read(nombre))
    except Exception:
        return None
    costo = data.get("filament_cost")
    if isinstance(costo, list) and costo:
        try:
            return float(costo[0])
        except (ValueError, TypeError):
            return None
    if isinstance(costo, (str, int, float)):
        try:
            return float(costo)
        except (ValueError, TypeError):
            return None
    return None


def leer_diseno(ruta: Path, carpeta: Path):
    """Extrae todos los datos de un archivo .3mf.
    'archivo' es la ruta relativa a 'carpeta' (incluye subcarpetas si las hay),
    y se usa como identificador para renombrar/eliminar.
    """
    rel = ruta.relative_to(carpeta)
    subcarpeta = str(rel.parent).replace(os.sep, "/")
    if subcarpeta == ".":
        subcarpeta = ""
    info = {
        "archivo": str(rel).replace(os.sep, "/"),
        "nombre": ruta.stem,
        "subcarpeta": subcarpeta,
        "peso_g": None,
        "precio_kg": None,
        "material": None,
        "color": None,
        "miniatura": None,   # data URI base64
        "error": None,
    }
    try:
        with zipfile.ZipFile(ruta) as z:
            info["peso_g"] = _leer_peso_g(z)
            info["precio_kg"] = _leer_precio_kg(z)
            mat, col = _leer_material(z)
            info["material"] = mat
            info["color"] = col
            png = _leer_miniatura(z)
            if png:
                b64 = base64.b64encode(png).decode("ascii")
                info["miniatura"] = "data:image/png;base64," + b64
    except zipfile.BadZipFile:
        info["error"] = "No es un .3mf válido (zip dañado)"
    except Exception as e:
        info["error"] = str(e)
    return info


def escanear(carpeta: Path):
    """Busca .3mf en 'carpeta' y en todas sus subcarpetas."""
    archivos = sorted(carpeta.rglob("*.3mf"),
                       key=lambda p: str(p.relative_to(carpeta)).lower())
    return [leer_diseno(a, carpeta) for a in archivos]


# ----------------------------------------------------------
#  RUTAS SEGURAS (anti path-traversal)
# ----------------------------------------------------------
def _resolver_relativo(carpeta: Path, rel: str):
    """Valida que 'rel' sea una ruta relativa que quede dentro de 'carpeta'.
    Devuelve el Path resuelto, o None si es inválida / intenta salir de la carpeta."""
    if not rel:
        return None
    rel = rel.strip().lstrip("/\\")
    if not rel:
        return None
    carpeta_res = carpeta.resolve()
    destino = (carpeta_res / rel).resolve()
    if destino != carpeta_res and carpeta_res not in destino.parents:
        return None
    return destino


# ----------------------------------------------------------
#  RENOMBRADO SEGURO EN DISCO
# ----------------------------------------------------------
def renombrar(carpeta: Path, viejo: str, nuevo: str):
    """Renombra viejo -> nuevo, conservando la subcarpeta del original.
    'viejo' es la ruta relativa a 'carpeta' (puede incluir subcarpetas).
    Devuelve (ok, mensaje, ruta_relativa_final)."""
    nuevo = nuevo.strip()
    if not nuevo:
        return (False, "El nombre está vacío", None)
    # el nuevo nombre es solo el nombre de archivo, sin ruta
    nuevo = os.path.basename(nuevo)
    # caracteres problemáticos
    if re.search(r'[\\/:*?"<>|]', nuevo):
        return (False, "El nombre tiene caracteres no permitidos", None)
    # asegurar extensión .3mf
    if not nuevo.lower().endswith(".3mf"):
        nuevo += ".3mf"

    origen = _resolver_relativo(carpeta, viejo)
    if origen is None:
        return (False, "Origen fuera de la carpeta", None)
    if not origen.exists():
        return (False, "El archivo original ya no existe", None)

    destino = origen.parent / nuevo
    if destino.exists() and destino != origen:
        return (False, f"Ya existe un archivo llamado «{nuevo}»", None)

    try:
        origen.rename(destino)
        rel_final = str(destino.relative_to(carpeta.resolve())).replace(os.sep, "/")
        return (True, "Renombrado", rel_final)
    except Exception as e:
        return (False, str(e), None)


# ----------------------------------------------------------
#  ELIMINAR ARCHIVO
# ----------------------------------------------------------
def eliminar(carpeta: Path, archivo: str):
    """Elimina un .3mf dentro de 'carpeta' (o subcarpeta). Devuelve (ok, mensaje)."""
    ruta = _resolver_relativo(carpeta, archivo)
    if ruta is None:
        return (False, "Ruta fuera de la carpeta")
    if ruta.suffix.lower() != ".3mf":
        return (False, "Solo se pueden eliminar archivos .3mf")
    if not ruta.exists():
        return (False, "El archivo ya no existe")
    try:
        ruta.unlink()
        return (True, "Eliminado")
    except Exception as e:
        return (False, str(e))


# ----------------------------------------------------------
#  MOVER DESDE DESCARGAS
# ----------------------------------------------------------
def mover_desde_descargas(carpeta_descargas: Path, carpeta_destino: Path, archivo: str):
    """Mueve un .3mf de 'carpeta_descargas' a la raíz de 'carpeta_destino'.
    Si ya existe un archivo con ese nombre, agrega ' (2)', ' (3)'... para no pisarlo.
    Devuelve (ok, mensaje, nombre_final)."""
    origen = _resolver_relativo(carpeta_descargas, archivo)
    if origen is None:
        return (False, "Ruta de origen inválida", None)
    if origen.suffix.lower() != ".3mf":
        return (False, "Solo se pueden mover archivos .3mf", None)
    if not origen.exists():
        return (False, "El archivo ya no existe en Descargas", None)

    carpeta_destino_res = carpeta_destino.resolve()
    carpeta_destino_res.mkdir(parents=True, exist_ok=True)
    destino = carpeta_destino_res / origen.name
    if destino.exists():
        base, ext = origen.stem, origen.suffix
        n = 2
        while destino.exists():
            destino = carpeta_destino_res / f"{base} ({n}){ext}"
            n += 1

    try:
        shutil.move(str(origen), str(destino))
        return (True, "Movido", destino.name)
    except Exception as e:
        return (False, str(e), None)


# ----------------------------------------------------------
#  PÁGINA HTML (galería)
# ----------------------------------------------------------
def pagina_html(carpeta: Path):
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catálogo 3D</title>
<style>
  :root{
    --bg:#f4f2ee; --card:#fffdfa; --ink:#2b2a27; --muted:#8a857c;
    --line:#e6e2da; --accent:#c56b47; --ok:#3f7d5a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
  header{position:sticky;top:0;z-index:5;background:rgba(244,242,238,.92);
         backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
         padding:16px 24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
  h1{font-size:18px;margin:0;font-weight:600;letter-spacing:.2px}
  .sub{color:var(--muted);font-size:13px}
  .tabs{display:flex;gap:6px}
  .tab{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 14px;
       font-size:13px;cursor:pointer;color:var(--muted)}
  .tab.activo{background:var(--ink);color:#fff;border-color:var(--ink)}
  .controls{margin-left:auto;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
  .field{display:flex;flex-direction:column;gap:2px}
  .field label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .field input{border:1px solid var(--line);border-radius:8px;padding:6px 10px;
               font-size:14px;background:var(--card);width:110px}
  .stat{font-size:13px;color:var(--muted)}
  .stat b{color:var(--ink);font-weight:600}
  main{padding:24px;max-width:1400px;margin:0 auto}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;
        overflow:hidden;display:flex;flex-direction:column;
        transition:transform .12s ease,box-shadow .12s ease}
  .card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.06)}
  .thumb{aspect-ratio:1/1;background:#efeae2 center/cover no-repeat;
         display:flex;align-items:center;justify-content:center}
  .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .thumb .noimg{color:var(--muted);font-size:13px}
  .body{padding:14px;display:flex;flex-direction:column;gap:10px}
  .nombre{display:flex;gap:6px}
  .nombre input{flex:1;min-width:0;border:1px solid transparent;border-radius:8px;padding:6px 8px;
                font-size:15px;font-weight:600;background:transparent;color:var(--ink)}
  .nombre input:hover{border-color:var(--line)}
  .nombre input:focus{border-color:var(--accent);background:#fff;outline:none}
  .btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:6px 10px;
       font-size:13px;cursor:pointer;color:var(--ink);white-space:nowrap;flex-shrink:0}
  .btn:hover{border-color:var(--accent);color:var(--accent)}
  .btn.save{border-color:var(--ok);color:var(--ok);padding:6px 9px;opacity:0;pointer-events:none;transition:opacity .15s}
  .btn.save.show{opacity:1;pointer-events:auto}
  .btn.del{border-color:var(--line);color:#a53b3b;padding:6px 9px}
  .btn.del:hover{border-color:#a53b3b;background:#fbeaea}
  .btn.mover{border-color:var(--accent);color:var(--accent);width:100%;text-align:center;font-weight:600}
  .btn.mover:hover{background:var(--accent);color:#fff}
  .nombre.solo span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                     padding:6px 8px;font-size:15px;font-weight:600}
  .meta{display:flex;gap:8px;flex-wrap:wrap}
  .chip{font-size:12px;background:#efeae2;color:#5b564d;padding:3px 9px;border-radius:999px}
  .chip.peso{background:#e7efe9;color:#356b4c}
  .chip.costo{background:#f5e7df;color:#a85a38;font-weight:600}
  .chip.mat{background:#eae6f0;color:#5b4c78}
  .chip.warn{background:#fbeaea;color:#a53b3b}
  .chip.folder{background:#eef1f5;color:#4a5b73}
  .toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(40px);
         background:var(--ink);color:#fff;padding:10px 18px;border-radius:10px;font-size:14px;
         opacity:0;transition:.25s;pointer-events:none}
  .toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
  .empty{text-align:center;color:var(--muted);padding:80px 20px}
</style>
</head>
<body>
<header>
  <div>
    <h1>Catálogo 3D</h1>
    <div class="sub" id="carpeta"></div>
  </div>
  <div class="tabs">
    <button class="tab activo" id="tab-mios" onclick="cambiarVista('mios')">Mis diseños</button>
    <button class="tab" id="tab-descargas" onclick="cambiarVista('descargas')">Descargas</button>
  </div>
  <div class="controls">
    <div class="stat">Piezas: <b id="total">0</b></div>
    <div class="stat">Peso total: <b id="pesoTotal">0 g</b></div>
    <div class="stat">Costo total: <b id="costoTotal">0</b></div>
    <div class="field">
      <label>Precio filamento / kg</label>
      <input id="precio" type="number" min="0" step="10" value="350">
    </div>
    <button class="btn" onclick="cargar()">↻ Recargar</button>
  </div>
</header>
<main>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">
    No se encontraron archivos .3mf.
  </div>
</main>
<div class="toast" id="toast"></div>

<script>
const MONEDA = "__MONEDA__";
let disenosMios = [];
let disenosDescargas = [];
let descargasCargadas = false;
let vista = 'mios';

function activos(){ return vista==='mios' ? disenosMios : disenosDescargas; }

function fmtCosto(n){
  return new Intl.NumberFormat('es-MX',{style:'currency',currency:MONEDA,
    maximumFractionDigits:2}).format(n);
}
function precioKg(){ return parseFloat(document.getElementById('precio').value)||0; }

function render(){
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const disenos = activos();
  grid.innerHTML = '';
  if(!disenos.length){ empty.style.display='block'; }
  else empty.style.display='none';

  let pesoTot = 0, costoTot = 0;
  const precio = precioKg();

  disenos.forEach((d, i) => {
    const peso = d.peso_g;
    const costo = (peso!=null) ? (peso/1000*precio) : null;
    if(peso!=null) pesoTot += peso;
    if(costo!=null) costoTot += costo;

    const card = document.createElement('div');
    card.className = 'card';

    const thumb = d.miniatura
      ? `<div class="thumb"><img src="${d.miniatura}" alt=""></div>`
      : `<div class="thumb"><span class="noimg">sin miniatura</span></div>`;

    const chips = [];
    if(d.subcarpeta) chips.push(`<span class="chip folder">📁 ${d.subcarpeta.replace(/</g,'&lt;')}</span>`);
    if(peso!=null) chips.push(`<span class="chip peso">${peso.toFixed(1)} g</span>`);
    else chips.push(`<span class="chip warn">sin laminar</span>`);
    if(costo!=null) chips.push(`<span class="chip costo">${fmtCosto(costo)}</span>`);
    if(d.material) chips.push(`<span class="chip mat">${d.material}</span>`);

    const nombreEscapado = d.nombre.replace(/"/g,'&quot;');

    const filaNombre = vista==='mios'
      ? `<div class="nombre">
          <input value="${nombreEscapado}"
                 data-archivo="${d.archivo.replace(/"/g,'&quot;')}"
                 data-idx="${i}"
                 oninput="marcar(${i})"
                 onkeydown="if(event.key==='Enter'){guardar(${i})}">
          <button class="btn save" id="save-${i}" onclick="guardar(${i})" title="Guardar nombre">💾</button>
          <button class="btn del" onclick="eliminar(${i})" title="Eliminar archivo">🗑</button>
        </div>`
      : `<div class="nombre solo"><span title="${nombreEscapado}">${nombreEscapado}</span></div>`;

    const botonMover = vista==='descargas'
      ? `<button class="btn mover" onclick="mover(${i})">→ Mover a mi carpeta</button>`
      : '';

    card.innerHTML = thumb + `
      <div class="body">
        ${filaNombre}
        <div class="meta">${chips.join('')}</div>
        ${botonMover}
      </div>`;
    grid.appendChild(card);
  });

  document.getElementById('total').textContent = disenos.length;
  document.getElementById('pesoTotal').textContent = pesoTot.toFixed(0)+' g';
  document.getElementById('costoTotal').textContent = fmtCosto(costoTot);
}

function marcar(i){
  document.getElementById('save-'+i).classList.add('show');
}

async function guardar(i){
  const input = document.querySelector(`input[data-idx="${i}"]`);
  const viejo = input.dataset.archivo;
  const nuevo = input.value.trim();
  if(!nuevo){ toast('El nombre está vacío'); return; }
  try{
    const r = await fetch('/api/rename', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({viejo, nuevo})
    });
    const res = await r.json();
    if(res.ok){
      disenosMios[i].archivo = res.nombre_final;
      const base = res.nombre_final.split('/').pop();
      disenosMios[i].nombre = base.replace(/\\.3mf$/i,'');
      input.dataset.archivo = res.nombre_final;
      document.getElementById('save-'+i).classList.remove('show');
      toast('✓ Renombrado en disco');
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function eliminar(i){
  const d = disenosMios[i];
  if(!confirm(`¿Eliminar «${d.nombre}» del disco? Esta acción no se puede deshacer.`)) return;
  try{
    const r = await fetch('/api/delete', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo})
    });
    const res = await r.json();
    if(res.ok){
      disenosMios.splice(i, 1);
      render();
      toast('✓ Eliminado del disco');
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function mover(i){
  const d = disenosDescargas[i];
  try{
    const r = await fetch('/api/mover', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo})
    });
    const res = await r.json();
    if(res.ok){
      disenosDescargas.splice(i, 1);
      render();
      toast(`✓ Movido a Mis diseños (${res.nombre_final})`);
      cargarMios();
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

let toastT;
function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(()=>t.classList.remove('show'), 2200);
}

let carpetaMiosTexto = '';
let carpetaDescargasTexto = '';

async function cargarMios(){
  const r = await fetch('/api/designs');
  const data = await r.json();
  disenosMios = data.disenos;
  carpetaMiosTexto = data.carpeta;
  if(data.precio_sugerido){
    document.getElementById('precio').value = data.precio_sugerido;
  }
  if(vista==='mios'){
    document.getElementById('carpeta').textContent = carpetaMiosTexto;
    render();
  }
}

async function cargarDescargas(){
  const r = await fetch('/api/downloads');
  const data = await r.json();
  disenosDescargas = data.disenos;
  descargasCargadas = true;
  carpetaDescargasTexto = data.carpeta;
  if(vista==='descargas'){
    document.getElementById('carpeta').textContent = carpetaDescargasTexto;
    render();
  }
}

function cambiarVista(v){
  vista = v;
  document.getElementById('tab-mios').classList.toggle('activo', v==='mios');
  document.getElementById('tab-descargas').classList.toggle('activo', v==='descargas');
  document.getElementById('carpeta').textContent = v==='mios' ? carpetaMiosTexto : carpetaDescargasTexto;
  if(v==='descargas' && !descargasCargadas){
    cargarDescargas();
  } else {
    render();
  }
}

async function cargar(){
  if(vista==='mios'){
    await cargarMios();
  } else {
    await cargarDescargas();
  }
}

document.getElementById('precio').addEventListener('input', render);
cargarMios();
</script>
</body>
</html>""".replace("__MONEDA__", MONEDA)


# ----------------------------------------------------------
#  SERVIDOR
# ----------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    carpeta = None            # se asigna al arrancar
    carpeta_descargas = None  # ídem

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            body = pagina_html(self.carpeta).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/designs":
            disenos = escanear(self.carpeta)
            precios = [d["precio_kg"] for d in disenos if d["precio_kg"]]
            sugerido = round(precios[0]) if precios else PRECIO_KG_DEFECTO
            self._json({
                "carpeta": str(self.carpeta),
                "precio_sugerido": sugerido,
                "disenos": disenos,
            })
        elif self.path == "/api/downloads":
            disenos = escanear(self.carpeta_descargas) if self.carpeta_descargas.exists() else []
            self._json({
                "carpeta": str(self.carpeta_descargas),
                "disenos": disenos,
            })
        else:
            self._json({"error": "no encontrado"}, 404)

    def do_POST(self):
        if self.path not in ("/api/rename", "/api/delete", "/api/mover"):
            self._json({"ok": False, "mensaje": "ruta desconocida"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n))
        except Exception:
            self._json({"ok": False, "mensaje": "petición inválida"}, 400)
            return

        if self.path == "/api/rename":
            ok, msg, final = renombrar(self.carpeta,
                                       data.get("viejo", ""), data.get("nuevo", ""))
            self._json({"ok": ok, "mensaje": msg, "nombre_final": final})
        elif self.path == "/api/delete":
            ok, msg = eliminar(self.carpeta, data.get("archivo", ""))
            self._json({"ok": ok, "mensaje": msg})
        else:  # /api/mover
            ok, msg, final = mover_desde_descargas(self.carpeta_descargas, self.carpeta,
                                                    data.get("archivo", ""))
            self._json({"ok": ok, "mensaje": msg, "nombre_final": final})

    def log_message(self, *a):
        pass  # silenciar el log de cada request


def main():
    carpeta = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else CARPETA_DEFECTO
    if not carpeta.exists():
        print(f"⚠  No existe la carpeta:\n   {carpeta}\n")
        print("   Pásala como argumento:")
        print('   python3 catalogo3d.py "/ruta/a/tu/carpeta"')
        sys.exit(1)

    Handler.carpeta = carpeta
    Handler.carpeta_descargas = CARPETA_DESCARGAS
    n = len(list(carpeta.glob("*.3mf")))
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    url = f"http://127.0.0.1:{PUERTO}/"

    print("=" * 52)
    print("  Catálogo 3D en marcha")
    print("=" * 52)
    print(f"  Carpeta : {carpeta}")
    print(f"  Archivos: {n} .3mf")
    print(f"  Abre    : {url}")
    print("  (Ctrl+C para detener)")
    print("=" * 52)

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Detenido. ¡Hasta luego!")
        servidor.shutdown()


if __name__ == "__main__":
    main()