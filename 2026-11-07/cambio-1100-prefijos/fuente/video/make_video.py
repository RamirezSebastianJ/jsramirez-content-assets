#!/usr/bin/env python3
"""Video 9:16 'Un cambio, 1.100 prefijos' (post-mortem Cloudflare 2026-02-20, arquitectura). Uso: python3 make_video.py <salida_dir> [--test]
Genera: video-preview.mp4 (sin voz, SFX sutiles), portada.png 1080x1920, guion-voz.txt, frames de prueba si --test."""
import sys, json, pathlib, subprocess, wave
import numpy as np
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
TEST = "--test" in sys.argv
FPS = 30
# cada oración del guion de voz = una escena
SCENES = [
 dict(dur=3.4, voz="Un solo cambio retiró 1.100 prefijos de red.", sfx=[(1.0,"blip"),(1.9,"thud")]),
 dict(dur=3.2, voz="Fue en Cloudflare, el 20 de febrero de 2026.", sfx=[(1.2,"blip")]),
 dict(dur=3.6, voz="Un cambio en su pipeline de BYOIP.", sfx=[(1.0,"blip"),(1.8,"blip"),(2.4,"thud")]),
 dict(dur=3.6, voz="Para los clientes afectados, fueron cerca de seis horas.", sfx=[(1.0,"blip"),(2.6,"thud")]),
 dict(dur=3.4, voz="¿A cuántos puede llegar tu próximo cambio?", sfx=[(1.4,"blip")]),
 dict(dur=3.8, voz="Primero a un grupo pequeño. Miras. Y luego a más.", sfx=[(0.9,"blip"),(1.7,"blip"),(2.5,"blip")]),
 dict(dur=3.6, voz="Cloudflare lo llamó Fail Small y dijo que completó el plan en mayo de 2026.", sfx=[(1.2,"blip"),(2.4,"thud")]),
 dict(dur=3.8, voz="Mi lección: todo cambio masivo necesita un freno antes de llegar a todos.", sfx=[(1.2,"blip"),(2.8,"thud")], cierre=True),
 dict(dur=3.0, voz="Comenta SISTEMA y te envío mi guía.", sfx=[(0.3,"blip")], cierre=True),
]
TOTAL = sum(s["dur"] for s in SCENES)

# guion de voz
(OUT/"guion-voz.txt").write_text("\n".join(f"{i+1}. {s['voz']}"+("   [CIERRE]" if s.get("cierre") else "") for i,s in enumerate(SCENES))+"\n", encoding="utf-8")
(OUT/"scenes.json").write_text(json.dumps(SCENES, ensure_ascii=False, indent=1), encoding="utf-8"); (HERE/"scenes.json").write_text(json.dumps(SCENES, ensure_ascii=False, indent=1), encoding="utf-8")

# HTML con escenas inyectadas (queda junto a las fuentes relativas)
html = (HERE/"scene_template.html").read_text(encoding="utf-8").replace("/*SCENES*/", json.dumps([{"dur":s["dur"]} for s in SCENES]))
page_html = HERE/"scene.html"; page_html.write_text(html, encoding="utf-8")

# --- SFX sutiles (sin música) ---
SR = 44100
def env(n, a=0.003, k=40): 
    t = np.arange(n)/SR; return np.minimum(1, t/a)*np.exp(-k*t)
def tone(f, dur, k, amp):
    n=int(SR*dur); t=np.arange(n)/SR; return amp*np.sin(2*np.pi*f*t)*env(n,0.002,k)
def sfx(kind):
    if kind=="tick":  return tone(2000,0.04,90,0.10)
    if kind=="blip":  return tone(880,0.09,45,0.14)+tone(1320,0.09,60,0.05)
    if kind=="thud":
        n=int(SR*0.22); t=np.arange(n)/SR; rng=np.random.default_rng(1)
        return 0.34*np.sin(2*np.pi*(95-40*t/0.22)*t)*env(n,0.002,16)+0.03*rng.standard_normal(n)*env(n,0.001,60)
    if kind=="whoosh":
        n=int(SR*0.22); rng=np.random.default_rng(2); x=rng.standard_normal(n)
        y=np.cumsum(x)*0.0; a=0.0; o=np.zeros(n)
        for i in range(n): a=a*0.88+x[i]*0.12; o[i]=a
        w=np.sin(np.linspace(0,np.pi,n))**2
        return 0.30*o*w
