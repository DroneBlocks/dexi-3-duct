#!/usr/bin/env python3
"""Side cross-section of the bench test article: motor + prop sitting in the throat."""
import numpy as np
# geometry (integrated.py, tip=1.0), blade plane = z0, throat centered on it
Dt=76.2; prop_r=Dt/2; tip=1.0; R=prop_r+tip          # throat inner r 39.1
r_lip=9.9; Cx=R+r_lip; wall=1.6; th=4.0; Ld=38.1
exit_r=R+Ld*np.tan(np.radians(5))
tt,tb=th/2,-th/2                                      # throat band +2..-2
mz=18.0; hub_r=10; hub_h=5; motor_r=14                # motor mount face at +mz; motor bell ~Ø28
# duct inner profile (r,z): rim -> throat -> exit
ain=np.radians(np.linspace(90,180,30))
inner=[(Cx+r_lip*np.cos(a), tt+r_lip*np.sin(a)) for a in ain]+[(R,tb),(exit_r,tb-Ld)]
outer=[(exit_r+wall,tb-Ld),(R+wall,tb)]+[(Cx+(r_lip-wall)*np.cos(a),tt+(r_lip-wall)*np.sin(a)) for a in np.radians(np.linspace(180,90,30))]
prof=np.array(inner+outer)

s=5.2; padL=150; padR=150; padT=70; padB=60
zmin,zmax=tb-Ld-3, mz+hub_h+8
W=2*Cx*s+padL+padR; H=(zmax-zmin)*s+padT+padB
def X(r): return W/2+r*s
def Y(z): return padT+(zmax-z)*s
o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" font-family="Helvetica,Arial" font-size="13">',
   f'<rect width="{W:.0f}" height="{H:.0f}" fill="white"/>']
def poly(p,**k):
    a=" ".join(f'{kk.replace("_","-")}="{vv}"' for kk,vv in k.items())
    return f'<polygon points="{" ".join(f"{X(r):.1f},{Y(z):.1f}" for r,z in p)}" {a}/>'
def line(r1,z1,r2,z2,**k):
    a=" ".join(f'{kk.replace("_","-")}="{vv}"' for kk,vv in k.items())
    return f'<line x1="{X(r1):.1f}" y1="{Y(z1):.1f}" x2="{X(r2):.1f}" y2="{Y(z2):.1f}" {a}/>'
def txt(r,z,t,**k):
    a=" ".join(f'{kk.replace("_","-")}="{vv}"' for kk,vv in k.items())
    return f'<text x="{X(r):.1f}" y="{Y(z):.1f}" {a}>{t}</text>'
def rect(r0,z0,r1,z1,**k):
    a=" ".join(f'{kk.replace("_","-")}="{vv}"' for kk,vv in k.items())
    return f'<rect x="{X(min(r0,r1)):.1f}" y="{Y(max(z0,z1)):.1f}" width="{abs(r1-r0)*s:.1f}" height="{abs(z1-z0)*s:.1f}" {a}/>'
o.append('<defs><marker id="a" markerWidth="9" markerHeight="9" refX="4.5" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#444"/></marker></defs>')
# duct (both sides)
for m in (1,-1):
    o.append(poly([(m*r,z) for r,z in prof],fill="#cfe0f2",stroke="#356",stroke_width="1.3"))
# motor body + hub (center)
o.append(rect(-motor_r,0,motor_r,mz,fill="#9fe0d8",stroke="#3a8"))
o.append(txt(0,mz*0.55,"motor",text_anchor="middle",fill="#246",font_size="13"))
o.append(rect(-hub_r,mz,hub_r,mz+hub_h,fill="#b9a4c8",stroke="#6a4a8a"))
o.append(txt(0,mz+hub_h+5,"hub (motor bolts here, Ø4 + 4×Ø2.5)",text_anchor="middle",fill="#6a4a8a",font_size="11"))
# spokes (hub -> rim)
for m in (1,-1):
    o.append(poly([(m*hub_r,mz),(m*hub_r,mz-3),(m*(Cx-2),tt+r_lip-2),(m*(Cx-2),tt+r_lip)],fill="#b9a4c8",stroke="#6a4a8a",stroke_width="0.8"))
