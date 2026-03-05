v {xschem version=3.0.0 file_version=1.2 }
G {}
K {}
V {}
S {}
E {}
N 2410 -3010 2410 -3000 {
lab=GND}
N 2410 -3090 2410 -3070 {
lab=vp}
N 2330 -3010 2330 -3000 {
lab=GND}
N 2330 -3090 2330 -3070 {
lab=vss}
N 1180 -2490 1200 -2490 {
lab=vx}
N 1040 -2490 1120 -2490 {
lab=inp}
N 1100 -2360 1120 -2360 {
lab=inp}
N 1100 -2490 1100 -2360 {
lab=inp}
N 1180 -2360 1190 -2360 {
lab=vx}
N 1190 -2360 1200 -2360 {
lab=vx}
N 1200 -2490 1200 -2360 {
lab=vx}
N 1150 -2380 1150 -2360 {
lab=vx}
N 1150 -2380 1190 -2380 {
lab=vx}
N 1190 -2380 1190 -2360 {
lab=vx}
N 1150 -2320 1150 -2290 {
lab=reset}
N 1150 -2230 1150 -2210 {
lab=GND}
N 940 -2490 1040 -2490 {
lab=inp}
N 830 -2570 860 -2570 {
lab=vdd}
N 830 -2530 860 -2530 {
lab=vx}
N 830 -2510 910 -2510 {
lab=vp}
N 830 -2490 850 -2490 {
lab=inp}
N 830 -2470 910 -2470 {
lab=GND}
N 910 -2470 910 -2450 {
lab=GND}
N 850 -2490 940 -2490 {
lab=inp}
N 910 -2510 930 -2510 {
lab=vp}
N 960 -2550 960 -2530 {
lab=GND}
N 830 -2550 890 -2550 {
lab=#net1}
N 950 -2550 960 -2550 {
lab=GND}
N 2090 -2450 2090 -2410 {
lab=GND}
N 2060 -2570 2110 -2570 {
lab=inp}
N 2060 -2510 2110 -2510 {
lab=inn}
N 2060 -2490 2110 -2490 {
lab=outn}
N 2060 -2550 2090 -2550 {
lab=ck}
N 2060 -2530 2090 -2530 {
lab=outp}
N 2060 -2590 2110 -2590 {
lab=vdd}
N 2060 -2450 2090 -2450 {
lab=GND}
N 2140 -2470 2140 -2450 {
lab=#net2}
N 2140 -2390 2140 -2370 {
lab=GND}
N 2060 -2470 2140 -2470 {
lab=#net2}
N 2320 -3200 2320 -3180 {
lab=GND}
N 2320 -3310 2320 -3260 {
lab=ck}
N 2510 -3210 2510 -3190 {
lab=GND}
N 2510 -3320 2510 -3270 {
lab=inn}
N 1940 -3050 1940 -3030 {
lab=in+}
N 1940 -2970 1940 -2950 {
lab=GND}
N 1940 -3060 1940 -3050 {
lab=in+}
N 1940 -3070 1940 -3060 {
lab=in+}
N 1940 -3140 1940 -3130 {
lab=in+}
N 1940 -3130 1940 -3070 {
lab=in+}
N 1450 -2780 1450 -2760 {
lab=GND}
N 1450 -2920 1450 -2870 {
lab=n5}
N 1450 -3010 1450 -2980 {
lab=#net3}
N 1450 -3010 1550 -3010 {
lab=#net3}
N 1450 -2810 1450 -2780 {
lab=GND}
N 1390 -2890 1450 -2890 {
lab=n5}
N 1610 -3010 1660 -3010 {
lab=vdd}
N 1200 -2500 1200 -2490 {
lab=vx}
N 1360 -2520 1360 -2500 {
lab=GND}
N 1200 -2580 1200 -2500 {
lab=vx}
N 1270 -2580 1360 -2580 {
lab=#net4}
N 1200 -2580 1210 -2580 {
lab=vx}
N 1520 -2980 1520 -2920 {
lab=#net3}
N 1500 -2980 1520 -2980 {
lab=#net3}
N 1500 -3010 1500 -2980 {
lab=#net3}
N 1520 -2860 1520 -2780 {
lab=GND}
N 1450 -2780 1520 -2780 {
lab=GND}
N 1190 -3090 1220 -3090 {
lab=vdd3v3}
N 1190 -3050 1220 -3050 {
lab=n5}
N 1190 -3010 1210 -3010 {
lab=#net3}
N 1190 -2990 1270 -2990 {
lab=GND}
N 1270 -2990 1270 -2970 {
lab=GND}
N 1320 -3070 1320 -3050 {
lab=GND}
N 1190 -3070 1250 -3070 {
lab=#net5}
N 1310 -3070 1320 -3070 {
lab=GND}
N 1190 -3030 1220 -3030 {
lab=in+}
N 1210 -3010 1220 -3010 {
lab=#net3}
N 1220 -3010 1340 -3010 {
lab=#net3}
N 2170 -3220 2170 -3200 {
lab=GND}
N 2170 -3300 2170 -3280 {
lab=vdd3v3}
N 1340 -3010 1390 -3010 {
lab=#net3}
N 1390 -3010 1450 -3010 {
lab=#net3}
C {devices/code_shown.sym} 2370 -2820 0 0 {name=s2 only_toplevel=false value="

.include /foss/design/single_slope/netgen/ldos_wores_pex.spice
.include /foss/design/single_slope/guncel_layoutlar/netgen/preamp_singleslope_new_pex.spice
.include /foss/design/single_slope/guncel_layoutlar/netgen/latch_singleslope_new_pex.spice
.include /foss/design/single_slope/guncel_layoutlar/netgen/opamp_singleslope_addcap_pex.spice
.option method = Gear

.control
set color0=white
save all

tran 10u 260u
plot inp inn outp outn
plot inp_neg inn outp_neg outn_neg
let i_1v8 = i(v4)
let i_3v3 = i(v6)
let i_g= i(v5)
let i_miller = i(v10)
let i_s= i(v1)
let i_d = i(v11)
let zort = vdd/i(v4)
plot i_1v8 i_3v3
plot v(vdd)
plot vdd3v3
plot i_1v8
plot i_3v3
plot i_g
plot i_miller
plot i_d
plot i_s
*show all
.endc
.end
"
}
C {devices/code.sym} 2070 -3070 0 0 {name=TT_MODELS1
only_toplevel=true
format="tcleval(@value )"
value=".lib $::SKYWATER_MODELS/sky130.lib.spice tt
.include $::SKYWATER_STDCELLS/sky130_fd_sc_hd.spice
"
spice_ignore=false
place=header}
C {devices/vsource.sym} 2410 -3040 0 0 {name=V9 value=0.2}
C {devices/gnd.sym} 2410 -3000 0 1 {name=l5 lab=GND}
C {devices/vsource.sym} 2330 -3040 0 0 {name=V7 value=0}
C {devices/gnd.sym} 2330 -3000 0 1 {name=l53 lab=GND}
C {devices/lab_pin.sym} 2330 -3090 0 0 {name=l54 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 2410 -3090 2 0 {name=l59 sig_type=std_logic lab=vp}
C {devices/capa.sym} 1150 -2490 1 0 {name=C1
m=1
value=20p
footprint=1206
device="ceramic capacitor"}
C {pdk/sky130A/libs.tech/xschem/sky130_fd_pr/nfet_01v8.sym} 1150 -2340 3 0 {name=M32
L=0.15
W=10
nf=1 
mult=2
ad="'int((nf+1)/2) * W/nf * 0.29'" 
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'" 
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'" nrs="'0.29 / W'"
sa=0 sb=0 sd=0
model=nfet_01v8
spiceprefix=X
}
C {devices/vsource.sym} 1150 -2260 0 0 {name=V22 value="PULSE(0 1.8 0 10p 10p 40n 256.04u)"}
C {devices/gnd.sym} 1150 -2210 0 0 {name=l81 lab=GND}
C {devices/lab_pin.sym} 860 -2570 2 0 {name=l82 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1150 -2300 0 0 {name=l83 sig_type=std_logic lab=reset}
C {devices/lab_pin.sym} 860 -2530 2 0 {name=l84 sig_type=std_logic lab=vx}
C {devices/gnd.sym} 910 -2450 0 0 {name=l85 lab=GND}
C {devices/lab_pin.sym} 1000 -2490 1 0 {name=l86 sig_type=std_logic lab=inp}
C {devices/isource.sym} 920 -2550 3 0 {name=I1 value=20u}
C {devices/gnd.sym} 960 -2530 0 0 {name=l87 lab=GND}
C {design/single_slope/opamp_singleslope_wcapnew.sym} 680 -2520 0 0 {name=x3}
C {devices/lab_pin.sym} 930 -2510 0 1 {name=l88 sig_type=std_logic lab=vp}
C {devices/gnd.sym} 2090 -2410 0 0 {name=l76 lab=GND}
C {devices/lab_pin.sym} 2110 -2590 0 1 {name=l79 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2090 -2550 0 1 {name=l107 sig_type=std_logic lab=ck}
C {devices/lab_pin.sym} 2110 -2570 0 1 {name=l108 sig_type=std_logic lab=inp}
C {devices/lab_pin.sym} 2110 -2510 0 1 {name=l109 sig_type=std_logic lab=inn}
C {devices/lab_pin.sym} 2090 -2530 0 1 {name=l110 sig_type=std_logic lab=outp}
C {devices/lab_pin.sym} 2110 -2490 0 1 {name=l111 sig_type=std_logic lab=outn}
C {devices/isource.sym} 2140 -2420 0 0 {name=I0 value=10u}
C {devices/gnd.sym} 2140 -2370 0 0 {name=l112 lab=GND}
C {design/single_slope/comparator_ss_h.sym} 1910 -2520 0 0 {name=x7}
C {devices/vsource.sym} 2320 -3230 0 0 {name=V8 value="PULSE(0 1.8 0 10p 10p .5u 1u)"
}
C {devices/gnd.sym} 2320 -3180 0 0 {name=l123 lab=GND}
C {devices/lab_pin.sym} 2320 -3310 0 0 {name=l124 sig_type=std_logic lab=ck}
C {devices/vsource.sym} 2510 -3240 0 0 {name=V23 value=0.4}
C {devices/gnd.sym} 2510 -3190 0 0 {name=l125 lab=GND}
C {devices/lab_pin.sym} 2510 -3320 0 0 {name=l126 sig_type=std_logic lab=inn}
C {devices/vsource.sym} 1940 -3000 0 0 {name=V3 value=1.2}
C {devices/gnd.sym} 1940 -2950 0 0 {name=l4 lab=GND}
C {devices/lab_pin.sym} 1940 -3140 2 0 {name=l24 sig_type=std_logic lab=in+}
C {devices/gnd.sym} 1450 -2760 0 0 {name=l156 lab=GND}
C {devices/res.sym} 1450 -2950 0 0 {name=R13
value=60k
footprint=1206
device=resistor
m=1}
C {devices/res.sym} 1450 -2840 0 0 {name=R14
value=120k
footprint=1206
device=resistor
m=1}
C {devices/lab_pin.sym} 1390 -2890 0 0 {name=l100 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1660 -3010 0 1 {name=l101 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 1580 -3010 1 0 {name=V4 value=0}
C {devices/vsource.sym} 1360 -2550 2 0 {name=V2 value=1}
C {devices/gnd.sym} 1360 -2500 0 0 {name=l1 lab=GND}
C {devices/res.sym} 1240 -2580 1 0 {name=R1
value=12.7Meg
footprint=1206
device=resistor
m=1}
C {devices/lab_pin.sym} 1200 -2580 1 0 {name=l6 sig_type=std_logic lab=vx}
C {devices/code_shown.sym} 3250 -2820 0 0 {name=s1 only_toplevel=false value="

.measure tran ipp1 PP i(v6) from=5u to=6u
.measure tran ipp2 PP i(v6) from=20u to=21u
.measure tran ipp3 PP i(v6) from=50u to=51u
.measure tran ipp4 PP i(v6) from=100u to=101u
.measure tran ipp5 PP i(v6) from=170u to=171u
.measure tran ipp6 PP i(v6) from=220u to=221u
.measure tran iavg AVG i(v4) from=1u to=255u
.measure tran ravg AVG zort from=1u to=255u
.end
"
}
C {devices/capa.sym} 1520 -2890 0 0 {name=C3
m=1
value=100p
footprint=1206
device="ceramic capacitor"}
C {devices/lab_pin.sym} 1220 -3090 2 0 {name=l2 sig_type=std_logic lab=vdd3v3}
C {devices/lab_pin.sym} 1220 -3050 2 0 {name=l3 sig_type=std_logic lab=n5}
C {devices/gnd.sym} 1270 -2970 0 0 {name=l7 lab=GND}
C {devices/lab_pin.sym} 1220 -3030 2 0 {name=l8 sig_type=std_logic lab=in+}
C {devices/isource.sym} 1280 -3070 3 0 {name=I2 value=15u}
C {devices/gnd.sym} 1320 -3050 0 0 {name=l9 lab=GND}
C {devices/vsource.sym} 2170 -3250 0 0 {name=V6 value=3.3}
C {devices/gnd.sym} 2170 -3200 0 0 {name=l11 lab=GND}
C {devices/lab_pin.sym} 2170 -3300 0 1 {name=l12 sig_type=std_logic lab=vdd3v3}
C {design/ldo/ldos_wores.sym} 1040 -3040 0 0 {name=x1}
