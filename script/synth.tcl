yosys echo on

puts "Hello yosys"

# read liberty files
yosys read_liberty -lib ~/Lib/skywater-pdk/libraries/sky130_fd_sc_hs/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib 

# read design
yosys read_verilog -sv $::env(SYNTH_VERILOG)

# elaborate design hierarchy
#hierarchy -check -top control

# synthesize top level module
yosys synth -top control

# mapping flip-flops to mycells.lib
yosys dfflibmap -liberty ~/Lib/skywater-pdk/libraries/sky130_fd_sc_hs/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib
#yosys dfflibmap -liberty ~/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs/timing/sky130_fd_sc_hs__tt_025C_1v50.lib

# mapping logic to mycells.lib
yosys abc -liberty ~/Lib/skywater-pdk/libraries/sky130_fd_sc_hs/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib
#yosys abc -liberty ~/Lib/efabless/skywater-pdk-libs-sky130_fd_sc_hs/timing/sky130_fd_sc_hs__tt_025C_1v50.lib

yosys flatten
yosys clean

# write synthesized design
yosys write_verilog -noattr $::env(SYNTH_TARGET).v
yosys write_json $::env(SYNTH_TARGET).json
#yosys write_spice $::env(SYNTH_TARGET).spice

#yosys show