# prop (blade plane at z0)
o.append(line(-prop_r,0,prop_r,0,stroke="#c0392b",stroke_width="3"))
o.append(txt(0,-3,"prop blade plane",text_anchor="middle",fill="#c0392b",font_size="11"))
# throat band highlight
o.append(rect(R,tb,R+wall,tt,fill="#f5b86b",stroke="none"))
o.append(rect(-R-wall,tb,-R,tt,fill="#f5b86b",stroke="none"))
# ===== dimensions =====
g="#1a5"
# motor mount -> prop (vertical, left)
xL=-Cx-6
o.append(line(xL,0,xL,mz,stroke=g,stroke_width="1.3",marker_start="url(#a)",marker_end="url(#a)"))
o.append(txt(xL-1,mz/2,"18 mm",text_anchor="end",fill=g,font_weight="bold",font_size="13"))
o.append(txt(xL-1,mz/2-4.5,"motor mount → prop",text_anchor="end",fill=g,font_size="10.5"))
# prop diameter (bottom)
zP=tb-Ld-1
o.append(line(-prop_r,zP,prop_r,zP,stroke="#c0392b",stroke_width="1",marker_start="url(#a)",marker_end="url(#a)"))
o.append(txt(0,zP-3,"prop Ø76.2 (3\")",text_anchor="middle",fill="#c0392b",font_size="12"))
# throat diameter
o.append(txt(0,tb-7,"throat Ø78.2",text_anchor="middle",fill=g,font_size="12"))
# total height (right)
xR=Cx+10
o.append(line(xR,tb-Ld,xR,tt+r_lip,stroke="#888",stroke_width="1",marker_start="url(#a)",marker_end="url(#a)"))
o.append(f'<text x="{X(xR)+5:.1f}" y="{(Y(tb-Ld)+Y(tt+r_lip))/2:.1f}" fill="#888" font-size="11">~52 mm tall</text>')
o.append(txt(Cx-2,tt+r_lip+2,"bellmouth (intake)",fill="#356",font_size="10.5"))
o.append(txt(exit_r+2,tb-Ld,"diffuser exit",fill="#356",font_size="10.5"))
# ===== tip-gap zoom inset (lower-right empty area) with leader =====
zx,zy,zs=W-150,H-170,26     # inset center px, scale px/mm
o.append(f'<line x1="{X(R+wall):.0f}" y1="{Y(0):.0f}" x2="{zx-70:.0f}" y2="{zy-55:.0f}" stroke="#caa" stroke-width="1" stroke-dasharray="4 3"/>')
o.append(f'<rect x="{zx-95:.0f}" y="{zy-70:.0f}" width="195" height="160" fill="#fffdf5" stroke="#caa" rx="6"/>')
o.append(f'<text x="{zx:.0f}" y="{zy-52:.0f}" text-anchor="middle" font-size="12" font-weight="bold">tip gap (zoom)</text>')
def ZX(dr): return zx+dr*zs
def ZY(dz): return zy+10-dz*zs
# throat wall (orange) from r=R..R+wall
o.append(f'<rect x="{ZX(0):.0f}" y="{ZY(2):.0f}" width="{wall*zs:.0f}" height="{4*zs:.0f}" fill="#f5b86b" stroke="#c80"/>')
o.append(f'<text x="{ZX(wall/2):.0f}" y="{ZY(2)-4:.0f}" text-anchor="middle" font-size="10" fill="#c80">throat wall</text>')
# prop tip (red) approaching from left
o.append(f'<line x1="{ZX(-2.0):.0f}" y1="{ZY(0):.0f}" x2="{ZX(-tip):.0f}" y2="{ZY(0):.0f}" stroke="#c0392b" stroke-width="4"/>')
o.append(f'<text x="{ZX(-1.5):.0f}" y="{ZY(0)+18:.0f}" text-anchor="middle" font-size="10" fill="#c0392b">prop tip</text>')
# the 1mm gap
o.append(f'<line x1="{ZX(-tip):.0f}" y1="{ZY(0):.0f}" x2="{ZX(0):.0f}" y2="{ZY(0):.0f}" stroke="#1a5" stroke-width="1.5" marker-start="url(#a)" marker-end="url(#a)"/>')
o.append(f'<text x="{ZX(-tip/2):.0f}" y="{ZY(0)-6:.0f}" text-anchor="middle" font-size="11" fill="#1a5" font-weight="bold">1.0 mm</text>')
# title
o.append(f'<text x="{W/2:.0f}" y="26" text-anchor="middle" font-size="16" font-weight="bold">Bench test article — how the prop sits in the throat</text>')
o.append(f'<text x="{W/2:.0f}" y="44" text-anchor="middle" font-size="12" fill="#666">orange = throat ring (the tight band); prop tips run 1 mm inside it</text>')
o.append('</svg>')
open("side_profile.svg","w").write("".join(o))
print("wrote side_profile.svg")
