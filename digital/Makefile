DESIGN_FILES = design/counters/counter.v
TESTBENCH_FILES = tb/tb_lib.v tb/counter_tb.v

counter:
	iverilog -s counter -o build/count_tb ${DESIGN_FILES} ${TESTBENCH_FILES}
	vvp build/count_tb

counter2:
	verilator --binary tb/counter_tb.v tb/tb_lib.v design/counters/* --top-module 'counter_tb' --timing -Itb -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC --trace
	./obj_dir/Vcounter_tb

