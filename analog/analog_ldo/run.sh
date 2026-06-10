#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

sstart=0
sstop=255
queue=1
batch=""
norun=""
append=""
outdir=""
keepold=""

while getopts "o:s:S:q:nNbk" opt
do
    case "$opt" in 
        o ) outdir="outfiles/${dataset}" ;;
        s ) sstart="${OPTARG}"           ;;
        S ) sstop="${OPTARG}"            ;;
        q ) queue="${OPTARG}"            ;;
        b ) batch=1                      ;;
        n ) norun=1                      ;;
        N ) norun=1;append=1             ;;
        k ) keepold=1                    ;;
    esac
done

if [ "$sstop" -lt "$sstart" ]; then
    sstop=$sstart
fi

shift $((OPTIND - 1))

if [ "$outdir" = "" ]; then
    outdir="outfiles/dataset_$*"
    outdir="${outdir// /_}"
    outdir="${outdir//=/:}"
fi
if [ "$SCRATCH" != "" ]; then
    outdir="$SCRATCH/$outdir"
fi

echo "Dumping outputs to $outdir"

# Environment Variable Defaults

if [ "$PYTHON" = "" ]; then PYTHON="python3"; fi
TENG="$PYTHON ../../script/teng.py"
SMAIN="$TENG main.tspice $@"
SPOST="$TENG post.tspice $@"
PYPATH="$(which $PYTHON)"

# Main

if ! [ "$append" ]; then
    echo "#!/bin/bash" > jobs.sh
fi

if [ "$batch" ]; then
    COUNT=1
    echo Running in Batch mode

    for i in $(seq $sstart $sstop); do
        if [ "$keepold" ]; then
            echo -n "[ -f $outdir/ptrace_${i}_d* ] || " >> jobs.sh
        fi
        echo -n "ngspice -b -r $outdir/rawfile_$i <($SMAIN outdir=$outdir start=$i batch= python=$PYPATH) && " >> jobs.sh
        echo "ngspice <($SPOST outdir=$outdir start=$i)" >> jobs.sh
    done

else
    COUNT=$(((sstop - sstart + 1) / queue))
    echo Interactively batching $COUNT per thread $sstart-$sstop

    for i in $(seq 1 $queue); do
        istop=$((sstart + COUNT))
        if [ $istop -gt $sstop ]; then
            istop=$((sstop + 1))
        fi
        echo "ngspice -i <($SMAIN outdir=$outdir start=$sstart stop=$istop python=$PYPATH)" >> jobs.sh
        sstart=$istop
    done

fi
echo "Generated jobs.sh"

mkdir -p $outdir

if ! [ "$norun" ]; then
    echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
    if command -v kbatch > /dev/null; then
        kbatch jobs.sh -c $queue --project eda
        exit $?
    else
        cat jobs.sh | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
        echo "Done"
    fi
fi
