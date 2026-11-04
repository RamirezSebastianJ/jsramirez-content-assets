#!/usr/bin/env python3
"""Genera el carrusel 'GitHub reescribe el almacenamiento de Git' en 4:5 (IG) y 9:16 (TikTok).
Uso: python3 build_carrusel.py <salida_dir>   (fuentes en ../fonts relativo a este archivo)"""
import sys, pathlib, html
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]).resolve()
FONTS = HERE if any(HERE.glob('*.woff2')) else (HERE.parent / 'fonts')

STAR = '<svg class="star" viewBox="0 0 24 24" width="26" height="26"><path d="M12 1 L14.6 9.4 L23 12 L14.6 14.6 L12 23 L9.4 14.6 L1 12 L9.4 9.4 Z" fill="currentColor"/></svg>'

# ---------- contenido ----------
SLIDES = [
    dict(kind="cover", tag="[ARCHITECTURE]",
         title="GitHub reescribe cómo guarda tu código",
         sub="7.400 millones de commits al mes lo obligaron a cambiar la arquitectura."),
    dict(kind="text", tag="[EL PROBLEMA]",
         title="Cada push esperaba a la réplica más lenta",
         body="Su sistema Spokes guarda cada repo en 5 réplicas y exige quórum. Una escritura no termina hasta que responde la réplica más lenta, y mientras tanto el repo entero queda bloqueado."),
    dict(kind="diagram1", tag="[EL CUELLO DE BOTELLA]",
         title="Una réplica lenta frena todo el repo",
         body="Una réplica a ~1.600 km suma unos 25 ms por ida y vuelta, y cada escritura necesita varias."),
    dict(kind="text", tag="[DECISIÓN 1]",
         title="Quórum por rama, no por repositorio",
         body="Las ramas de distintos devs (o agentes) casi nunca chocan, así que dejan de esperarse. En pruebas internas con tráfico realista: de 3 a 4 veces más escrituras por segundo."),
    dict(kind="diagram2", tag="[DECISIÓN 2]",
         title="Separar almacenamiento de cómputo",
         body="Los datos viven en un almacenamiento de objetos (Azure Blob). Las réplicas de lectura son efímeras y escalan a demanda. Solo las referencias necesitan consenso."),
    dict(kind="text", tag="[EL TRADE-OFF]",
         title="Nada es gratis",
         body="Cada escritura paga algo de latencia, porque no se confirma hasta ser durable en el almacenamiento. Y el quórum sigue marcando el techo. Por eso GitHub dice que aún no ha terminado."),
    dict(kind="cta", tag="[SISTEMA]",
         title="Mi lección: no sumes réplicas para leer más",
         body="Separa lo que lee de lo que escribe. Sígueme y comparte esto con tu equipo. Comenta SISTEMA y te envío mi guía."),
]

