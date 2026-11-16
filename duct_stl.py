#!/usr/bin/env python3
"""Mesh the DEXI-3 duct to a watertight binary STL by revolving the wall
cross-section 360 deg. Pure numpy; emits the tip-clearance sweep."""
import numpy as np, struct, sys

def section(Dt, tip, lip_ratio=0.13, diff_len_ratio=0.50, diff_half=5.0,
            throat_h=4.0, wall=1.6, arc_n=48):
    R = Dt/2 + tip
    r_lip = lip_ratio*Dt
    Ld = diff_len_ratio*Dt
    exit_r = R + Ld*np.tan(np.radians(diff_half))
    Cx = R + r_lip
    a_in  = np.radians(np.linspace(90, 180, arc_n))
    a_out = np.radians(np.linspace(180, 90, arc_n))
    arc_in  = np.c_[Cx + r_lip*np.cos(a_in),        r_lip*np.sin(a_in)]
    arc_out = np.c_[Cx + (r_lip-wall)*np.cos(a_out), (r_lip-wall)*np.sin(a_out)]
    mid = np.array([[R,        -throat_h],
                    [exit_r,   -(throat_h+Ld)],
                    [exit_r+wall, -(throat_h+Ld)],
                    [R+wall,   -throat_h]])
    P = np.vstack([arc_in, mid, arc_out])           # closed loop (r,z)
    return P, dict(throat_d=2*R, exit_d=2*exit_r, rim_d=2*Cx, height=r_lip+throat_h+Ld)

def revolve(P, N=160):
    th = np.linspace(0, 2*np.pi, N, endpoint=False)
    r = P[:,0][:,None]; z = P[:,1][:,None]
    ring = np.stack([r*np.cos(th), r*np.sin(th), np.broadcast_to(z, (len(P), N))], -1)  # (M,N,3)
    M = len(P)
    inext = (np.arange(M)+1) % M
    jnext = (np.arange(N)+1) % N
    p00 = ring
    p10 = ring[inext]
    p01 = ring[:, jnext]
    p11 = ring[inext][:, jnext]
    t1 = np.stack([p00, p10, p11], 2).reshape(-1, 3, 3)
    t2 = np.stack([p00, p11, p01], 2).reshape(-1, 3, 3)
    return np.concatenate([t1, t2])

def write_stl(tris, path):
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
    ln = np.linalg.norm(n, axis=1, keepdims=True); ln[ln==0]=1; n/=ln
    with open(path, "wb") as f:
        f.write(b"DEXI-3 rotor duct" + b"\0"*(80-17))
        f.write(struct.pack("<I", len(tris)))
        buf = bytearray()
        for tri, nz in zip(tris, n):
            buf += struct.pack("<3f", *nz)
            for v in tri: buf += struct.pack("<3f", *v)
            buf += struct.pack("<H", 0)
        f.write(buf)

Dt = 76.2
for tip in (0.5, 1.0, 2.0):
    P, d = section(Dt, tip)
    tris = revolve(P)
    name = f"dexi3_duct_gap{tip:.1f}mm.stl"
    write_stl(tris, name)
    print(f"{name:32s} tris={len(tris):6d}  throatØ{d['throat_d']:.1f}  "
          f"exitØ{d['exit_d']:.1f}  rimØ{d['rim_d']:.1f}  H{d['height']:.1f}")
print("done")
