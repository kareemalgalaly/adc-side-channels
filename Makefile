PDK_PROCESS_LIB	?= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice
PDK_CELL_LIB 	?= /Users/kareemahmad/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs/cells
PDK_LIBERTY     ?= /Users/kareemahmad/Lib/skywater-pdk/libraries/sky130_fd_sc_hs/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib

PROJ_ROOT 		= ${PWD}

# Synthesis ---------------------------------------------

synth/%: ${PROJ_ROOT}/digital/design/%.v ${PROJ_ROOT}/script/synth.tcl
	mkdir -p $@
	SYNTH_VERILOG=${PROJ_ROOT}/digital/design/$*.v SYNTH_PATH=$@ PDK_LIBERTY=${PDK_LIBERTY} PDK_CELL=${PDK_CELL_LIB} yosys -c ${PROJ_ROOT}/script/synth.tcl

# Area Calculation --------------------------------------

area:
	PDK_CELL_LIB=${PDK_CELL_LIB} ${PROJ_ROOT}/script/calc_area.sh
