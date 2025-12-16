#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

dval=""
seed=0
corner="tt"
numsim=1
queue=1
interactive=""
norun=""
pixels=1
version="arch2"

while getopts "d:s:n:q:iN" opt
do
    case "$opt" in 
        d ) dval="${OPTARG}"    ;;
        s ) seed="${OPTARG}"    ;;
        n ) numsim="${OPTARG}"  ;;
        q ) queue="${OPTARG}"   ;;
        i ) interactive=1       ;;
        N ) norun=1             ;;
    esac
done

if ! [ "$dval" ]; then
    dval=$((seed % 256))
fi

shift $((OPTIND - 1))

# Environment Variable Defaults

if [ "$PYTHON" = "" ]; then PYTHON="python3"; fi
TENG="$PYTHON ../../script/teng.py"
SPGEN="$TENG template_batch.cir $@"

# Main

if [ "$pixels" = 1 ]; then

    outdir=outfiles/${version}_${corner}
    echo "#!/bin/bash" > jobs.sh
    echo "#!/bin/bash" > jobs_post.sh
    mkdir -p $outdir

    for i in $(seq $numsim); do
        s=$((seed + i - 1))
        d=$((dval + i - 1))

        if [ "$interactive" ]; then
            ngspice <($SPGEN "dvals=eval:[$d]" "seed=$s" "interactive=")
        else
            echo "ngspice -b -r $outdir/rawfile_${d}_${s} <($SPGEN 'dvals=eval:[$d]' 'seed=$s')" >> jobs.sh
            echo "ngspice <($TENG template_batch_post.cir rawfile=$outdir/rawfile_${d}_${s} outfile=$outdir/trace_${s})" >> jobs_post.sh
        fi
    done

    if ! [ "$interactive" ]; then
        echo "Generated jobs.sh, jobs_post.sh"
        if ! [ "$norun" ]; then
            echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
            cat jobs.sh      | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
            echo "Simulations completed, extracting trace data"
            cat jobs_post.sh | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
            echo "Done"
        fi
    fi
else
    echo Unsupported number of pixels $pixels
fi

