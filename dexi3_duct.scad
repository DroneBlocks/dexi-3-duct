// =============================================================
// DEXI-3 rotor duct (shroud) — parametric test article
// Geometry per Pereira (2008) ducted-rotor study, as summarized at
// https://capolight.wordpress.com/2015/01/14/quadcopter-rotor-duct/
//
// The flow surface is fully determined by ONE number: prop diameter (Dt).
// Everything else is a ratio of Dt. Change Dt at the top and the whole
// duct regenerates. Default values are for the DEXI-3's 3" props.
// =============================================================

// ---------- PRIMARY INPUT ----------
Dt = 76.2;            // prop diameter [mm]  (3" = 76.2)

// ---------- DUCT RATIOS (from the paper) ----------
lip_ratio       = 0.13;   // inlet lip (bellmouth) radius  = 13% of Dt
diff_len_ratio  = 0.50;   // diffuser length               = 50% of Dt (min-height choice; paper allows 50-72%)
diff_half_angle = 5;      // diffuser half-angle [deg]      (10 deg included)

// ---------- TIP CLEARANCE ----------
// Paper's optimum is 0.1% of Dt (= 0.076 mm on a 3" prop) — NOT printable
// and below prop runout. Default to a measurable, printable gap and sweep it.
tip_clearance   = 0.5;    // radial gap, blade tip -> throat wall [mm]
// tip_clearance = 0.001*Dt;  // <- the paper's "optimal" value, for reference

// ---------- PRINT / STRUCTURE ----------
throat_h = 4.0;   // straight throat section height [mm] (>= blade+hub thickness)
wall     = 1.6;   // shell wall thickness [mm] (4 perimeters @ 0.4 nozzle)
$fn      = 200;

// ---------- DERIVED ----------
R_throat = Dt/2 + tip_clearance;            // throat (flow) radius
r_lip    = lip_ratio * Dt;                  // bellmouth radius
Ld       = diff_len_ratio * Dt;             // diffuser length
exit_r   = R_throat + Ld*tan(diff_half_angle);
Cx       = R_throat + r_lip;                // lip arc center, r-axis
total_h  = r_lip + throat_h + Ld;           // overall height
rim_r    = R_throat + r_lip;                // widest point (bellmouth rim)

echo(str("Dt=", Dt, "  throat_Dia=", 2*R_throat, "  exit_Dia=", 2*exit_r,
         "  rim_Dia(widest)=", 2*rim_r, "  height=", total_h));

// ---------- 2D WALL CROSS-SECTION (revolved) ----------
arc_n = 48;
// lip inner arc: rim (a=90) -> throat top (a=180), radius r_lip about Cx
arc_in  = [ for (i=[0:arc_n]) let(a = 90 + i*90/arc_n)
              [Cx + r_lip*cos(a), r_lip*sin(a)] ];
// lip outer arc: throat top (a=180) -> rim (a=90), radius (r_lip - wall) about Cx
arc_out = [ for (i=[0:arc_n]) let(a = 180 - i*90/arc_n)
              [Cx + (r_lip - wall)*cos(a), (r_lip - wall)*sin(a)] ];

section = concat(
    arc_in,                                   // I1 rim-inner .. I2 throat-top-inner
    [ [R_throat,        -throat_h],           // I3 throat bottom inner
      [exit_r,          -(throat_h + Ld)],    // I4 diffuser exit inner
      [exit_r + wall,   -(throat_h + Ld)],    // O1 diffuser exit outer
      [R_throat + wall, -throat_h] ],         // O2 throat bottom outer
    arc_out                                   // O3 throat-top-outer .. O4 rim-outer
);

module duct() {
    rotate_extrude(angle = 360) polygon(points = section);
}

// ---------- OPTIONAL mounting tabs (placeholder) ----------
// Final mount keys off the DEXI-3 top plate hole pattern (TBD). These are
// just example ears so you can see clearance; set make_tabs=true to preview.
make_tabs  = false;
tab_count  = 3;
tab_len    = 10;      // radial reach beyond rim
tab_th     = 4;       // tab thickness
tab_hole   = 3.2;     // M3 clearance
tab_z      = -throat_h; // tab plane (at throat base)

module tab() {
    difference() {
        translate([rim_r - 2, 0, tab_z - tab_th/2])
            cube([tab_len + 2, tab_th*2, tab_th], center = false);
        translate([rim_r + tab_len/2, tab_th, tab_z])
            cylinder(h = tab_th*4, d = tab_hole, center = true);
    }
}

duct();
if (make_tabs)
    for (i = [0:tab_count-1]) rotate([0,0, i*360/tab_count]) tab();