CSS = """
@font-face{font-family:'Space Grotesk';font-weight:500;src:url('FONTS/space-grotesk-latin-500-normal.woff2') format('woff2')}
@font-face{font-family:'Space Grotesk';font-weight:700;src:url('FONTS/space-grotesk-latin-700-normal.woff2') format('woff2')}
@font-face{font-family:'DM Sans';font-weight:400;src:url('FONTS/dm-sans-latin-400-normal.woff2') format('woff2')}
@font-face{font-family:'DM Sans';font-weight:500;src:url('FONTS/dm-sans-latin-500-normal.woff2') format('woff2')}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:W_PXpx;height:H_PXpx;background:#0B0B0B;color:#F5F5F5;font-family:'DM Sans',sans-serif;overflow:hidden}
.slide{position:relative;width:W_PXpx;height:H_PXpx;background:#0B0B0B;color:#F5F5F5}
.slide.light{background:#F5F5F5;color:#0B0B0B}
.frame{position:absolute;left:PADLpx;top:PADTpx;right:PADRpx;bottom:PADBpx;border:1px solid currentColor;padding:44px 48px;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;font-family:'Space Grotesk';font-weight:500;font-size:26px;letter-spacing:.08em;color:#8A8A8A}
.slide.light .top{color:#555}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px}
h1{font-family:'Space Grotesk';font-weight:700;line-height:1.04;letter-spacing:-.02em}
p.body{font-size:BODYpx;line-height:1.4;font-weight:400}
p.sub{font-size:SUBpx;line-height:1.35;color:#8A8A8A}
.slide.light p.sub{color:#444}
.foot{display:flex;justify-content:space-between;align-items:center;font-family:'Space Grotesk';font-weight:500;font-size:24px;letter-spacing:.04em}
.wm{display:flex;align-items:center;gap:10px}
.star{display:block}
.arrows{display:flex;gap:18px;font-size:34px}
.rule{height:1px;background:currentColor;opacity:.9}
.tagbox{display:inline-block;border:1px solid currentColor;padding:8px 16px;align-self:flex-start;font-family:'Space Grotesk';font-weight:500;font-size:26px;letter-spacing:.08em}
svg text{font-family:'Space Grotesk';font-weight:500}
"""

def layout(fmt):
    if fmt == "ig":   # 1080x1350
        return dict(W=1080, H=1350, PADL=60, PADT=60, PADR=60, PADB=60, H1=84, H1c=100, BODY=36, SUB=38, DIAG_H=420)
    # 9:16 TikTok: zonas seguras: arriba 250, abajo 420, derecha 190
    return dict(W=1080, H=1920, PADL=60, PADT=250, PADR=190, PADB=420, H1=76, H1c=92, BODY=34, SUB=36, DIAG_H=520)

def diagram1(L):
    # 5 réplicas, una lenta; barra de latencia
    w = 760
    s = f'''<svg viewBox="0 0 {w} 400" width="100%" style="max-height:{L["DIAG_H"]}px">
      <rect x="1" y="1" width="150" height="90" fill="none" stroke="currentColor" stroke-width="2"/>
      <text x="76" y="56" text-anchor="middle" font-size="26" fill="currentColor">PUSH</text>'''
    ys = [20, 95, 170, 245, 320]
    for i, y in enumerate(ys):
        slow = (i == 4)
        bw = 330 if slow else 120
        s += f'<line x1="151" y1="46" x2="270" y2="{y+25}" stroke="currentColor" stroke-width="1.5"/>'
        s += f'<rect x="270" y="{y}" width="110" height="50" fill="{"currentColor" if slow else "none"}" stroke="currentColor" stroke-width="2"/>'
        s += f'<text x="325" y="{y+33}" text-anchor="middle" font-size="22" fill="{"#0B0B0B" if slow else "currentColor"}">réplica {i+1}</text>'
        s += f'<rect x="395" y="{y+14}" width="{bw}" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="{"0" if slow else "6 4"}"/>'
        if slow:
            s += f'<rect x="395" y="{y+14}" width="{bw}" height="22" fill="currentColor"/>'
    s += '<text x="1" y="392" font-size="22" fill="currentColor">la lenta marca la latencia de todas</text></svg>'
    return s

def diagram2(L):
    s = '''<svg viewBox="0 0 760 400" width="100%" style="max-height:DIAGHpx">
      <rect x="1" y="1" width="220" height="110" fill="none" stroke="currentColor" stroke-width="2"/>
      <text x="111" y="50" text-anchor="middle" font-size="24" fill="currentColor">ESCRITURAS</text>
      <text x="111" y="84" text-anchor="middle" font-size="20" fill="#8A8A8A">consenso solo en refs</text>
      <line x1="221" y1="56" x2="320" y2="56" stroke="currentColor" stroke-width="2"/>
      <rect x="320" y="1" width="438" height="110" fill="currentColor"/>
      <text x="539" y="50" text-anchor="middle" font-size="26" fill="#0B0B0B">ALMACENAMIENTO</text>
      <text x="539" y="84" text-anchor="middle" font-size="20" fill="#0B0B0B">objetos durables (Azure Blob)</text>'''.replace("DIAGH", str(L["DIAG_H"]))
    for i in range(4):
        x = 1 + i * 190
        s += f'<line x1="539" y1="111" x2="{x+85}" y2="250" stroke="currentColor" stroke-width="1.5" stroke-dasharray="6 4"/>'
        s += f'<rect x="{x}" y="250" width="170" height="80" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="8 5"/>'
        s += f'<text x="{x+85}" y="298" text-anchor="middle" font-size="22" fill="currentColor">lectura {i+1}</text>'
    s += '<text x="1" y="385" font-size="22" fill="currentColor">réplicas de lectura efímeras: escalan a demanda</text></svg>'
    return s

