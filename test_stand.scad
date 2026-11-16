// =============================================================
// DEXI-3 duct TEST ARTICLE (one printable piece):
//   duct  +  central motor hub (real DEXI-3 bolt pattern)  +  spokes  +  side tab
// The duct is rigidly tied to the motor so the load cell/scale reads the TOTAL
// system thrust (rotor thrust + duct lip suction) — the whole point of the test.
//
// Orientation: prop plane at z=0 (the throat). Bellmouth points +Z (intake, up),
// diffuser points -Z (exhaust, down). Mount prop-DOWN with open air above & below.
//
// >>> MEASURE motor_mount_z (motor base face -> prop plane) before printing. <<<
// =============================================================

// ---- duct (match dexi3_duct.scad) ----
Dt = 76.2;
tip_clearance = 1.0;            // print one of {0.5, 1.0, 2.0}
lip_ratio = 0.13; diff_len_ratio = 0.50; diff_half_angle = 5;
throat_h = 4.0; wall = 1.6; $fn = 160;

// ---- motor mount (measured from DEXI 3 Top Plate Symmetrical.step) ----
motor_bore   = 4.5;   // central pass-through (plate bore was Ø4.0; +clearance)
motor_screw  = 2.7;   // M2.5 clearance (plate holes were Ø2.5)
motor_bcr    = 4.5;   // 4 screws on a cross at R4.5 (= 9 mm across flats)
hub_d = 20; hub_h = 5;
motor_mount_z = 18;   // <-- prop plane (z=0) -> motor mount face. MEASURE THIS.

// ---- holder ----
spokes = 3; spoke_w = 4.5; spoke_h = 4.5;
tab_thk = 5; tab_hole = 3.4;   // M3 tab to bolt the article to the stand arm

R_throat = Dt/2 + tip_clearance; r_lip = lip_ratio*Dt; Ld = diff_len_ratio*Dt;
exit_r = R_throat + Ld*tan(diff_half_angle); Cx = R_throat + r_lip; rim_r = Cx;

arc_n = 48;
arc_in  = [for (i=[0:arc_n]) let(a=90+i*90/arc_n)  [Cx+r_lip*cos(a),        r_lip*sin(a)]];
arc_out = [for (i=[0:arc_n]) let(a=180-i*90/arc_n) [Cx+(r_lip-wall)*cos(a), (r_lip-wall)*sin(a)]];
section = concat(arc_in,
    [[R_throat,-throat_h],[exit_r,-(throat_h+Ld)],[exit_r+wall,-(throat_h+Ld)],[R_throat+wall,-throat_h]],
    arc_out);

module duct() rotate_extrude(angle=360) polygon(section);

module hub() difference() {
    cylinder(h=hub_h, d=hub_d);
    translate([0,0,-1]) cylinder(h=hub_h+2, d=motor_bore);
    for (a=[0:90:359]) rotate([0,0,a]) translate([motor_bcr,0,-1]) cylinder(h=hub_h+2, d=motor_screw);
}

// spoke: from hub rim (axis, at motor_mount_z) out to the bellmouth rim
module spoke() hull() {
    translate([hub_d/2-1, 0, motor_mount_z+spoke_h/2]) cube([0.1, spoke_w, spoke_h], center=true);
    translate([rim_r-2,   0, r_lip+spoke_h/2])         cube([0.1, spoke_w, spoke_h], center=true);
}

module side_tab() difference() {
    translate([rim_r-1, 0, r_lip-tab_thk/2]) cube([14, tab_thk*2, tab_thk], center=false);
    translate([rim_r+7, tab_thk, r_lip]) cylinder(h=tab_thk*4, d=tab_hole, center=true);
}

duct();
translate([0,0,motor_mount_z]) hub();
for (i=[0:spokes-1]) rotate([0,0,i*360/spokes]) spoke();
side_tab();
