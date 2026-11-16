#!/usr/bin/env python3
"""Analyze a duct A/B bench test: thrust, RPM, V, A -> power, g/W, and the gains.
Usage:  .venv/bin/python analyze_bench.py [bench_test_log.csv]
        .venv/bin/python analyze_bench.py --demo   (built-in example numbers)
"""
import sys, csv, numpy as np

DEMO = {  # throttle: (thrust_g, rpm, V, A)
 'open': [(60,6000,11.1,1.0),(110,9000,11.0,2.2),(180,12000,10.9,4.0),(270,15000,10.8,6.5),
          (380,18000,10.6,9.8),(500,21000,10.4,14.0),(720,26000,10.0,24.0)],
 'duct': [(78,6000,11.1,1.15),(142,9000,11.0,2.5),(232,12000,10.9,4.5),(348,15000,10.7,7.3),
          (490,18000,10.5,11.0),(645,21000,10.3,15.6),(920,26000,9.9,26.0)],
}

def load(path):
    d={'open':[],'duct':[]}
    with open(path) as f:
        for r in csv.DictReader(f):
            try: row=(float(r['thrust_g']),float(r['rpm']),float(r['volts']),float(r['amps']))
            except (ValueError,KeyError): continue
            if r['config'] in d: d[r['config']].append(row)
    return d

def prep(rows):
    a=np.array(sorted(rows, key=lambda x:x[1]))           # sort by rpm
    thrust,rpm,V,A=a.T; P=V*A; gpw=thrust/P
    return dict(thrust=thrust,rpm=rpm,P=P,gpw=gpw)

src = '--demo' if '--demo' in sys.argv else (sys.argv[1] if len(sys.argv)>1 else 'bench_test_log.csv')
data = {k:[(t,r,v,a) for (t,r,v,a) in v] for k,v in DEMO.items()} if src=='--demo' else load(src)
if not data['open'] or not data['duct']:
    print("Need both 'open' and 'duct' rows filled in. (Try --demo to see sample output.)"); sys.exit()
O,D = prep(data['open']), prep(data['duct'])

# --- gains ---
print(f"source: {src}\n")
print("THRUST GAIN at matched RPM:")
for rpm in np.linspace(max(O['rpm'].min(),D['rpm'].min()), min(O['rpm'].max(),D['rpm'].max()), 4):
    to=np.interp(rpm,O['rpm'],O['thrust']); td=np.interp(rpm,D['rpm'],D['thrust'])
    print(f"  {rpm:6.0f} rpm:  open {to:5.0f} g  ->  duct {td:5.0f} g   (+{100*(td-to)/to:4.1f}%)")
print("\nEFFICIENCY (g/W) + POWER SAVED at matched THRUST:")
lo,hi=max(O['thrust'].min(),D['thrust'].min()), min(O['thrust'].max(),D['thrust'].max())
for th in np.linspace(lo,hi,4):
    eo=np.interp(th,O['thrust'],O['gpw']); ed=np.interp(th,D['thrust'],D['gpw'])
    po=np.interp(th,O['thrust'],O['P']);   pd=np.interp(th,D['thrust'],D['P'])
    print(f"  {th:5.0f} g:  open {eo:4.2f} g/W -> duct {ed:4.2f} g/W (+{100*(ed-eo)/eo:4.1f}%)   "
          f"power {po:5.1f}W -> {pd:5.1f}W (save {100*(po-pd)/po:4.1f}%)")

# ---- WIN/LOSE verdict at hover, accounting for the duct's own weight ----
DUCT_MASS_G = 15.0    # <-- weigh one printed duct
AUW_G       = 1000.0  # <-- your all-up weight (open-prop config)
hov_o = AUW_G/4.0                 # hover thrust per motor, open
hov_d = AUW_G/4.0 + DUCT_MASS_G   # ...with ducts: each motor also lifts its duct
print(f"\nHOVER VERDICT  (AUW {AUW_G:.0f} g, duct {DUCT_MASS_G:.0f} g/ea):")
if hov_o<lo or hov_d>hi:
    print(f"  hover thrust {hov_o:.0f}->{hov_d:.0f} g/motor is outside your test range {lo:.0f}-{hi:.0f} g — sweep wider.")
