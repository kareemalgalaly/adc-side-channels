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
yosys read_liberty -lib $::env(PDK_LIBERTY)

# read design
yosys read_verilog -sv $::env(SYNTH_VERILOG)

# elaborate design hierarchy
yosys hierarchy -check -top $SYNTH_MODULE

# synthesize top level module
yosys synth -top $SYNTH_MODULE

# mapping flip-flops to mycells.lib
yosys dfflibmap -liberty $::env(PDK_LIBERTY)

# mapping logic to mycells.lib
yosys abc -liberty $::env(PDK_LIBERTY) -dont_use sky130_fd_sc_hs__clkinv_1

yosys flatten
yosys clean

# write synthesized design
yosys write_verilog -noattr $SYNTH_TARGET.v
yosys write_json $SYNTH_TARGET.json
#yosys show -prefix $SYNTH_TARGET

#yosys show
exec python script/json2spice.py $SYNTH_TARGET.json $::env(PDK_CELL) $SYNTH_MODULE $SYNTH_TARGET.spice | tee /dev/tty
