PDK_PROCESS_LIB	= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice
PDK_CELL_LIB 	= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs/cells
PROCESS_CORNER  = tt
DIGITAL_TARGETS = control_v0 test
MODULE = control

ANALOG_TARGET  ?= adc

ROOT=${PWD}
SYNTH=${ROOT}/synth
BUILD=${ROOT}/build
SCRIPT=${ROOT}/script
ANALOG=${ROOT}/analog
DIGITAL=${ROOT}/digital
DESIGN=${DIGITAL}/design


#SYNTH_TARGETS = $(addsuffix .synth, $(DIGITAL_TARGETS))
#SIM_TARGETS	  = $(addsuffix .cosim, $(DIGITAL_TARGETS))
SIM_SO_OBJ 	  = $(addsuffix .so, $(addprefix ${BUILD}/, $(DIGITAL_TARGETS)))

# Digital Synthesis
synth/%: ${DESIGN}/top/%.v
	mkdir $@
	SYNTH_VERILOG=${DESIGN}/top/$*.v SYNTH_TARGET=$@/${MODULE} yosys -c ${SCRIPT}/synth.tcl
	python script/json2spice.py $@/${MODULE}.json ${PDK_CELL_LIB} ${MODULE} $@/${MODULE}.spice

#$(SIM_TARGETS): %.cosim: ${BUILD}/%.so
cosim/%: ${BUILD}/%.so
	cp ${BUILD}/$*.so ${BUILD}/adc.so
	cd ${ANALOG}/${ANALOG_TARGET}/ && ngspice ${ANALOG_TARGET}.cir

$(SIM_SO_OBJ): ${BUILD}/%.so:
	ngspice vlnggen -- --CFLAGS -DVL_TIME_STAMP64 --CFLAGS -DVL_NO_LEGACY ${DESIGN}/top/$*.v
	mv $*.so ${BUILD}/$*.so
	rm -rf $*_obj_dir

clean:
	rm -rf ${SYNTH}/*
	rm -rf ${BUILD}/*