else:
    eo=np.interp(hov_o,O['thrust'],O['gpw']); ed=np.interp(hov_d,D['thrust'],D['gpw'])
    Po=4*hov_o/eo; Pd=4*hov_d/ed
    breakeven=100*DUCT_MASS_G/hov_o; gain=100*(ed-eo)/eo
    print(f"  efficiency gain at hover: {gain:+.1f}%   (break-even needed: {breakeven:.1f}%)")
    print(f"  total hover power: open {Po:.0f} W  ->  ducted {Pd:.0f} W  ({100*(Po-Pd)/Po:+.1f}%)")
    print(f"  >>> {'WIN' if Pd<Po else 'LOSE'} — ducts {'save' if Pd<Po else 'cost'} "
          f"{abs(100*(Po-Pd)/Po):.1f}% hover power after carrying their own weight")

# --- SVG: thrust vs power, and g/W vs thrust ---
def panel(ox,oy,w,h,xO,yO,xD,yD,xlab,ylab,title):
    xs=np.r_[xO,xD]; ys=np.r_[yO,yD]; x0,x1=xs.min(),xs.max(); y0,y1=0,ys.max()*1.08
    def X(x): return ox+(x-x0)/(x1-x0)*w
    def Y(y): return oy+h-(y-y0)/(y1-y0)*h
    s=[f'<rect x="{ox}" y="{oy}" width="{w}" height="{h}" fill="#fafbfc" stroke="#ccc"/>',
       f'<text x="{ox+w/2}" y="{oy-8}" text-anchor="middle" font-weight="bold" font-size="13">{title}</text>',
       f'<text x="{ox+w/2}" y="{oy+h+34}" text-anchor="middle" font-size="11">{xlab}</text>',
       f'<text x="{ox-34}" y="{oy+h/2}" text-anchor="middle" font-size="11" transform="rotate(-90 {ox-34} {oy+h/2})">{ylab}</text>']
    for frac in (0,.25,.5,.75,1):
        s.append(f'<text x="{ox-6}" y="{Y(y0+frac*(y1-y0))+4}" text-anchor="end" font-size="9" fill="#888">{y0+frac*(y1-y0):.0f}</text>')
        s.append(f'<text x="{X(x0+frac*(x1-x0))}" y="{oy+h+15}" text-anchor="middle" font-size="9" fill="#888">{x0+frac*(x1-x0):.0f}</text>')
    for xv,yv,col,nm in [(xO,yO,'#c0392b','open'),(xD,yD,'#1a5cff','duct')]:
        pts=" ".join(f"{X(a):.1f},{Y(b):.1f}" for a,b in zip(xv,yv))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"/>')
        for a,b in zip(xv,yv): s.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="2.5" fill="{col}"/>')
    return "".join(s)
W,H=900,420
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     f'<text x="{W/2}" y="24" text-anchor="middle" font-size="15" font-weight="bold">Duct A/B bench test ({src})</text>',
     '<rect x="690" y="40" width="12" height="12" fill="#c0392b"/><text x="708" y="50" font-size="12">open prop</text>',
     '<rect x="690" y="58" width="12" height="12" fill="#1a5cff"/><text x="708" y="68" font-size="12">ducted</text>',
     panel(70,70,360,300,O['P'],O['thrust'],D['P'],D['thrust'],"electrical power (W)","thrust (g)","more thrust per watt = higher"),
     panel(510,70,330,300,O['thrust'],O['gpw'],D['thrust'],D['gpw'],"thrust (g)","efficiency (g/W)","efficiency vs thrust"),
     '</svg>']
open("bench_results.svg","w").write("".join(svg))
print("\nwrote bench_results.svg")
