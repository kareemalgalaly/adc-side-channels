#!/bin/bash

D1=analog/ece_1px
D2=analog/digital_v2
D1LIB=$D1/lib
D2LIB=$D2/lib

measure() {
    cat $1 | grep '^x.*' | grep -oP 'sky130_fd_sc_hs\w+' | python script/area_calc.py $PDK_CELL_LIB 
}

measure2() {
    cat $1 | grep '^x.*' | grep -oP 'sky130_fd_sc_hs\w+' | python script/area_calc.py -m $PDK_CELL_LIB
}


between() {
    start=$1
    stop=$2
    file=$3
    cat $file | awk -v start="$start" -v stop="$stop" 'BEGIN {disp=0} $0~start {disp=2} $0~stop {disp=0} $0 {if (disp>1) {disp=1} else if (disp) print($0)}'
}

echo "--------------------------------------------------"
echo "-- Digital Components                           --"
echo "--------------------------------------------------"

#counter_half=$(measure2 $D2LIB/counter_half.spice)
between 'lib synth$' 'endl synth$' $D2LIB/counter_half.spice
counter_half=$(measure2 <(between 'lib synth$' 'endl synth$' $D2LIB/counter_half.spice))
echo -e "\ncounter_half        $counter_half"

neg_samp_1=$(measure2 $D1LIB/negedge_detector.spice )
echo -e "\nnegedge_detector v1 $neg_samp_1"

neg_samp_2=$(measure2 $D2LIB/negedge_detector.spice )
echo -e "\nnegedge_detector v2 $neg_samp_2"

reg_array=$(measure2 $D2LIB/register_array.spice )
echo -e "\nregister_array      $reg_array"

double_samp=$(measure2 $D2LIB/double_rate_sampler_v3.spice )
echo -e "\ndouble_rate_sampler $double_samp"

echo
echo "--------------------------------------------------"
echo "-- Digital Systems                              --"
echo "--------------------------------------------------"
echo

sys_d_unprot_c=$(measure2 $D1/runme_1px_ss_x_0.cir)
sys_d_unprot=$(bc <<< "$sys_d_unprot_c + $counter_half + $reg_array + $neg_samp_2" )
echo -e "digital unprotected $sys_d_unprot\t 1 counter 1 reg_array  1 negedge detector"

sys_d_prot1f_c=$(measure2 $D1/runme_1px_ss_p_0.cir)
sys_d_prot1f=$(bc <<< "$sys_d_prot1f_c + $counter_half + 2*$reg_array + 2*$neg_samp_2")
echo -e "digital failed mask $sys_d_prot1f\t 1 counter 2 reg_array 2 negedge_detector"

sys_d_randprot_c=$(measure2 $D2/ece_runme_1px_ff_q_0.cir)
sys_d_randprot=$(bc <<< "$sys_d_randprot_c + $counter_half + 4*$reg_array + 4*$neg_samp_2")
echo -e "digital random prot $sys_d_randprot\t 1 counter 4 reg_array 4 negedge_detector"

sys_d_maskprot_c=$(measure2 $D2/template.cir)
sys_d_maskprot=$(bc <<< "$sys_d_maskprot_c + $counter_half + $double_samp")
echo -e "digital masked prot $sys_d_maskprot\t 1 counter 1 double_rate_sampler"

echo -e "\nMultipixel\n"

sys_d_unprot_sc=$(measure2 <(between 'Singleton' 'Pixel' $D1/runme_1px_ss_x_0.cir))
sys_d_unprot_pc=$(measure2 <(between 'Pixel' 'Control' $D1/runme_1px_ss_x_0.cir))
sys_d_unprot_50=$(bc <<< "$sys_d_unprot_sc + 50*$sys_d_unprot_pc + $counter_half + 50*$reg_array + 50*$neg_samp_2")
echo "digital unprotected @50 $sys_d_unprot_50"

sys_d_prot1f_sc=$(measure2 <(between 'Singleton' 'Pixel' $D1/runme_1px_ss_p_0.cir))
sys_d_prot1f_pc=$(measure2 <(between 'Pixel' 'Control' $D1/runme_1px_ss_p_0.cir))
sys_d_prot1f_50=$(bc <<< "$sys_d_prot1f_sc + 50*$sys_d_prot1f_pc + $counter_half + 100*$reg_array + 100*$neg_samp_2")
echo "digital failed mask @50 $sys_d_prot1f_50"

sys_d_randprot_sc=$(measure2 <(between 'Singleton' 'Pixel' $D2/ece_runme_1px_ff_q_0.cir))
sys_d_randprot_pc=$(measure2 <(between 'Pixel' 'Control' $D2/ece_runme_1px_ff_q_0.cir))
# echo $sys_d_randprot_sc + $sys_d_randprot_pc = $sys_d_randprot_c
sys_d_randprot_50=$(bc <<< "$sys_d_randprot_sc + 50*$sys_d_randprot_pc + $counter_half + 200*$reg_array + 200*$neg_samp_2")
echo "digital random prot @50 $sys_d_randprot_50"

sys_d_maskprot_50=$(bc <<< "$sys_d_maskprot_c + $counter_half + 50*$double_samp")
echo "digital masked prot @50 $sys_d_maskprot_50"

echo
echo "--------------------------------------------------"
echo "-- Analog Components                            --"
echo "--------------------------------------------------"
echo

# ramp_gen=$(measure2 <(between 

echo "--------------------------------------------------"
echo "-- Analog Systems                               --"
echo "--------------------------------------------------"

