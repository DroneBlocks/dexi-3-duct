#!/usr/bin/env python3
"""Visual + numeric fit verification: overlays the corrected duct on the real
DEXI-3 top plate geometry (from top_sym.step). Emits dexi3_fit_verify.svg with a
top view (duct footprints vs bores/guards/mount-holes) and a side cross-section."""
import cadquery as cq, numpy as np, math
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
import frame_duct as fd

solid = cq.importers.importStep("top_sym.step").val()
bb=solid.BoundingBox(); cx=(bb.xmin+bb.xmax)/2; cy=(bb.ymin+bb.ymax)/2
W,H=bb.xlen,bb.ylen
motors=[(sx*53.10, sy*55.00) for sy in(1,-1) for sx in(-1,1)]   # plate-centered

# unique vertical holes (plate plane), plate-centered coords
seen=set(); holes=[]
for f in solid.Faces():
    ad=BRepAdaptor_Surface(f.wrapped)
    if ad.GetType()!=GeomAbs_Cylinder: continue
    c=ad.Cylinder()
    if abs(c.Axis().Direction().Z())<0.9: continue
    l=c.Location()
    if l.Z()>50: continue
    k=(round(2*c.Radius(),2),round(l.X(),1),round(l.Y(),1))
    if k in seen: continue
    seen.add(k); holes.append((2*c.Radius(), l.X()-cx, l.Y()-cy))

# ---- numeric checks ----
print("=== FIT CHECKS ===")
fr=fd.flange_r; thr=fd.Dt/2+1.0   # 1mm gap throat radius
# adjacent flange clearance
gx=106.2-2*fr; gy=110.0-2*fr
print(f"flange Ø{2*fr:.0f}: adjacent gap x={gx:+.1f}mm y={gy:+.1f}mm  -> {'OK' if min(gx,gy)>2 else 'COLLIDE'}")
print(f"flange Ø{2*fr:.0f} vs guard Ø94: {'inside guard (OK)' if 2*fr<=94 else 'OVERHANGS guard'}")
print(f"throat Ø{2*thr:.1f}+walls Ø{2*(thr+fd.wall):.1f} vs bore Ø80: seats on plate face (cannot pass bore) -> by design")
# screw holes land on real Ø3 @ R43.5 ?
for mi,(mx,my) in enumerate(motors):
    real=[(math.degrees(math.atan2(y-my,x-mx)))%360 for d,x,y in holes
          if abs(d-3.0)<0.1 and 42<((x-mx)**2+(y-my)**2)**0.5<45]
    duct=[(fd.screw_ang0+i*90)%360 for i in range(fd.n_screw)]
    land=sum(any(abs((a-b+180)%360-180)<3 for a in duct) for b in real)
    print(f"motor{mi} real Ø3 holes at {sorted(round(r) for r in real)} -> {land}/{len(real)} duct holes align")

# ---- SVG ----
SC=2.2; PAD=30; pw=W*SC+2*PAD
top_h=H*SC+2*PAD
side_h=120*SC*0.5+2*PAD
def X(x): return PAD+(x+W/2)*SC
def Y(y): return PAD+(H/2-y)*SC     # flip
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw:.0f}" height="{top_h+side_h+40:.0f}" '
   f'font-family="sans-serif" font-size="9">']
s.append(f'<rect width="100%" height="100%" fill="white"/>')
s.append(f'<text x="{PAD}" y="18" font-size="13" font-weight="bold">DEXI-3 duct fit — top plate (top_sym.step), 1.0mm tip gap</text>')
# plate outline
s.append(f'<rect x="{X(-W/2):.1f}" y="{Y(H/2):.1f}" width="{W*SC:.1f}" height="{H*SC:.1f}" '
         f'fill="#f4f4f4" stroke="#999"/>')
# real holes
for d,x,y in holes:
    r=d/2*SC
    col="#bbb"
    if abs(d-80)<0.5: col="#3366cc"     # bore
    elif abs(d-94)<0.5: col="#88aacc"   # guard rim
    elif abs(d-3.0)<0.1: col="none"
    if abs(d-3.0)<0.1:
        s.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r:.1f}" fill="#cc3333" stroke="#cc3333"/>')
    elif abs(d-80)<0.5 or abs(d-94)<0.5:
        s.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r:.1f}" fill="none" stroke="{col}" stroke-width="1.3"/>')
