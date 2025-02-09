# Build seeds

if [ "$1" = "clean" ]; then
    rm demo_*.cir runme_*.cir seeds_*
    exit 0
fi

if [ "$1" = "1px" ]; then
    pixels="1px"
    corners=( tt ss ff sf fs )
    seeds=(0)
    args="pixels=eval:1"
else
    pixels="5px"
    corners=( sf ss ff fs )
    seeds=(0 128 256 384)
    args="pixels=eval:5"
fi

args="$args halfcounter="

if [ -f /foss/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice ]; then
    args="$args foss="
fi

python ../../script/template_engine.py digital.temp.cir -s $args plot= seed=0            -o demo_${pixels}_tt_x.cir
python ../../script/template_engine.py digital.temp.cir -s $args plot= seed=0 protected= -o demo_${pixels}_tt_p.cir

if [ "$pixels" = "1px" ]; then
    values=("randvec_1=eval:'compose randvec_1 values '+' '.join(str(i) for i in range(256))")
else
    for seed in ${seeds[@]}; do
        [ -f seeds_$seed ] || python ../../script/gen_seeds.py -s 0 -p 5 -i 1 -r 256 -n 128 --start $seed > seeds_$seed
    done
fi

outdir=outfiles/digital_5px_${corner}_x
for seed in ${seeds[@]}; do
    if [ "$pixels" = "5px" ]; then
        values=()
        while read -r i ; do 
            echo $i
            values+=("$i")
        done < seeds_$seed
    fi

    for corner in ${corners[@]}; do
        python ../../script/template_engine.py digital.temp.cir -s $args "${values[@]}" seed=$seed outdir=outfiles/digital_${pixels}_${corner}_x            -o runme_${pixels}_${corner}_x_${seed}.cir
        python ../../script/template_engine.py digital.temp.cir -s $args "${values[@]}" seed=$seed outdir=outfiles/digital_${pixels}_${corner}_p protected= -o runme_${pixels}_${corner}_p_${seed}.cir
    done
done

