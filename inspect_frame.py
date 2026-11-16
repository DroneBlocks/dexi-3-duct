#!/usr/bin/env python3
"""Authoritative geometry extraction from the DEXI-3 top plate STEP.
Lists every cylindrical face (vertical-axis = a drilled hole), its radius and
XY center, then clusters them around the 4 motor positions so we can see the
real bore diameter and the real mounting-hole pattern the duct must match."""
import cadquery as cq
import numpy as np
from collections import defaultdict
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

wp = cq.importers.importStep("top_sym.step")
solid = wp.val()

# collect cylindrical faces
holes = []
for f in solid.Faces():
    ad = BRepAdaptor_Surface(f.wrapped)
    if ad.GetType() != GeomAbs_Cylinder:
        continue
    cyl = ad.Cylinder()
    ax = cyl.Axis().Direction()
    nx, ny, nz = ax.X(), ax.Y(), ax.Z()
    loc = cyl.Location()
    r = cyl.Radius()
    # only vertical-axis cylinders are through-holes / bores
    if abs(nz) > 0.9:
        holes.append((r, loc.X(), loc.Y(), loc.Z(), f.Area()))

# plate bounding box / center
bb = solid.BoundingBox()
cx = (bb.xmin + bb.xmax) / 2
cy = (bb.ymin + bb.ymax) / 2
print(f"Plate bbox: X[{bb.xmin:.1f},{bb.xmax:.1f}] Y[{bb.ymin:.1f},{bb.ymax:.1f}] "
      f"Z[{bb.zmin:.1f},{bb.zmax:.1f}]  size {bb.xlen:.1f}x{bb.ylen:.1f}x{bb.zlen:.1f}")
print(f"Plate center (file coords): ({cx:.2f}, {cy:.2f})")
print(f"{len(holes)} vertical-axis cylindrical faces\n")

# the 4 motor quadrant centers ~ (cx +/- a, cy +/- b). Cluster holes by quadrant
# relative to plate center, then within a quadrant print radius+local offset.
quad = defaultdict(list)
for r, x, y, z, area in holes:
    sx = '+' if x >= cx else '-'
    sy = '+' if y >= cy else '-'
    quad[(sx, sy)].append((r, x - cx, y - cy, z, area))

# Use the quadrant with the most holes as the representative motor
rep = max(quad.values(), key=len)
# its motor-pattern center = the small-radius cluster centroid (bore + screw holes
# share one axis center: the center bore is the largest-near-center small circle)
print("=== Representative motor quadrant (offsets from plate center) ===")
for r, dx, dy, z, area in sorted(rep, key=lambda h: -h[0]):
    print(f"  Ø{2*r:6.2f}  center=({dx:+7.2f},{dy:+7.2f})  z={z:6.2f}")

# Identify motor axis = centroid of the tiny screw holes (Ø<6) in this quadrant
screws = [(r, dx, dy) for r, dx, dy, z, a in rep if 2*r < 6.0]
if screws:
    max_ = np.mean([s[1] for s in screws])
    may_ = np.mean([s[2] for s in screws])
    print(f"\nMotor axis (screw-cluster centroid): offset ({max_:+.2f},{may_:+.2f}) from plate center")
    print("  -> holes re-expressed about the MOTOR axis:")
    for r, dx, dy, z, a in sorted(rep, key=lambda h: -h[0]):
        rx, ry = dx - max_, dy - may_
        rad = (rx**2 + ry**2) ** 0.5
        print(f"    Ø{2*r:6.2f}  R={rad:6.2f}  ang={np.degrees(np.arctan2(ry,rx)):7.1f}  z={z:6.2f}")
