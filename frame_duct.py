#!/usr/bin/env python3
"""Frame-mount DEXI-3 duct, CORRECTED against the canonical STEP
(DEXI 3 Top Plate Symmetrical.step -> top_sym.step).

Verified frame facts (CAD kernel, see inspect_frame.py):
  prop bore     = Ø80.0  (NOT the Ø88.3 the old version used -> that made it too big)
  motor spacing = 106.2 x 110.0 mm, motors at (±53.1, ±55.0)
  guard rim     = Ø94.0 around each bore
  mount holes   = Ø3.0 @ R43.5, 4 corner positions (45/135/225/315), inboard one
                  omitted per motor. A 4-hole flange is universal -> use the 3 that land.

Motors mount inverted (prop hangs ~A=14mm below the top-plate underside, blows down).
The Ø80 bore ≈ Ø76.2 prop, so the throat ring (outer ~Ø81 w/ walls) can't drop THROUGH
the bore; the duct seats UP against the plate underside (flange annulus Ø80->Ø93) and
hangs down: short contraction -> throat at the prop plane -> diffuser exhausting below.
3x M3 up into the Ø3 @ R43.5 holes retain it; lift self-seats the flange. z=0 at the
prop blade plane. CSG via manifold3d."""
import numpy as np, struct
try:
    import manifold3d as m
    FN=180; m.set_circular_segments(FN); Mani=m.Manifold
except ModuleNotFoundError:
    m=None; FN=180        # constants/profile() still importable without the CSG kernel

Dt=76.2; wall=1.6
bore_r=40.0            # Ø80 TRUE prop bore (was 44.15/Ø88.3 -> oversize bug)
plate_t=2.5
A=14.0                 # MEASURED: plate underside -> prop blade plane
throat_h=4.0
inlet_in=40.0          # inlet opening radius = bore (Ø80); ~no room for a bellmouth
flange_r=46.5          # seats on plate underside, inside the Ø94 guard; clears neighbors
flange_h=2.0
Ld=38.0; diff_half=5.0 # diffuser length / half-angle
screw_d=3.4; screw_bcr=43.5; n_screw=4; screw_ang0=45.0   # M3 clearance @ R43.5, 4 corners

def profile(tip, n=44):
    R=Dt/2+tip                                              # throat radius
    fb=A-flange_h                                           # flange bottom z; TOP face at A = plate underside
    exit_r=R+Ld*np.tan(np.radians(diff_half))
    tt=throat_h/2; tb=-throat_h/2
    u=np.linspace(0,1,n); sm=(1-np.cos(np.pi*u))/2
    in_z=A-u*(A-tt);  in_r=inlet_in+(R-inlet_in)*sm        # inner, top->down: (inlet_in,A)->(R,tt)
    ou_z=tt+u*(fb-tt); ou_r=(R+wall)+((inlet_in+wall)-(R+wall))*sm  # outer, bottom->up
    pts =list(zip(in_r,in_z))
    pts+=[(R,tb),(exit_r,tb-Ld),(exit_r+wall,tb-Ld),(R+wall,tb)]    # throat in, diffuser, exit, throat out
    pts+=list(zip(ou_r,ou_z))                              # throat out top + outer contraction
    pts+=[(flange_r,fb),(flange_r,A)]                      # flange; closes (flange_r,A)->(inlet_in,A) seat
    return np.array(pts), dict(throat=2*R,exit=2*exit_r,flange=2*flange_r,inletID=2*inlet_in)

def build(tip):
    poly,d=profile(tip)
    cs=m.CrossSection([poly.tolist()], m.FillRule.Positive)
    if cs.area()<=0: cs=m.CrossSection([poly[::-1].tolist()], m.FillRule.Positive)
    part=cs.revolve(circular_segments=FN, revolve_degrees=360)
    for i in range(n_screw):                               # M3 clearance holes through flange
        a=np.radians(screw_ang0+i*360/n_screw)
        part-=Mani.cylinder(8, screw_d/2, screw_d/2, 48).translate(
              [screw_bcr*np.cos(a), screw_bcr*np.sin(a), A-flange_h-1])
    return part,d

def write_stl(part,path):
    msh=part.to_mesh(); V=np.asarray(msh.vert_properties)[:,:3]; F=np.asarray(msh.tri_verts)
    tris=V[F]; nrm=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    ln=np.linalg.norm(nrm,axis=1,keepdims=True); ln[ln==0]=1; nrm/=ln
    with open(path,'wb') as f:
        hdr=b'DEXI-3 frame-mount duct (D80 bore corrected)'; f.write(hdr+b'\0'*(80-len(hdr))); f.write(struct.pack('<I',len(F)))
        b=bytearray()
        for t,nz in zip(tris,nrm):
            b+=struct.pack('<3f',*nz)
            for v in t: b+=struct.pack('<3f',*v)
            b+=struct.pack('<H',0)
        f.write(b)
    return len(F),part.genus(),len(part.decompose()),part.volume()

if __name__=="__main__":
    for tip in (0.5,1.0,2.0):
        part,d=build(tip)
        name=f"dexi3_frame_duct_gap{tip:.1f}mm.stl"
        nt,g,bodies,vol=write_stl(part,name)
        print(f"{name:34s} tris={nt:6d} bodies={bodies} vol={vol/1000:.1f}cm3  "
              f"throatØ{d['throat']:.1f} inletID Ø{d['inletID']:.1f} flangeØ{d['flange']:.0f} exitØ{d['exit']:.1f}")
    print(f"done; bore Ø{2*bore_r:.0f}  A={A}  {n_screw}x M3 @ R{screw_bcr} (45/135/225/315; use the 3 that land)")
