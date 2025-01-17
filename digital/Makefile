DESIGN_FILES = design/counters/counter.v
TESTBENCH_FILES = tb/tb_lib.v tb/counter_tb.v
IGNORED_WARNINGS = WIDTHEXPAND WIDTHTRUNC

SUPPRESS_WARNINGS = $(addprefix -Wno-, $(IGNORED_WARNINGS))

#counter:
#	iverilog -s counter -o build/count_tb ${DESIGN_FILES} ${TESTBENCH_FILES}
#	vvp build/count_tb

counter:
	verilator --binary tb/counter_tb.v tb/tb_lib.v design/counters/* --top-module 'counter_tb' --timing -Itb ${SUPPRESS_WARNINGS} --trace
	./obj_dir/Vcounter_tb

sampler:
	verilator --binary tb/sampler_tb.v tb/tb_lib.v design/counters/* --top-module 'sampler_tb' --timing -Itb ${SUPPRESS_WARNINGS} --trace 
	./obj_dir/Vsampler_tb +verilator+error+limit+10

