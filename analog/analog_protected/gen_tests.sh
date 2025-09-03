#!/usr/bin/env bash

if [ "$1" = "clean" ]; then
    echo "Cleaning files"
    rm -f seeds_*
    rm -f demo_*.cir
    rm -f runme_*.cir
    rm -f *.cir_err
    shift 1
    [ "$1" = "" ] && exit 0
fi

pixels=( 1 )
flavors=( x )

# tt sf ss
# 0 128 256 tt 384 512 l 1024 1152 <1280 1408>

nseed=128

case $1 in
    tt1 ) corners=( tt ) ; seeds=$(seq 0    $nseed  896 ) ;;
    tt2 ) corners=( tt ) ; seeds=$(seq 1024 $nseed 1920 ) ;;
    ttl ) corners=( tt ) ; seeds=$(seq 1280 $nseed 1920 ) ; flavors=( l ) ;;
    ss  ) corners=( ss ) ; seeds=$(seq 1024 $nseed 1920 ) ;;
    sf  ) corners=( sf ) ; seeds=$(seq 1024 $nseed 1920 ) ;;
esac


for seed in ${seeds[@]}; do
    if [ "$seed" = "0" ]; then 
        [ -f seeds_$seed ] || python -c "print('randpx0=compose randpx0 values '+' '.join(str(i/256) for i in range(128)))"      > seeds_$seed

    elif [ "$seed" = "128" ]; then
        [ -f seeds_$seed ] || python -c "print('randpx0=compose randpx0 values '+' '.join(str(i/256) for i in range(128, 256)))" > seeds_$seed

    else
        [ -f seeds_$seed ] || python ../../script/gen_seeds.py -s $seed -p 5 -i 0 -r 1           -n $nseed       --prefix randpx > seeds_$seed
    fi

    [ -f seeds_rr_$seed ]  || python ../../script/gen_seeds.py -s $seed -p 5 -i 0 -r 1.8 -t 2 -d -n $((nseed*4)) --prefix randvc > seeds_rr_$seed
done

if [ -f /foss/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice ]; then
    foss="foss="
else
    foss=""
fi

for flavor in ${flavors[@]}; do
    case $flavor in 
        x ) flv=""        ;;
        l ) flv="layout=" ;;
        *  ) echo "nomatch <$flavor>"
    esac

    for pixel in ${pixels[@]}; do
        pxl="pixels=eval:$pixel"

        echo Building demo_${pixel}_tt_${flavor}.cir
        python ../../script/template_engine.py analog.temp.cir -s $flv $pxl $foss seed=0 plot= -o demo_${pixel}_tt_${flavor}.cir
        echo

        for corner in ${corners[@]}; do
            for seed in ${seeds[@]}; do

                args=( $flv $pxl $foss seed=$seed corner=$corner "outdir=outfiles/analog_${pixel}_${corner}_${flavor}" )
                while read -r i ; do 
                    args+=("$i")
                done < seeds_$seed
                while read -r i ; do 
                    args+=("$i")
                done < seeds_rr_$seed

                echo Building runme_${pixel}_${corner}_${flavor}_${seed}.cir
                python ../../script/template_engine.py analog.temp.cir -s "${args[@]}" -o runme_${pixel}_${corner}_${flavor}_${seed}.cir
                echo

            done
        done
    done
done
