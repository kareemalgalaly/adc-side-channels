if {[info exists ::env(SYNTH_PATH)]} {
    puts "PATH EXISTS"
    regexp {.*/(\w+)} $::env(SYNTH_PATH) -> SYNTH_MODULE
    set SYNTH_TARGET "$::env(SYNTH_PATH)/$SYNTH_MODULE"
} else {
    puts "PATH NO EXISTS"
    set SYNTH_TARGET = "$::env(SYNTH_TARGET)"
    set SYNTH_MODULE = "$::env(SYNTH_MODULE)"
}

puts "Target: $SYNTH_TARGET"
puts "Module: $SYNTH_MODULE"

yosys echo on

# read liberty files
yosys read_liberty -lib ~/Lib/skywater-pdk/libraries/sky130_fd_sc_hs/latest/timing/sky130_fd_sc_hs__tt_025C_1v50.lib 

# read design
yosys read_verilog -sv $::env(SYNTH_VERILOG)

# elaborate design hierarchy
yosys hierarchy -check -top $SYNTH_MODULE

# synthesize top level module
yosys synth -top $SYNTH_MODULE

# mapping flip-flops to mycells.lib
yosys dfflibmap -liberty $::env(PDK_LIBERTY)

# mapping logic to mycells.lib
yosys abc -liberty $::env(PDK_LIBERTY)

yosys flatten
yosys clean

# write synthesized design
yosys write_verilog -noattr $SYNTH_TARGET.v
yosys write_json $SYNTH_TARGET.json

#yosys show
exec python script/json2spice.py $SYNTH_TARGET.json $::env(PDK_CELL) $SYNTH_MODULE $SYNTH_TARGET.spice | tee /dev/tty
