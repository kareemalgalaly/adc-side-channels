# Build seeds

if [ "$1" = "clean" ]; then
    echo "Cleaning files"
    rm -f seeds_*
    rm -f demo_*.cir
    rm -f runme_*.cir
    rm -f *.cir_err
    shift 1
    [ "$1" = "" ] && exit 0
fi

if [ "$1" = "1px" ]; then
    pixels="1px"
    corners=( tt ) # ss ff sf fs 
    flavors=( xx px xm pm )
    seeds=(0)
    parg="pixels=eval:1"
elif [ "$1" = "1qx" ]; then
    pixels="1px"
    corners=( tt ) # ss ff sf fs 
    flavors=( qx )
    seeds=(0 256)
    parg="pixels=eval:1"
elif [ "$1" = "5px" ]; then
    pixels="5px"
    corners=( tt ) # ss ff sf fs 
    flavors=( xx px xm pm qx qm)
    seeds=(0 128 256 384)
    parg="pixels=eval:5"
elif [ "$1" = "run" ]; then
    for file in $(ls runme*cir); do echo ngspice $file; ngspice $file; done
    exit 0
else
    echo "Unsupported argument <$1>"
    exit 1
fi
shift 1

for seed in ${seeds[@]}; do
    [ -f seeds_$seed ]    || python ../../script/gen_seeds.py -s 0 -p 5 -i 1 -r 1           -n 128                 --start $seed > seeds_$seed
    [ -f seeds_rr_$seed ] || python ../../script/gen_seeds.py -s 0 -p 5 -i 0 -r 1.8 -t 2 -d -n 256 --prefix randvc --start $seed > seeds_rr_$seed
done

if [ -f /foss/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice ]; then
    foss="foss="
else
    foss=""
fi


for flavor in ${flavors[@]}; do
    case $flavor in 
        xx ) flv=""                               ;;
        px ) flv="protected="                     ;;
        xm ) flv="mismatch="                      ;;
        pm ) flv="protected= mismatch="           ;;
        qx ) flv="protected= randramp="           ;;
        qm ) flv="protected= randramp= mismatch=" ;;
        *  ) echo "nomatch <$flavor>"
    esac

    args=("randvec_1=compose randvec_1 values 0.1 1.0 0.6" "randvec_2=compose randvec_2 values 0.3 0.0 0.6" "randvec_3=compose randvec_3 values 0.5 0.2 0.6" "randvec_4=compose randvec_4 values 0.7 0.8 0.6" "randvec_5=compose randvec_5 values 0.9 0.4 0.6" "randvc0=compose randvc0 values 0 1.8 0" "randvc1=compose randvc1 values 1.8 0 1.8" "randvc2=compose randvc2 values 0 1.8 1.8" "randvc3=compose randvc3 values 0 0 0" "randvc4=compose randvc4 values 0 1.8 0" "seed=0")

    echo Building demo_${pixels}_${corners[0]}_${flavor}_${seeds[0]}.cir
    python ../../script/template_engine.py adc_sky_5px.temp.cir -s plot= $flv "${args[@]}" $parg -o demo_${pixels}_${corners[0]}_${flavor}_${seeds[0]}.cir
    echo

    for corner in ${corners[@]}; do
        for seed in ${seeds[@]}; do
            args=()
            if [ "$pixels" = 1px ]; then
                args+=("randvec_1=eval:'compose randvec_1 values '+' '.join(str(i/256) for i in range(256))")
                while read -r i ; do 
                    args+=("$i")
                done < seeds_rr_$seed
            else
                while read -r i ; do 
                    args+=("$i")
                done < seeds_$seed
                while read -r i ; do 
                    args+=("$i")
                done < seeds_rr_$seed
            fi
            args+=("corner=$corner")
            args+=("outdir=outfiles/analog_${pixels}_${corner}_${flavor}")
            args+=("seed=$seed")
            args+=("$foss")
            args+=("$parg")

            echo Building runme_${pixels}_${corner}_${flavor}_${seed}.cir
            python ../../script/template_engine.py adc_sky_5px.temp.cir -s "${args[@]}" $flv -o runme_${pixels}_${corner}_${flavor}_${seed}.cir
            echo
        done
    done
done

if [ "$1" = run ]; then
    for file in $(ls runme*cir); do echo ngspice $file; ngspice $file; done
fi
