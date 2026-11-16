#!/usr/bin/env python3
"""2in DEXI-3 frame from the CORRECT source (the *Symmetrical.step files, tessellated
to top_sym.stl/bottom_sym.stl). Scale X/Y, restore FC 25mm + motor pattern full size,
keep FULL guard rings. Outputs printable STLs."""
import struct, numpy as np, manifold3d as m
FN=128; m.set_circular_segments(FN); Mani=m.Manifold

CX,CY=-20.4,85.8          # true plate center (motor centroid), file coords
k=0.685                   # 3"->2": bore Ø80->Ø55, motors ±53/±55 -> ±36.4/±37.7
mx,my=53.1*k,55.0*k

def load_manifold(p):
    with open(p,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        d=np.frombuffer(f.read(n*50),dtype=np.uint8).reshape(n,50)
    V=d[:,12:48].copy().view('<f4').reshape(-1,3)
    u,inv=np.unique(np.round(V,3),axis=0,return_inverse=True)
    return Mani(m.Mesh(vert_properties=u.astype(np.float32),tri_verts=inv.reshape(-1,3).astype(np.uint32)))

def recenter_scale(name):
    p=load_manifold(name); bb=p.bounding_box()
    p=p.translate([-CX,-CY,-bb[2]]).scale([k,k,1.0])   # center at origin, z from 0, scale XY
    return p, p.bounding_box()[5]-p.bounding_box()[2]

def write_stl(part,path):
    msh=part.to_mesh(); V=np.asarray(msh.vert_properties)[:,:3]; F=np.asarray(msh.tri_verts)
    t=V[F]; nr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); ln=np.linalg.norm(nr,axis=1,keepdims=True); ln[ln==0]=1; nr/=ln
    with open(path,'wb') as f:
        f.write(b'DEXI-3 2in (from STEP)'+b'\0'*(80-22)); f.write(struct.pack('<I',len(F)))
        b=bytearray()
        for tri,n in zip(t,nr):
            b+=struct.pack('<3f',*n)
            for v in tri: b+=struct.pack('<3f',*v)
            b+=struct.pack('<H',0)
        f.write(b)

# ---- TOP ----
top,H=recenter_scale("top_sym.stl")
def cyl(d,x,y): return Mani.cylinder(H+2,d/2,d/2,48).translate([x,y,-1])
def disk(d,x,y): return Mani.cylinder(H,d/2,d/2,FN).translate([x,y,0])
# preserve the original center cutout: do NOT fill with a solid pad.
# Just plug the 4 SCALED FC holes so the new full-size ones don't leave doubles.
for sx in(-1,1):
  for sy in(-1,1):
    top += disk(5.0, sx*12.7*k, sy*12.7*k)             # tiny plug at scaled FC pos
    top += disk(14, sx*mx, sy*my)                       # motor-hub reinforcement (local)
for sx in(-1,1):
  for sy in(-1,1): top -= cyl(3.0, sx*12.7, sy*12.7)   # FC 25.4mm square (full size)
for sx in(-1,1):
  for sy in(-1,1):
    top -= cyl(4.0, sx*mx, sy*my)                      # motor center Ø4
    for a in (0,90,180,270):
        top -= cyl(2.5, sx*mx+4.5*np.cos(np.radians(a)), sy*my+4.5*np.sin(np.radians(a)))
write_stl(top,"dexi3_2in_top_plate_v2.stl")
bt=top.bounding_box()
print(f"TOP  bodies={len(top.decompose())} vol={top.volume()/1000:.1f}cm3  {bt[3]-bt[0]:.0f}x{bt[4]-bt[1]:.0f}x{bt[5]-bt[2]:.1f}mm  motors ±{mx:.1f}/±{my:.1f}")

# ---- BOTTOM ----
bot,Hb=recenter_scale("bottom_sym.stl")
write_stl(bot,"dexi3_2in_bottom_plate_v2.stl")
bb=bot.bounding_box()
print(f"BOT  bodies={len(bot.decompose())} vol={bot.volume()/1000:.1f}cm3  {bb[3]-bb[0]:.0f}x{bb[4]-bb[1]:.0f}x{bb[5]-bb[2]:.1f}mm")
print("wrote dexi3_2in_top_plate_v2.stl + dexi3_2in_bottom_plate_v2.stl")