buf = np.zeros(int(SR*(TOTAL+0.5)))
def put(t, x):
    i=int(t*SR); buf[i:i+len(x)] += x[:max(0,len(buf)-i)]
acc=0.0
for s in SCENES:
    put(acc,sfx("tick")); put(acc+s["dur"]-0.24,sfx("whoosh"))
    for (rt,k) in s["sfx"]: put(acc+rt,sfx(k))
    acc+=s["dur"]
buf = np.clip(buf,-0.95,0.95)
with wave.open(str(OUT/"sfx.wav"),"wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf*32767).astype(np.int16).tobytes())

# --- portada 1080x1920 ---
cover = f"""<!doctype html><html><head><meta charset=utf-8><style>
@font-face{{font-family:'Space Grotesk';font-weight:500;src:url('../fonts/space-grotesk-latin-500-normal.woff2')}}
@font-face{{font-family:'Space Grotesk';font-weight:700;src:url('../fonts/space-grotesk-latin-700-normal.woff2')}}
@font-face{{font-family:'DM Sans';font-weight:400;src:url('../fonts/dm-sans-latin-400-normal.woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:#F5F5F5;color:#0B0B0B;position:relative;font-family:'DM Sans'}}
.f{{position:absolute;left:60px;right:60px;top:250px;bottom:420px;border:1px solid #0B0B0B}}
.tag{{position:absolute;left:100px;top:660px;border:1px solid #0B0B0B;padding:8px 16px;font:500 28px 'Space Grotesk';letter-spacing:.08em}}
h1{{position:absolute;left:100px;right:100px;top:760px;font:700 140px/1.0 'Space Grotesk';letter-spacing:-.03em}}
.r{{position:absolute;left:100px;width:700px;top:1090px;height:1px;background:#0B0B0B}}
p{{position:absolute;left:100px;right:200px;top:1125px;font:400 40px/1.35 'DM Sans';color:#444}}
.wm{{position:absolute;left:100px;top:1360px;display:flex;gap:10px;align-items:center;font:500 26px 'Space Grotesk'}}
</style></head><body><div class=f></div><div class=tag>[POST-MORTEM]</div>
<h1>1.100<br>PREFIJOS</h1><div class=r></div><p>Un cambio, una caída y lo que cambió Cloudflare.</p>
<div class=wm><svg width=26 height=26 viewBox="0 0 24 24"><path d="M12 1 L14.6 9.4 L23 12 L14.6 14.6 L12 23 L9.4 14.6 L1 12 L9.4 9.4 Z"/></svg>JSRamirez · @jsramirezdev</div></body></html>"""
(HERE/"cover.html").write_text(cover, encoding="utf-8")

with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width":1080,"height":1920})
    pg.goto((HERE/"cover.html").as_uri()); pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT/"portada.png"))
    pg.goto(page_html.as_uri()); pg.wait_for_timeout(500)
    fr = OUT/"frames"; fr.mkdir(exist_ok=True)
    if TEST:
        acc=0; ts=[]
        for s in SCENES: ts += [acc+s["dur"]*0.55]; acc+=s["dur"]
        ts += [1.0, 1.55]
        for k,t in enumerate(sorted(ts)):
            pg.evaluate(f"render({t})"); pg.screenshot(path=str(OUT/f"test_{k:02d}.png"))
    else:
        n=int(TOTAL*FPS)
        for k in range(n):
            pg.evaluate(f"render({k/FPS})"); pg.screenshot(path=str(fr/f"{k:04d}.jpg"), type="jpeg", quality=92)
    br.close()

if not TEST:
    subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(OUT/"frames/%04d.jpg"),"-i",str(OUT/"sfx.wav"),
        "-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",
        str(OUT/"video-preview.mp4")],check=True)
    print("OK", TOTAL)
