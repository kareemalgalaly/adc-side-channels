PDK_PROCESS_LIB	?= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice
PDK_CELL_LIB 	?= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs/cells

ANALOG_TARGET   ?= adc_sky
PROCESS_CORNER  ?= tt
DIGITAL_TARGET  ?= control_v0
TOP_MODULE	    ?= control
D_START			?= 0
D_STOP			?= 1
D_COUNT			?= 256

ROOT 	 		= ${PWD}
P_SYNTH	 		= ${ROOT}/synth
P_BUILD	 		= ${ROOT}/build
P_SCRIPT 		= ${ROOT}/script
P_ANALOG 		= ${ROOT}/analog
P_DIGITAL		= ${ROOT}/digital
P_DESIGN 		= ${P_DIGITAL}/design

TOP_ANALOG_CIR  = ${P_ANALOG}/${ANALOG_TARGET}/${ANALOG_TARGET}.cir
TOP_VERILOG_SRC = ${P_DESIGN}/top/${DIGITAL_TARGET}.v
TOP_SYNTH 		= ${P_SYNTH}/${DIGITAL_TARGET}/${DIGITAL_TARGET}

SIM_SO_OBJ 	  	= $(addsuffix .so, $(addprefix ${P_BUILD}/, $(DIGITAL_TARGETS)))


${TOP_SYNTH}.v ${TOP_SYNTH}.json: ${TOP_VERILOG_SRC}
	mkdir -p ${P_SYNTH}/${DIGITAL_TARGET}
	SYNTH_VERILOG=${TOP_VERILOG_SRC} SYNTH_TARGET=${TOP_SYNTH} SYNTH_MODULE=${TOP_MODULE} yosys -c ${P_SCRIPT}/synth.tcl

${TOP_SYNTH}.spice: ${TOP_SYNTH}.v ${TOP_SYNTH}.json
	python ${P_SCRIPT}/json2spice.py ${TOP_SYNTH}.json ${PDK_CELL_LIB} ${TOP_MODULE} ${TOP_SYNTH}.spice

digital-synth: ${TOP_SYNTH}.spice

spice-sim-old: ${TOP_ANALOG_CIR}
	cd ${P_ANALOG}/${ANALOG_TARGET} && ngspice ${ANALOG_TARGET}.cir

spice-sim:
	cd ${P_ANALOG}/${ANALOG_TARGET} && bash -c "ngspice <(python ${P_SCRIPT}/template_engine.py ${ANALOG_TARGET}_temp.cir -t corner=${PROCESS_CORNER} start=${D_START} stop=${D_STOP} count=${D_COUNT} isplot=';' islin= 'iswrite=' 'isbatch=')"

spice-plot:
	#cd ${P_ANALOG}/${ANALOG_TARGET} && bash -c "ngspice <(python ${P_SCRIPT}/template_engine.py ${ANALOG_TARGET}_temp.cir -t corner=${PROCESS_CORNER} start=${D_START} stop=${D_STOP} count=1 isplot= islin= 'iswrite=;' 'isbatch=;')"
	cd ${P_ANALOG}/${ANALOG_TARGET} && bash -c "vim     <(python ${P_SCRIPT}/template_engine.py ${ANALOG_TARGET}_temp.cir -t corner=${PROCESS_CORNER} start=${D_START} stop=${D_STOP} count=1 isplot= islin= 'iswrite=;' 'isbatch=;')"

${P_BUILD}/${DIGITAL_TARGET}.so: ${TOP_VERILOG_SRC}.v
	cd ${P_BUILD} && ngspice vlnggen -- --CFLAGS -DVL_TIME_STAMP64 --CFLAGS -DVL_NO_LEGACY ${TOP_VERILOG_SRC}.v

# Digital Synthesis
synth/%: ${P_DESIGN}/top/%.v
	mkdir $@
	SYNTH_VERILOG=${P_DESIGN}/top/$*.v SYNTH_TARGET=$@/${TOP_MODULE} SYNTH_MODULE=${TOP_MODULE} yosys -c ${P_SCRIPT}/synth.tcl
	python ${P_SCRIPT}/json2spice.py $@/${TOP_MODULE}.json ${PDK_CELL_LIB} ${TOP_MODULE} $@/${TOP_MODULE}.spice

#$(SIM_TARGETS): %.cosim: ${BUILD}/%.so
cosim/%: ${P_BUILD}/%.so
	cp ${P_BUILD}/$*.so ${P_BUILD}/adc.so
	cd ${P_ANALOG}/${ANALOG_TARGET}/ && ngspice ${ANALOG_TARGET}.cir

$(SIM_SO_OBJ): ${P_BUILD}/%.so:
	ngspice vlnggen -- --CFLAGS -DVL_TIME_STAMP64 --CFLAGS -DVL_NO_LEGACY ${P_DESIGN}/top/$*.v
	mv $*.so ${P_BUILD}/$*.so
	rm -rf $*_obj_dir

clean:
	rm -rf ${P_SYNTH}/*
	rm -rf ${P_BUILD}/*