# duct overlays at each motor
for mx,my in motors:
    # flange footprint (dashed green)
    s.append(f'<circle cx="{X(mx):.1f}" cy="{Y(my):.1f}" r="{fr*SC:.1f}" fill="rgba(40,160,40,0.08)" '
             f'stroke="#2a2" stroke-width="1.3" stroke-dasharray="4,3"/>')
    # throat (solid green)
    s.append(f'<circle cx="{X(mx):.1f}" cy="{Y(my):.1f}" r="{thr*SC:.1f}" fill="none" stroke="#2a2" stroke-width="1"/>')
    # duct screw holes (4 corners) — ring if it lands on a real hole, x if not
    for i in range(fd.n_screw):
        a=math.radians(fd.screw_ang0+i*90)
        hx,hy=mx+fd.screw_bcr*math.cos(a), my+fd.screw_bcr*math.sin(a)
        lands=any(abs(d-3.0)<0.1 and ((x-hx)**2+(y-hy)**2)**0.5<2 for d,x,y in holes)
        c="#2a2" if lands else "#e8a"
        s.append(f'<circle cx="{X(hx):.1f}" cy="{Y(hy):.1f}" r="{fd.screw_d/2*SC:.1f}" '
                 f'fill="none" stroke="{c}" stroke-width="1.6"/>')
# legend
ly=top_h-4
s.append(f'<text x="{PAD}" y="{ly:.0f}" fill="#3366cc">○ Ø80 bore</text>'
         f'<text x="{PAD+70}" y="{ly:.0f}" fill="#cc3333">● Ø3 mount hole (real)</text>'
         f'<text x="{PAD+220}" y="{ly:.0f}" fill="#2a2">▱ duct flange/throat/screws</text>'
         f'<text x="{PAD+400}" y="{ly:.0f}" fill="#e8a">○ duct screw w/ no frame hole</text>')

# ---- side cross-section (one duct) ----
oy=top_h+30; sx0=PAD+60; ssc=SC
def SX(x): return sx0+(x+50)*ssc
def SY(z): return oy+ (20-z)*ssc       # z up
s.append(f'<text x="{PAD}" y="{oy-6:.0f}" font-size="12" font-weight="bold">Cross-section (z=0 prop plane, plate underside at A={fd.A}mm)</text>')
poly,_=fd.profile(1.0)
# right half + mirrored left, plate
pts_r=" ".join(f"{SX(r):.1f},{SY(z):.1f}" for r,z in poly)
pts_l=" ".join(f"{SX(-r):.1f},{SY(z):.1f}" for r,z in poly)
s.append(f'<polygon points="{pts_r}" fill="#cfe6cf" stroke="#2a2" stroke-width="1"/>')
s.append(f'<polygon points="{pts_l}" fill="#cfe6cf" stroke="#2a2" stroke-width="1"/>')
# plate (2.5mm) sitting at z=A..A+2.5, bore Ø80 gap
pt=fd.plate_t
for sgn in (1,-1):
    s.append(f'<rect x="{SX(sgn*40) if sgn<0 else SX(40):.1f}" y="{SY(fd.A+pt):.1f}" '
             f'width="{(50-40+5)*ssc:.1f}" height="{pt*ssc:.1f}" fill="#ddd" stroke="#999"/>')
# prop disk
s.append(f'<line x1="{SX(-fd.Dt/2):.1f}" y1="{SY(0):.1f}" x2="{SX(fd.Dt/2):.1f}" y2="{SY(0):.1f}" '
         f'stroke="#c33" stroke-width="2"/>')
s.append(f'<text x="{SX(0)-18:.1f}" y="{SY(0)-4:.1f}" fill="#c33">prop Ø76.2</text>')
s.append(f'<text x="{SX(46):.1f}" y="{SY(fd.A)+3:.1f}" fill="#666">plate</text>')
s.append(f'<text x="{SX(fd.Dt/2+3):.1f}" y="{SY(-fd.Ld):.1f}" fill="#2a2">diffuser exit Ø84.8</text>')
s.append("</svg>")
open("dexi3_fit_verify.svg","w").write("\n".join(s))
print("\nwrote dexi3_fit_verify.svg")
