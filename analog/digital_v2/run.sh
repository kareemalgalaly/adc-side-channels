#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

interactive=""
dvalue="[30]"
pixels=1
seed=""
corner="tt"
numsim=1
norun=""
debug=""
version="v3"

while getopts "id:p:s:c:n:v:NQ:" opt
do
    case "$opt" in 
        i ) interactive="interactive="  ;;
        d ) dvalue="eval:${OPTARG}"     ;;
        p ) pixels="${OPTARG}"          ;;
        s ) seed="${OPTARG}"            ;;
        c ) corner="${OPTARG}"          ;;
        n ) numsim="${OPTARG}"          ;;
        v ) version="${OPTARG}"         ;;
        N ) norun=1                     ;;
        Q ) queue="${OPTARG}"           ;;
    esac
done

# Environment Variable Defaults

if [ "$PYTHON" = "" ]; then PYTHON="python3"; fi
TENG="$PYTHON ../../script/teng.py"
SPGEN="$TENG -g template_batch.cir pixels=eval:$pixels corner=$corner version=$version counter_header= $interactive"

# Main

if [ "$version" = "ece" ]; then
    if ! [ $queue ]; then queue=1; fi

    echo "#!/bin/bash" > jobs.sh
    for i in $(seq $queue); do
        echo "ngspice <(python3 ../../script/teng.py -g template_ece_randprot.cir corner=$corner start=$((numsim*(i-1)/queue+seed)) stop=$((numsim*i/queue+seed)) stdc=hs)" >> jobs.sh
    done

    if [ "$norun" = "" ]; then
        if [ "$queue" != 1 ]; then
            echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
            cat jobs.sh | xargs -I cmd -P $queue bash -c "echo '> cmd'; eval 'cmd'"
        else
            bash jobs.sh
        fi
    fi

elif [ "$pixels" = 1 ]; then

    if [ "$queue" != "" ]; then
        echo "#!/bin/bash" > jobs.sh
        echo "#!/bin/bash" > jobs_post.sh
    fi

    if [ "$norun" = "" ] || [ "$queue" ]; then
        outdir=outfiles/${version}_${corner}
        mkdir -p $outdir
    fi

    # local s value
    for i in $(seq $numsim); do
        if [ "$seed" != "" ]; then
            s=$((seed + i - 1))
            if [ "$pixels" = 1 ] && (( $s < 256 )); then
                value="dvals=eval:[$s]"
            else
                value="seed=eval:$s"
            fi
        else
            value="dvals='$dvalue'"
            s="d$(echo $dvalue | tr -d '[\[ \]]')"
        fi

        if [ "$norun" ] && [ "$queue" = "" ]; then
            eval $SPGEN $value
        else
            if [ "$interactive" ]; then
                ngspice <($SPGEN $value)
            else
                if [ "$queue" ]; then
                    echo "ngspice -b -r $outdir/rawfile_${s} <($SPGEN $value)" >> jobs.sh
                    echo "ngspice <($TENG template_batch_post.cir rawfile=$outdir/rawfile_${s} outfile=$outdir/trace_${s})" >> jobs_post.sh
                else
                    ngspice -b -r rawfile_${s} <($SPGEN $value)
                    ngspice <($TENG template_batch_post.cir rawfile=rawfile_${s} outfile=$outdir/trace_$s)
                fi
            fi
        fi
    done

    if [ "$queue" ]; then
        echo "Generated jobs.sh, jobs_post.sh"
        if [ "$norun" = "" ]; then
            echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
            cat jobs.sh      | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
            echo "Simulations completed, extracting trace data"
            cat jobs_post.sh | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
            echo "Done"
        fi
    fi
else
    if [ "$seed" = "" ]; then seed=0; fi
    if [ "$interactive" != "" ]; then interactive="-i"; fi

    mkdir -p "outfiles/${version}_${corner}_${pixels}"
    python3 gen.py -p $pixels -c $corner -n $numsim -s $seed -v $version $interactive > jobs.sh
    echo "Generated jobs.sh"


    if [ "$norun" = "" ]; then
        if [ "$queue" ]; then
            echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
            cat jobs.sh      | xargs -I cmd -P $queue bash -c "echo '> cmd'; eval 'cmd'"
        else
            bash jobs.sh
        fi
    fi
fi

