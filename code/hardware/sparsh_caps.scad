// SPARSH tactile caps - OpenSCAD version of hardware/make_caps.py (same parameters)
// Open in OpenSCAD, pick SYMBOL and VARIANT, F6 to render, File > Export STL.
// All units mm. MEASURE YOUR ROCKER with calipers before printing the sleeve variant.

SYMBOL  = "dot";    // v1 vocabulary: "dot" (light) | "cross" (fan) | "triangle" (socket) | "square" (other); pilot extras: "line" "ring" "double_dot"
VARIANT = "tile";   // "tile" (adhesive) | "sleeve" (friction fit)

TILE = 15; BASE_T = 1.2; CORNER_R = 2; S = 10.5;
ROCKER_W = 16.5; ROCKER_H = 27.0; FIT = 0.15; WALL = 1.0; SLEEVE_DEPTH = 3.2;
function relief(n) = n=="dot"?1.5 : n=="line"?1.0 : n=="triangle"?1.25 : n=="ring"?0.8 : n=="cross"?1.1 : n=="double_dot"?1.3 : 0.9;
$fn = 64;

module rrect(w,h,r,t){ linear_extrude(t) offset(r) square([w-2*r,h-2*r],center=true); }
module dome(r,h){ R=(r*r+h*h)/(2*h); intersection(){ translate([0,0,h-R]) sphere(R); translate([-R,-R,0]) cube([2*R,2*R,h]); } }

module symbol(n){
  h = relief(n);
  if (n=="dot") dome(S*0.5,h);
  else if (n=="double_dot") { translate([-S*0.27,0,0]) dome(S*0.24,h); translate([S*0.27,0,0]) dome(S*0.24,h); }
  else if (n=="line") linear_extrude(h) offset(1.25) square([S-2.5,0.01],center=true);
  else if (n=="triangle") linear_extrude(h) offset(0.5) offset(-0.5) circle(r=S*0.58,$fn=3);
  else if (n=="ring") linear_extrude(h) difference(){ circle(S/2); circle(S/2-1.8); }
  else if (n=="cross") linear_extrude(h) union(){ square([S,2.2],center=true); square([2.2,S],center=true); }
  else linear_extrude(h) offset(1) square([S*0.95-2,S*0.95-2],center=true);
}

module tile(n){
  rrect(TILE,TILE,CORNER_R,BASE_T);
  translate([0,0,BASE_T]) symbol(n);
  if (n!="triangle") translate([-1.5,TILE/2-1.4,BASE_T]) cube([3,0.8,0.4]); // orientation tick (top edge)
}

module sleeve(n){
  iw=ROCKER_W+2*FIT; ih=ROCKER_H+2*FIT;
  difference(){ rrect(iw+2*WALL, ih+2*WALL, 1.5, SLEEVE_DEPTH+BASE_T); translate([0,0,-0.01]) rrect(iw,ih,1,SLEEVE_DEPTH+0.01); }
  translate([0, ih*0.22, SLEEVE_DEPTH+BASE_T]) symbol(n);
}

if (VARIANT=="tile") tile(SYMBOL); else sleeve(SYMBOL);
