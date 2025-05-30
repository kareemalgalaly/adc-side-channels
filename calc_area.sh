D1=analog/ece_1px
D2=analog/digital_v2
D1LIB=$D1/lib
D2LIB=$D2/lib

measure() {
    cat $1 | grep '^x.*' | grep -oP 'sky130_fd_sc_hs\w+' | python script/area_calc.py $PDK_CELL_LIB 
}

measure2() {
    cat $1 | grep '^x.*' | grep -oP 'sky130_fd_sc_hs\w+' | python script/area_calc.py $PDK_CELL_LIB -m
}

alias do_measure=measure2

echo -e "\ncounter_half"
measure $D2LIB/counter_half.spice

echo -e "\ndouble_rate_sampler"
measure $D2LIB/double_rate_sampler_v3.spice

echo -e "\nnegedge_detector v1"
measure $D1LIB/negedge_detector.spice

echo -e "\nnegedge_detector v2"
measure $D2LIB/negedge_detector.spice

echo -e "\nregister_array"
measure $D2LIB/register_array.spice

echo -e "\nunprot (1 counter 1 reg_array + 1 negedge detector)"
measure $D1/runme_1px_ss_x_0.cir

echo -e "\nprot v1 (1 counter 2 reg_array 2 negedge_detector)"
measure $D1/runme_1px_ss_p_0.cir

echo -e "\nrandprot (1 counter 4 reg_array 4 negedge_detector)"
measure $D2/ece_runme_1px_ff_q_0.cir

echo -e "\nprot3 (1 counter 1 double_rate_sampler_v3)"
measure $D2/template.cir
