# Build seeds

seeds=(0 128 256 384)
corners=( tt ) # ss ff sf fs 
flavors=( xx px xm pm )

for seed in ${seeds[@]}; do
    [ -f seeds_$seed ] || python ../../script/gen_seeds.py -s 0 -p 5 -i 1 -r 1 -n 128 --start $seed > seeds_$seed
done

for flavor in ${flavors[@]}; do
    case flavor in 
        xx ) flv="" ;;
        px ) flv="protected=" ;;
        xm ) flv="mismatch=" ;;
        pm ) flv="protected= mismatch=" ;;
    esac

    args=("randvec_1=compose randvec_1 values 0.1 1.0 0.6" "randvec_2=compose randvec_2 values 0.3 0.0 0.6" "randvec_3=compose randvec_3 values 0.5 0.2 0.6" "randvec_4=compose randvec_4 values 0.7 0.8 0.6" "randvec_5=compose randvec_5 values 0.9 0.4 0.6")
    python ../../script/template_engine.py adc_sky_5px.temp.cir -s plot= "${args[@]}" -o demo_5px_${corners[0]}_${flavor}_${seeds[0]}.cir

    for corner in ${corners[@]}; do
        for seed in ${seeds[@]}; do
            args=()
            while read -r i ; do 
                args+=("$i")
            done < seeds_$seed
            args+=("corner=$corner")
            args+=("outdir=outfiles/analog_5px_${corner}_${flavor}")
            args+=("$flv")
            args+=("seed=$seed")

            python ../../script/template_engine.py adc_sky_5px.temp.cir -s "${args[@]}" -o runme_5px_${corner}_${flavor}_${seed}.cir
        done
    done
done
