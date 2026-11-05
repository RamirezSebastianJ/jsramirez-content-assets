import asyncio, json, os, sys
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.dirname(HERE)
STAR='<svg width="22" height="22" viewBox="0 0 24 24"><path d="M12 0 L14.6 9.4 L24 12 L14.6 14.6 L12 24 L9.4 14.6 L0 12 L9.4 9.4Z" fill="currentColor"/></svg>'
S=[
 dict(tag="[ARCHITECTURE]",h="Cloudflare recortó <b>85%</b> la memoria de su DNS… construyendo menos.",sub="Cada cambio reconstruía la zona entera. Ya no.",kind="cover"),
 dict(tag="[PROBLEMA]",h="Un cambio pequeño, un build gigante.",body=["Cada cambio de DNS podía disparar una reconstrucción de la zona completa.","Hay zonas con <b>más de 20 millones</b> de registros.","Una full build lee, codifica y compara todo, y mantiene la zona en memoria."]),
 dict(tag="[LA DECISIÓN]",h="Construir lo mínimo que se pueda demostrar seguro.",body=["Un planificador elige entre 5 tipos de build:","resources only · resources + metadata · apex + metadata · purge · full zone.","Los eventos ahora dicen qué campo cambió."]),
 dict(tag="[LA REGLA]",h="Byte a byte idéntico, o build completa.",body=["Cada clave que escribe un build dirigido debe ser idéntica a la de una full build.","Si no pueden probarlo, hacen la full build.","Ante la duda, prefieren repetir trabajo a perder un cambio."]),
 dict(tag="[RESULTADOS]",h="Lo que midieron.",stats=[("92.95%","de los builds evitó reconstruir la zona completa"),("49 → 7 GiB","memoria promedio del working set"),("14.6 → 1.21 min","pico de retraso p99"),("7.7 → 3.3 s","mediana de espera del build")]),
 dict(tag="[MI LECCIÓN]",h="No recalcules todo si solo cambió una cosa.",body=["Pero solo si puedes demostrar que el atajo da el mismo resultado.","El trade-off: más lógica de planificación a cambio de menos cómputo y menos espera.","Diseñar es decidir cuándo NO hacer el trabajo completo."]),
 dict(tag="[SISTEMA]",h="¿Quieres la guía de mi metodología?",body=["Comenta <b>SISTEMA</b> y te la envío.","Sígueme y comparte con un dev que diseña sistemas."],kind="cta"),
]
def html(i,s,fmt):
    W,H=1080,(1350 if fmt=='ig' else 1920)
    pad=(70,70,70,70) if fmt=='ig' else (250,190,420,70)  # top,right,bottom,left
    t,r,b,l=pad
    kind=s.get('kind','')
    if kind=='cover': hs=88
    else: hs=66
    body=''
    if 'body' in s: body='<ul>'+''.join(f'<li>{x}</li>' for x in s['body'])+'</ul>'
    if 'stats' in s: body='<div class="stats">'+''.join(f'<div class="st"><div class="n">{a}</div><div class="d">{c}</div></div>' for a,c in s['stats'])+'</div>'
    sub=f'<p class="sub">{s["sub"]}</p>' if 'sub' in s else ''
    return f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:SG;font-weight:700;src:url(fonts/space-grotesk-latin-700-normal.woff2)}}
@font-face{{font-family:SG;font-weight:500;src:url(fonts/space-grotesk-latin-500-normal.woff2)}}
@font-face{{font-family:DM;font-weight:400;src:url(fonts/dm-sans-latin-400-normal.woff2)}}
@font-face{{font-family:DM;font-weight:500;src:url(fonts/dm-sans-latin-500-normal.woff2)}}
*{{margin:0;box-sizing:border-box}}body{{width:{W}px;height:{H}px;background:#0B0B0B;color:#F5F5F5;font-family:DM;position:relative;overflow:hidden}}
.box{{position:absolute;left:{l}px;top:{t}px;right:{r}px;bottom:{b}px;border:1px solid #8A8A8A;padding:50px;display:flex;flex-direction:column;justify-content:center;gap:34px}}
.tag{{font-family:SG;font-weight:500;font-size:28px;letter-spacing:3px;color:#8A8A8A}}
h1{{font-family:SG;font-weight:700;font-size:{hs}px;line-height:1.08;letter-spacing:-1px}}b{{font-weight:700;{'background:#F5F5F5;color:#0B0B0B;padding:0 10px;' if kind=='cover' else ''}}}
.sub{{font-size:36px;color:#8A8A8A;line-height:1.3}}
ul{{list-style:none;display:flex;flex-direction:column;gap:26px}}li{{font-size:35px;line-height:1.32;padding-left:28px;border-left:1px solid #F5F5F5}}
.stats{{display:flex;flex-direction:column;gap:22px}}.st{{border-top:1px solid #8A8A8A;padding-top:14px}}.n{{font-family:SG;font-weight:700;font-size:62px}}.d{{font-size:28px;color:#8A8A8A}}
.wm{{position:absolute;left:{l}px;bottom:{b-52 if fmt=='tt' else 22}px;font-family:SG;font-weight:500;font-size:22px;color:#8A8A8A;display:flex;gap:10px;align-items:center}}
.pg{{position:absolute;right:{r}px;top:{t-46 if fmt=='tt' else 22}px;font-size:22px;color:#8A8A8A;font-family:SG}}
</style><body><div class=box><div class=tag>{s['tag']}</div><h1>{s['h']}</h1>{sub}{body}</div>
<div class=wm>{STAR}<span>JSRamirez · @jsramirezdev</span></div><div class=pg>{i+1}/7</div></body>'''
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch()
        for fmt,H in(('ig',1350),('tt',1920)):
            pg=await br.new_page(viewport={'width':1080,'height':H})
            for i,s in enumerate(S):
                fp=os.path.join(HERE,f'_s_{fmt}_{i}.html'); open(fp,'w').write(html(i,s,fmt))
                await pg.goto('file://'+fp); await pg.wait_for_timeout(300)
                await pg.screenshot(path=os.path.join(OUT,fmt,f'slide-{i+1:02d}.png')); os.remove(fp)
        await br.close()
asyncio.run(main())
