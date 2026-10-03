"""Generate the profile's original artwork. Requires Pillow >= 10.

Run: python scripts/build_art.py
Use --stills for a fast layout pass; --font-dir selects a font directory.
The drawing is a conceptual surface, not a scan or live security telemetry.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from functools import lru_cache
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
TAU = math.tau
BG = "#090F12"
PANEL = "#10191D"
GRID = "#1B292D"
MUTED = "#98ADA9"
WHITE = "#F0F3E8"
ACID = "#D4FC51"
CYAN = "#75D9D0"
S = 2
FONT_DIR = Path("C:/Windows/Fonts")


@lru_cache(maxsize=64)
def font(size, kind="sans"):
    choices = {
        "display": ["ariblk.ttf", "DejaVuSans-Bold.ttf"],
        "sans": ["segoeui.ttf", "DejaVuSans.ttf"],
        "bold": ["segoeuib.ttf", "DejaVuSans-Bold.ttf"],
        "mono": ["consola.ttf", "DejaVuSansMono.ttf"],
    }
    dirs = [FONT_DIR, Path("/usr/share/fonts/truetype/dejavu")]
    for directory in dirs:
        for name in choices[kind]:
            path = directory / name
            if path.exists():
                return ImageFont.truetype(str(path), round(size * S))
    raise FileNotFoundError("Provide --font-dir with Segoe UI/Arial or DejaVu fonts.")


def color_mix(a, b, t):
    a = tuple(bytes.fromhex(a.removeprefix("#")))
    b = tuple(bytes.fromhex(b.removeprefix("#")))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class Art:
    def __init__(self, width, height, im=None):
        self.im = im if im is not None else Image.new("RGB", (width*S, height*S), BG)
        self.d = ImageDraw.Draw(self.im)

    def line(self, pts, fill=GRID, width=1):
        self.d.line([(round(x*S), round(y*S)) for x, y in pts], fill=fill, width=max(1, round(width*S)))

    def rect(self, box, fill=None, outline=None, width=1):
        self.d.rectangle(tuple(round(v*S) for v in box), fill=fill, outline=outline, width=round(width*S))

    def circle(self, x, y, r, fill=None, outline=None, width=1):
        self.d.ellipse(tuple(round(v*S) for v in (x-r,y-r,x+r,y+r)),fill=fill,outline=outline,width=round(width*S))

    def text(self, x, y, value, size, fill=WHITE, kind="sans"):
        self.d.text((round(x*S), round(y*S)), value, font=font(size, kind), fill=fill, anchor="lt")

    def cross(self, x, y, r=5, fill=MUTED):
        self.line([(x-r,y),(x+r,y)],fill)
        self.line([(x,y-r),(x,y+r)],fill)

    def finish(self):
        return self.im.resize((self.im.width//S, self.im.height//S),Image.Resampling.LANCZOS)


def background(mobile=False):
    w,h = (720,850) if mobile else (1280,600)
    a = Art(w,h)
    a.rect((0,0,w-1,h-1),outline="#2B393D")
    # A measured, sparse grid under the object only.
    left,top,bottom = (26,320,688) if mobile else (790,88,433)
    for x in range(left,w-24,24):
        for y in range(top,bottom,24):
            a.rect((x,y,x+.7,y+.7),fill=GRID)
    a.rect((0,0,6,72),fill=ACID)
    a.cross(42,38,7,ACID)
    a.text(62,28,"GK / INDEPENDENT",16,ACID,"mono")
    a.text(w-212,28,"RESEARCH + BUILD",16,MUTED,"mono")
    a.line([(32,66),(w-32,66)])
    if mobile:
        a.text(33,91,"GKDATA",110,WHITE,"display")
        a.text(38,218,"GARRETT KOHLRUSCH",19,ACID,"mono")
        a.text(38,265,"Web security. Bug bounty. Toolmaking.",25,WHITE)
        a.text(38,335,"01 / SURFACE STUDY",14,MUTED,"mono")
        a.line([(32,706),(w-32,706)])
        for x,num,head in [(38,"01","RECON"),(275,"02","RESEARCH"),(519,"03","TOOLS")]:
            a.text(x,734,num,14,ACID,"mono")
            a.text(x,764,head,21,WHITE,"bold")
        a.text(38,813,"MAP THE SURFACE. FOLLOW THE EVIDENCE.",14,MUTED,"mono")
    else:
        a.text(41,107,"GKDATA",134,WHITE,"display")
        a.text(50,272,"GARRETT KOHLRUSCH",20,ACID,"mono")
        a.text(49,326,"Web security. Bug bounty.",31,WHITE)
        a.text(49,367,"Tools for the work.",31,WHITE)
        a.text(811,90,"01 / SURFACE STUDY",13,MUTED,"mono")
        a.text(1120,414,"GK / LAB",13,MUTED,"mono")
        a.line([(32,490),(w-32,490)])
        for x,num,head,desc in [(49,"01","RECON","Map the surface"),(454,"02","RESEARCH","Follow the evidence"),(871,"03","TOOLS","Make it repeatable")]:
            a.text(x,519,num,15,ACID,"mono")
            a.text(x+37,515,head,20,WHITE,"bold")
            a.text(x+37,551,desc,17,MUTED)
        a.line([(421,515),(421,570)])
        a.line([(838,515),(838,570)])
    return a.im


def point(u,v,phase):
    # A slowly precessing torus: wireframe surface + one illuminated meridian.
    major,minor=120,51
    x=(major+minor*math.cos(v))*math.cos(u)
    y=(major+minor*math.cos(v))*math.sin(u)
    z=minor*math.sin(v)
    roll=.50 + .12*math.sin(phase)
    tilt=.96 + .16*math.cos(phase)
    yy=y*math.cos(tilt)-z*math.sin(tilt)
    zz=y*math.sin(tilt)+z*math.cos(tilt)
    xx=x*math.cos(roll)-yy*math.sin(roll)
    yy=x*math.sin(roll)+yy*math.cos(roll)
    return xx,yy,zz


def object_frame(base, phase, mobile=False):
    a=Art(0,0,base.copy())
    cx,cy,scale=(362,500,.94) if mobile else (1020,278,1.0)
    def p(u,v):
        x,y,z=point(u,v,phase)
        return cx+x*scale,cy+y*scale,z
    # Orbit and coordinate markers frame the sculpture without pretending to be data.
    a.circle(cx,cy,190*scale,outline=GRID)
    a.circle(cx,cy,203*scale,outline="#142125")
    for theta in [i*TAU/60 for i in range(60)]:
        r=203*scale
        a.line([(cx+math.cos(theta)*r,cy+math.sin(theta)*r),(cx+math.cos(theta)*(r+3),cy+math.sin(theta)*(r+3))],"#34454A")
    a.cross(cx,cy,7,"#475D60")
    segments=[]
    # Depth-sorted fine lines maintain a readable volume throughout the loop.
    for u in [i*TAU/32 for i in range(32)]:
        for j in range(52):
            q1=p(u,j*TAU/52);q2=p(u,(j+1)*TAU/52)
            segments.append((.5*(q1[2]+q2[2]),q1,q2,False))
    for v in [i*TAU/12 for i in range(12)]:
        for j in range(104):
            q1=p(j*TAU/104,v);q2=p((j+1)*TAU/104,v)
            segments.append((.5*(q1[2]+q2[2]),q1,q2,False))
    for j in range(104):
        q1=p(phase,j*TAU/104);q2=p(phase,(j+1)*TAU/104)
        segments.append((.5*(q1[2]+q2[2]),q1,q2,True))
    for depth,q1,q2,lit in sorted(segments,key=lambda q:q[0]):
        t=max(0,min(1,(depth+165)/330))
        color=color_mix("#344427",ACID,.35+.65*t) if lit else color_mix("#1C3034","#77A29B",t*.78)
        a.line([(q1[0],q1[1]),(q2[0],q2[1])],color,2 if lit else .8)
    # Packet-shaped markers follow a single closed route.
    for offset in [0,2.10,4.20]:
        x,y,z=p(phase+offset,.4)
        a.circle(x,y,5.0,fill=BG,outline=ACID,width=1.5)
        a.circle(x,y,1.6,fill=ACID)
    theta=-phase
    r=203*scale
    x,y=cx+math.cos(theta)*r,cy+math.sin(theta)*r
    a.rect((x-3,y-3,x+3,y+3),fill=ACID)
    return a.finish()


def card(name,title,kicker,lines,index,accent):
    # The cards are static, sharp SVGs; motion belongs to the masthead.
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="260" viewBox="0 0 400 260" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(". ".join(lines))}</desc>',
         f'<rect x=".5" y=".5" width="399" height="259" rx="0" fill="{BG}" stroke="#314146"/>',
         f'<path d="M0 0H58V4H0Z" fill="{accent}"/>']
    def text(x,y,s,size=12,color=MUTED,family="monospace",weight=400):
        out.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}">{escape(s)}</text>')
    def line(path,color=GRID,width=1):
        out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    text(24,33,f"0{index} / {kicker}",11,accent)
    if index==1:
        for i in range(5):
            x,y=295+i*7,57+i*5
            line(f'M{x} {y} h49 v53 h-49 Z',"#3B504C")
        line('M326 77h25m-25 9h18m-18 9h25',accent,2)
    elif index==2:
        for i in range(7):
            line(f'M{288+i*10} 54v66',"#2E4448")
        for i in range(6):
            line(f'M288 {54+i*12}h60',"#2E4448")
        out.append(f'<rect x="316" y="78" width="16" height="16" fill="{accent}"/>')
        line('M313 67V54h-13m38 13V54h13m-38 48v13h-13m38-13v13h13',accent)
    else:
        line('M300 61l-22 24 22 24m47-48 22 24-22 24m-16-57-17 68',accent,2)
    text(24,130,title,34,WHITE,"Arial, Helvetica, sans-serif",700)
    for i,s in enumerate(lines):text(25,161+i*20,s,13,MUTED,"Arial, Helvetica, sans-serif")
    line('M24 211H376',"#2B3C3F")
    text(25,239,'EXPLORE' if index!=2 else 'EXPLORE / BETA',11,accent)
    line('M353 237l11-11m-11 0h11v11',accent,1.5)
    out.append('</svg>')
    (OUT/f"project-{name}.svg").write_text('\n'.join(out)+"\n",encoding="utf-8")


def main():
    global FONT_DIR
    parser=argparse.ArgumentParser()
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--font-dir',type=Path,default=FONT_DIR)
    args=parser.parse_args()
    FONT_DIR=args.font_dir
    OUT.mkdir(exist_ok=True)
    for mobile in [False,True]:
        stem='profile-hero-mobile' if mobile else 'profile-hero'
        base=background(mobile)
        still=object_frame(base,.5,mobile)
        still.save(OUT/f'{stem}-static.png',optimize=True)
        if not args.stills:
            # Shared palette prevents shimmer; delta frames keep downloads small.
            # Motion assets target the actual GitHub column; stills retain full size.
            motion_size=(576,680) if mobile else (1024,480)
            palette=still.resize(motion_size,Image.Resampling.LANCZOS).quantize(colors=160,method=Image.Quantize.MEDIANCUT)
            frames=[]
            for i in range(96):
                frame=object_frame(base,.5+TAU*i/96,mobile).resize(motion_size,Image.Resampling.LANCZOS)
                frames.append(frame.quantize(palette=palette,dither=Image.Dither.NONE))
            frames[0].save(OUT/f'{stem}.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=1)
            print(f'{stem}.gif: {(OUT/f"{stem}.gif").stat().st_size:,} bytes, 96 frames, 7.68 seconds')
    card('vulns','vulns.co','FIELD LIBRARY',['Research tools, methods,','utilities and MCP resources.'],1,ACID)
    card('misconfig','misconfig.ai','EXPOSURE REVIEW',['Authorized exposure review.','Private evidence history.'],2,CYAN)
    card('gkdata','gkdata.io','INDEPENDENT STUDIO',['Security reviews and','websites built with care.'],3,ACID)


if __name__=='__main__':
    main()
