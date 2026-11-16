#!/usr/bin/env python3
"""Build the integrated DEXI-3 duct test article (duct + motor hub + spokes + tab)
as one watertight STL, for the tip-clearance sweep. CSG via manifold3d."""
import manifold3d as m
import numpy as np, struct

FN = 160
m.set_circular_segments(FN)
Mani = m.Manifold

# ---- duct params ----
Dt = 76.2
lip_ratio, diff_len_ratio, diff_half = 0.13, 0.50, 5.0
throat_h, wall = 4.0, 1.6
# ---- motor mount (measured from STEP) ----
motor_bore, motor_screw, motor_bcr = 4.5, 2.7, 4.5
hub_d, hub_h = 20.0, 5.0
motor_mount_z = 18.0          # prop plane (z=0) -> motor base
# ---- holder ----
spoke_w, spoke_h, n_spokes = 4.5, 4.5, 3
tab_thk, tab_hole, tab_reach = 5.0, 3.4, 14.0

def duct_poly(tip, arc_n=64):
    R = Dt/2 + tip; r_lip = lip_ratio*Dt; Ld = diff_len_ratio*Dt
    exit_r = R + Ld*np.tan(np.radians(diff_half)); Cx = R + r_lip
    a_in  = np.radians(np.linspace(90, 180, arc_n))
    a_out = np.radians(np.linspace(180, 90, arc_n))
    pts  = [(Cx+r_lip*np.cos(a),        r_lip*np.sin(a))        for a in a_in]
    pts += [(R,-throat_h), (exit_r,-(throat_h+Ld)),
            (exit_r+wall,-(throat_h+Ld)), (R+wall,-throat_h)]
    pts += [(Cx+(r_lip-wall)*np.cos(a), (r_lip-wall)*np.sin(a)) for a in a_out]
    return np.array(pts), R, r_lip, Ld, exit_r, Cx

def box(sx,sy,sz, x,y,z):                       # centered cube at (x,y,z)
    return Mani.cube([sx,sy,sz], True).translate([x,y,z])

def build(tip):
    poly, R, r_lip, Ld, exit_r, Cx = duct_poly(tip)
    cs = m.CrossSection([poly.tolist()], m.FillRule.Positive)
    if cs.area() <= 0:                            # fix winding if needed
        cs = m.CrossSection([poly[::-1].tolist()], m.FillRule.Positive)
    duct = cs.revolve(circular_segments=FN, revolve_degrees=360)  # axis already +Z
    rim_r = Cx

    # motor hub at z = motor_mount_z
    hub = Mani.cylinder(hub_h, hub_d/2, hub_d/2, FN)
    hub -= Mani.cylinder(hub_h+2, motor_bore/2, motor_bore/2, FN).translate([0,0,-1])
    for a in (0,90,180,270):
        sx, sy = motor_bcr*np.cos(np.radians(a)), motor_bcr*np.sin(np.radians(a))
        hub -= Mani.cylinder(hub_h+2, motor_screw/2, motor_screw/2, FN).translate([sx,sy,-1])
    hub = hub.translate([0,0,motor_mount_z])

    # spokes: hub edge (z=motor_mount_z) -> bellmouth rim (z=r_lip)
    a_box = box(2, spoke_w, spoke_h, hub_d/2-1, 0, motor_mount_z+spoke_h/2)
    b_box = box(6, spoke_w, spoke_h+3, rim_r-2, 0, r_lip-2)   # embed into the rim wall
    one_spoke = Mani.batch_hull([a_box, b_box])
    spokes = one_spoke
    for i in range(1, n_spokes):
        spokes += one_spoke.rotate([0,0,i*360/n_spokes])

    # side tab on the rim
    tab = box(tab_reach, tab_thk*2, tab_thk, rim_r-1+tab_reach/2, 0, r_lip-tab_thk/2)
    tab -= Mani.cylinder(tab_thk*4, tab_hole/2, tab_hole/2, FN).translate(
            [rim_r-1+tab_reach*0.7, 0, r_lip]).rotate([0,0,0])

    part = duct + hub + spokes + tab
    return part, dict(rim=2*rim_r, exit=2*exit_r, throat=2*R)

def write_stl(part, path):
    mesh = part.to_mesh()
    V = np.asarray(mesh.vert_properties)[:, :3]
    F = np.asarray(mesh.tri_verts)
    tris = V[F]                                   # (T,3,3)
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
    ln = np.linalg.norm(n,axis=1,keepdims=True); ln[ln==0]=1; n/=ln
    with open(path,"wb") as f:
        f.write(b"DEXI-3 duct test article"+b"\0"*(80-24))
        f.write(struct.pack("<I", len(F)))
        buf=bytearray()
        for tri,nz in zip(tris,n):
            buf += struct.pack("<3f",*nz)
            for v in tri: buf += struct.pack("<3f",*v)
            buf += struct.pack("<H",0)
        f.write(buf)
    return len(F), part.genus(), part.volume()

for tip in (0.5,1.0,2.0):
    part, d = build(tip)
    comps = len(part.decompose())                 # connected bodies (must be 1)
    name = f"dexi3_test_article_gap{tip:.1f}mm.stl"
    nt, genus, vol = write_stl(part, name)
    print(f"{name:36s} tris={nt:6d} bodies={comps} vol={vol/1000:.1f}cm3  "
          f"throatØ{d['throat']:.1f} rimØ{d['rim']:.1f}")
print("done; motor_mount_z =", motor_mount_z)
