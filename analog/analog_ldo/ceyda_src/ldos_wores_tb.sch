v {xschem version=3.0.0 file_version=1.2 }
G {}
K {}
V {}
S {}
E {}
N 630 -660 630 -640 {
lab=GND}
N 630 -740 630 -720 {
lab=vdd}
N 420 -380 450 -380 {
lab=vdd3v3}
N 420 -280 440 -280 {
lab=GND}
N 450 -280 450 -260 {
lab=GND}
N 550 -360 550 -340 {
lab=GND}
N 420 -360 480 -360 {
lab=#net1}
N 540 -360 550 -360 {
lab=GND}
N 420 -340 450 -340 {
lab=in-}
N 440 -280 450 -280 {
lab=GND}
N 420 -300 540 -300 {
lab=vout}
N 650 -240 650 -230 {
lab=vout}
N 650 -70 650 -50 {
lab=GND}
N 650 -300 650 -240 {
lab=vout}
N 650 -170 650 -70 {
lab=GND}
N 650 -300 750 -300 {
lab=vout}
N 780 -600 780 -580 {
lab=#net2}
N 780 -520 780 -500 {
lab=GND}
N 780 -670 780 -660 {
lab=in+}
N 780 -680 780 -670 {
lab=in+}
N 780 -750 780 -740 {
lab=in+}
N 780 -740 780 -680 {
lab=in+}
N 720 -300 720 -230 {
lab=vout}
N 720 -170 720 -150 {
lab=#net3}
N 720 -90 720 -70 {
lab=GND}
N 650 -70 720 -70 {
lab=GND}
N 540 -300 650 -300 {
lab=vout}
N 420 -320 450 -320 {
lab=in+}
N 600 -220 600 -170 {
lab=in-}
N 600 -110 600 -80 {
lab=GND}
N 600 -300 600 -280 {
lab=vout}
N 600 -80 600 -70 {
lab=GND}
N 600 -70 650 -70 {
lab=GND}
N 570 -190 600 -190 {
lab=in-}
C {devices/vsource.sym} 630 -690 0 0 {name=V1 value=3.3}
C {devices/gnd.sym} 630 -640 0 0 {name=l1 lab=GND}
C {devices/lab_pin.sym} 630 -740 0 0 {name=l12 sig_type=std_logic lab=vdd3v3}
C {devices/lab_pin.sym} 450 -380 2 0 {name=l4 sig_type=std_logic lab=vdd3v3}
C {devices/gnd.sym} 450 -260 0 0 {name=l6 lab=GND}
C {devices/lab_pin.sym} 450 -340 2 0 {name=l7 sig_type=std_logic lab=in-}
C {devices/isource.sym} 510 -360 3 0 {name=I2 value=15u}
C {devices/gnd.sym} 550 -340 0 0 {name=l8 lab=GND}
C {devices/code.sym} 90 -700 0 0 {name=TT_MODELS
only_toplevel=true
format="tcleval( @value )"
value="
** opencircuitdesign pdks install
.lib $::SKYWATER_MODELS/sky130.lib.spice tt

"
spice_ignore=false}
C {devices/capa.sym} 650 -200 0 0 {name=C1
m=1
value=100p
footprint=1206
device="ceramic capacitor"}
C {devices/gnd.sym} 650 -50 0 0 {name=l17 lab=GND}
C {devices/lab_pin.sym} 750 -300 0 1 {name=l2 sig_type=std_logic lab=vout}
C {devices/vsource.sym} 780 -550 0 0 {name=V4 value=1.2}
C {devices/gnd.sym} 780 -500 0 0 {name=l3 lab=GND}
C {devices/lab_pin.sym} 780 -750 2 0 {name=l5 sig_type=std_logic lab=in+}
C {devices/vsource.sym} 780 -630 0 0 {name=V6 value="AC 1"}
C {devices/code_shown.sym} 940 -770 0 0 {name=s1 only_toplevel=false value="

.include /foss/design/single_slope/netgen/ldos_wores_pex.spice
.option method=Gear 
*.ic v(vout)=1.8 v(n5)=1.2
.control
set color0=white
set units= degrees
*set sqrnoise
save all


tran .1u 20u
*let gmdp= @m.xm14.msky130_fd_pr__pfet_01v8[gm]
plot vb2 vb3
plot vout
plot n1
plot a b c d e f

*reset
*ac dec 100 1 1G
*plot vdb(vout) 
*plot phase(vout) 
*plot vdb(outn)
*plot inp inn out1

*meas ac gbw when vdb(vout)=0
*meas ac gbw_2 when vout=1

*reset
*noise v(vout) V4 dec 100 1 52Meg
*print inoise_total onoise_total
*setplot noise1
*plot inoise_spectrum xlog ylog
*plot onoise_spectrum xlog ylog


show all
.endc
"}
C {devices/vsource.sym} 720 -120 0 0 {name=V7 value=0}
C {devices/isource.sym} 720 -200 0 0 {name=I1 value=1m
*"PULSE(.1m 5m 0 10p 10p 1u 2u)"}
C {design/ldo/ldos_wores.sym} 270 -330 0 0 {name=x1}
C {devices/lab_pin.sym} 450 -320 2 0 {name=l9 sig_type=std_logic lab=in+}
C {devices/res.sym} 600 -250 0 0 {name=R13
value=60k
footprint=1206
device=resistor
m=1}
C {devices/res.sym} 600 -140 0 0 {name=R14
value=120k
footprint=1206
device=resistor
m=1}
C {devices/lab_pin.sym} 570 -190 2 1 {name=l10 sig_type=std_logic lab=in-}
