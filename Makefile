PDK_PROCESS_LIB	= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice
PDK_CELL_LIB 	= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs
PROCESS_CORNER  = tt
DIGITAL_MODULES = control_v0


ROOT=${PWD}
SYNTH=${ROOT}/synth
BUILD=${ROOT}/build
SCRIPT=${ROOT}/script
ANALOG=${ROOT}/analog
DIGITAL=${ROOT}/digital
DESIGN=${DIGITAL}/design


SYNTH_TARGETS = $(addsuffix .synth, $(DIGITAL_MODULES))
SIM_TARGETS	  = $(addsuffix .adcsim, $(DIGITAL_MODULES))
SIM_SO_OBJ 	  = $(addsuffix .so, $(addprefix ${BUILD}/, $(DIGITAL_MODULES)))

#$(SYNTH_TARGETS): %.synth: ${SYNTH}/%.v:
$(SYNTH_TARGETS): %.synth: ${DESIGN}/top/%.v
	SYNTH_VERILOG=${DESIGN}/top/$*.v SYNTH_TARGET=${SYNTH}/$* yosys -c ${SCRIPT}/synth.tcl
	python script/synth_post.py ${SYNTH}/$*.spice ${SYNTH}/$*.v ${PDK_PROCESS_LIB} ${PROCESS_CORNER} ${PDK_CELL_LIB} ${SYNTH}/$*_wrap.spice

$(SIM_TARGETS): %.adcsim: ${BUILD}/%.so
	cp ${BUILD}/$*.so ${BUILD}/adc.so
	cd ${ANALOG}/adc/ && ngspice adc.cir

$(SIM_SO_OBJ): ${BUILD}/%.so:
	ngspice vlnggen -- --CFLAGS -DVL_TIME_STAMP64 --CFLAGS -DVL_NO_LEGACY ${DESIGN}/top/$*.v
	mv $*.so ${BUILD}/$*.so
	rm -rf $*_obj_dir

clean:
	rm ${SYNTH}/*
	rm ${BUILD}/*
