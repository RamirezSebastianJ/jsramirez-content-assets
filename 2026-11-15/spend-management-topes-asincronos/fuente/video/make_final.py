#!/usr/bin/env python3
"""Montaje final: sincroniza escenas con la voz de Sebastian. Uso: python3 make_final.py <voz.m4a> <salida_dir>"""
import sys, json, pathlib, subprocess, importlib.util
import numpy as np
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
VOZ, OUT = sys.argv[1], pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
base = json.loads((HERE/"scenes.json").read_text()) if (HERE/"scenes.json").exists() else None
# inicio del habla de cada escena: silencedetect (-38 dB, d 0.28) sobre la voz de Sebastian; la escena entra 0.2 s antes
import re
def detect(voz):
    r=subprocess.run(["ffmpeg","-i",voz,"-af","silencedetect=noise=-38dB:d=0.28","-f","null","-"],capture_output=True,text=True).stderr
    ends=[float(x) for x in re.findall(r"silence_end: ([0-9.]+)",r)]
    starts_sil=[float(x) for x in re.findall(r"silence_start: ([0-9.]+)",r)]
    dur=float(re.search(r"Duration: (\d+):(\d+):([0-9.]+)",r).expand(r"\1:\2:\3").split(":")[0])*3600 if False else None
    return ends, starts_sil
ends_sil, starts_sil = detect(VOZ)
first = ends_sil[0] if starts_sil and starts_sil[0] < 0.05 else 0.0
SPEECH_START = [first] + ends_sil[1:] if first else [0.0]+ends_sil
SC0 = json.loads((HERE/"scenes.json").read_text())
assert len(SPEECH_START) >= len(SC0), f"se detectaron {len(SPEECH_START)} tramos de habla; el guion tiene {len(SC0)} oraciones (revisa pausas de ~0.5 s)"
SPEECH_START = SPEECH_START[:len(SC0)]
END = (starts_sil[-1] if starts_sil and starts_sil[-1] > SPEECH_START[-1] else SPEECH_START[-1]+3.0) + 0.5   # fin de voz + cola
starts = [0.0] + [t-0.2 for t in SPEECH_START[1:]]
ends = starts[1:] + [END]
SC = json.loads((HERE/"scenes.json").read_text())
for i,s in enumerate(SC): s["base"]=s["dur"]; s["dur"]=round(ends[i]-starts[i],3)
TOTAL = END
html = (HERE/"scene_template.html").read_text().replace("/*SCENES*/", json.dumps([{"dur":s["dur"],"base":s["base"]} for s in SC]))
page = HERE/"scene_final.html"; page.write_text(html, encoding="utf-8")
# SFX sobre la nueva línea de tiempo
SR=44100
def env(n,a=0.003,k=40): t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-k*t)
def tone(f,d,k,a): n=int(SR*d); t=np.arange(n)/SR; return a*np.sin(2*np.pi*f*t)*env(n,0.002,k)
def sfx(kind):
    if kind=="tick": return tone(2000,0.04,90,0.10)
    if kind=="blip": return tone(880,0.09,45,0.14)+tone(1320,0.09,60,0.05)
    if kind=="thud":
        n=int(SR*0.22); t=np.arange(n)/SR; r=np.random.default_rng(1)
        return 0.34*np.sin(2*np.pi*(95-40*t/0.22)*t)*env(n,0.002,16)+0.03*r.standard_normal(n)*env(n,0.001,60)
    if kind=="whoosh":
        n=int(SR*0.22); x=np.random.default_rng(2).standard_normal(n); a=0.0; o=np.zeros(n)
        for i in range(n): a=a*0.88+x[i]*0.12; o[i]=a
        return 0.30*o*np.sin(np.linspace(0,np.pi,n))**2
buf=np.zeros(int(SR*(TOTAL+0.5)))
def put(t,x):
    i=int(t*SR); buf[i:i+len(x)]+=x[:max(0,len(buf)-i)]
for i,s in enumerate(SC):
    k=s["base"]/s["dur"]; st=starts[i]
    put(st,sfx("tick")); put(st+s["dur"]-0.24,sfx("whoosh"))
    for rt,kind in base[i]["sfx"]: put(st+rt/k,sfx(kind))
import wave
buf=np.clip(buf,-0.95,0.95)
with wave.open(str(OUT/"sfx.wav"),"wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf*32767).astype(np.int16).tobytes())
# frames
fr=OUT/"frames"; fr.mkdir(exist_ok=True)
with sync_playwright() as p:
    br=p.chromium.launch(); pg=br.new_page(viewport={"width":1080,"height":1920})
    pg.goto(page.as_uri()); pg.wait_for_timeout(500)
    for k in range(int(TOTAL*30)):
        pg.evaluate(f"render({k/30})"); pg.screenshot(path=str(fr/f"{k:04d}.jpg"),type="jpeg",quality=92)
    br.close()
# audio: voz (highpass 70, compresor, loudnorm -16) + sfx a 0.55, recorte final
flt=(f"[0:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=11,"
     f"afade=t=out:st={TOTAL-0.15}:d=0.15[v];[1:a]volume=0.55,atrim=0:{TOTAL},asetpts=PTS-STARTPTS[x];[v][x]amix=inputs=2:duration=first:normalize=0[a]")
subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate","30","-i",str(fr/"%04d.jpg"),"-i",VOZ,"-i",str(OUT/"sfx.wav"),
  "-filter_complex",flt.replace("[0:a]","[1:a]").replace("[1:a]volume","[2:a]volume") if False else
  f"[1:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={TOTAL-0.15}:d=0.15[v];[2:a]volume=0.55,atrim=0:{TOTAL},asetpts=PTS-STARTPTS[x];[v][x]amix=inputs=2:duration=first:normalize=0[a]",
  "-map","0:v","-map","[a]","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-t",str(TOTAL),"-movflags","+faststart",
  str(OUT/"video-final.mp4")],check=True)
print("OK",TOTAL,[s["dur"] for s in SC])