def slide_html(i, s, L, total):
    first, last = (i == 0), (i == total - 1)
    light = s["kind"] in ("cover", "cta")
    cls = "slide light" if light else "slide"
    arrows = ("" if first else "<span>←</span>") + ("" if last else "<span>→</span>")
    top = f'<div class="top"><span>{html.escape(s["tag"])}</span><span>{i+1:02d} / {total:02d}</span></div>'
    wm = f'<div class="wm">{STAR}<span>JSRamirez · @jsramirezdev</span></div>'
    foot = f'<div class="foot">{wm}<div class="arrows">{arrows}</div></div>'
    h1size = L["H1c"] if s["kind"] == "cover" else L["H1"]
    t = html.escape(s["title"])
    b = html.escape(s.get("body", ""))
    if s["kind"] == "cover":
        main = f'<div class="main"><h1 style="font-size:{h1size}px">{t}</h1><div class="rule"></div><p class="sub">{html.escape(s["sub"])}</p></div>'
    elif s["kind"] == "diagram1":
        main = f'<div class="main"><h1 style="font-size:{h1size}px">{t}</h1>{diagram1(L)}<p class="body">{b}</p></div>'
    elif s["kind"] == "diagram2":
        main = f'<div class="main"><h1 style="font-size:{h1size}px">{t}</h1>{diagram2(L)}<p class="body">{b}</p></div>'
    elif s["kind"] == "cta":
        main = (f'<div class="main"><h1 style="font-size:{h1size}px">{t}</h1><p class="body">{b}</p>'
                f'<div class="tagbox" style="font-size:44px;padding:16px 28px;background:#0B0B0B;color:#F5F5F5">Comenta: SISTEMA</div></div>')
    else:
        main = f'<div class="main"><h1 style="font-size:{h1size}px">{t}</h1><p class="body">{b}</p></div>'
    css = (CSS.replace("FONTS", FONTS.as_uri().replace("file://", "file://"))
              .replace("W_PX", str(L["W"])).replace("H_PX", str(L["H"]))
              .replace("PADL", str(L["PADL"])).replace("PADT", str(L["PADT"]))
              .replace("PADR", str(L["PADR"])).replace("PADB", str(L["PADB"]))
              .replace("BODY", str(L["BODY"])).replace("SUB", str(L["SUB"])))
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="{cls}"><div class="frame">{top}{main}{foot}</div></div></body></html>'

def main():
    with sync_playwright() as p:
        br = p.chromium.launch()
        for fmt in ("ig", "tt"):
            L = layout(fmt)
            d = OUT / fmt; d.mkdir(parents=True, exist_ok=True)
            pg = br.new_page(viewport={"width": L["W"], "height": L["H"]})
            for i, s in enumerate(SLIDES):
                f = d / f"slide-{i+1:02d}.html"
                f.write_text(slide_html(i, s, L, len(SLIDES)), encoding="utf-8")
                pg.goto(f.as_uri()); pg.wait_for_timeout(250)
                pg.evaluate("document.fonts.ready")
                pg.screenshot(path=str(d / f"slide-{i+1:02d}.png"))
        br.close()

main()
