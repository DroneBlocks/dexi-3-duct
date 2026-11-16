#!/usr/bin/env python3
"""Estimate waterjet cut path length for DEXI-3 plates.
A waterjet cuts the flat 2D profile: outer silhouette + every interior hole.
We find the largest planar face (top/bottom face of the flat plate) and sum
the lengths of its outer wire + all inner wires (holes/cutouts)."""
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_WIRE
from OCP.TopExp import TopExp_Explorer
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.gp import gp_Dir
from OCP.ShapeAnalysis import ShapeAnalysis
from OCP.TopoDS import TopoDS

MM_PER_IN = 25.4

def face_area(face):
    g = GProp_GProps(); BRepGProp.SurfaceProperties_s(face, g); return g.Mass()

def edge_len(edge):
    g = GProp_GProps(); BRepGProp.LinearProperties_s(edge, g); return g.Mass()

def wire_len(wire):
    exp = TopExp_Explorer(wire, TopAbs_EDGE); tot = 0.0
    while exp.More():
        tot += edge_len(exp.Current()); exp.Next()
    return tot

def analyze(path, label):
    shape = cq.importers.importStep(path).val().wrapped
    # gather planar faces whose normal is ~vertical (the flat plate faces)
    best = None  # (area, face)
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    flat_faces = []
    while exp.More():
        f = TopoDS.Face_s(exp.Current())
        surf = BRepAdaptor_Surface(f)
        if surf.GetType() == GeomAbs_Plane:
            n = surf.Plane().Axis().Direction()
            if abs(n.Z()) > 0.99:  # normal ~ along Z => flat top/bottom face
                a = face_area(f)
                flat_faces.append((a, f, n.Z()))
        exp.Next()
    flat_faces.sort(key=lambda t: -t[0])
    area, face, nz = flat_faces[0]
    # outer + inner wires of that face
    outer = ShapeAnalysis.OuterWire_s(face)
    outer_len = wire_len(outer)
    wexp = TopExp_Explorer(face, TopAbs_WIRE)
    total_wire = 0.0; nwires = 0; inner_len = 0.0
    while wexp.More():
        w = wexp.Current(); L = wire_len(w); total_wire += L; nwires += 1
        if not w.IsSame(outer): inner_len += L
        wexp.Next()
    print(f"\n=== {label} ===")
    print(f"  flat face area      : {area/100:.1f} cm^2   ({area/MM_PER_IN**2:.1f} in^2)")
    print(f"  bounding flat faces : {len(flat_faces)} candidate faces")
    print(f"  wires on face       : {nwires} (1 outer + {nwires-1} holes/cutouts)")
    print(f"  outer perimeter     : {outer_len:.1f} mm   ({outer_len/MM_PER_IN:.1f} in)")
    print(f"  inner (holes) total : {inner_len:.1f} mm   ({inner_len/MM_PER_IN:.1f} in)")
    print(f"  TOTAL cut path      : {total_wire:.1f} mm   ({total_wire/MM_PER_IN:.2f} in)")
    return total_wire/MM_PER_IN

if __name__ == "__main__":
    rate = 75.0  # in/hr (Wazer Desktop, ballpark)
    grand = 0.0
    for path,label in [("top_sym.step","DEXI-3 TOP plate"),("bottom_sym.step","DEXI-3 BOTTOM plate")]:
        grand += analyze(path, label)
    print(f"\n=== TOTALS (top + bottom) ===")
    print(f"  combined cut path   : {grand:.1f} in")
    print(f"  @ {rate:.0f} in/hr        : {grand/rate*60:.1f} min")
