#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

sstart=0
sstop=255
queue=1
batch=""
norun=""
outdir=""

while getopts "o:s:S:q:nb" opt
do
    case "$opt" in 
        o ) outdir="outfiles/${dataset}" ;;
        s ) sstart="${OPTARG}"           ;;
        S ) sstop="${OPTARG}"            ;;
        q ) queue="${OPTARG}"            ;;
        b ) batch=1                      ;;
        n ) norun=1                      ;;
    esac
done

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

# Main

echo "#!/bin/bash" > jobs.sh

if [ "$batch" ]; then
    COUNT=1
    echo Running in Batch mode

    for i in $(seq $sstart $sstop); do
        echo -n "ngspice -b -r $outdir/rawfile_$i <($SMAIN outdir=$outdir start=$i batch=) && " >> jobs.sh
        echo "ngspice <($SPOST outdir=$outdir start=$i)" >> jobs.sh
    done

else
    COUNT=$(((sstop - sstart + 1) / queue))
    echo Interactively batching $COUNT per thread

    for i in $(seq 1 $queue); do
        istop=$((sstart + COUNT))
        if [ $istop -gt $sstop ]; then
            istop=$((sstop + 1))
        fi
        echo "ngspice <($SMAIN outdir=$outdir start=$sstart stop=$istop)" >> jobs.sh
        sstart=$istop
    done

fi

echo "Generated jobs.sh"
if ! [ "$norun" ]; then
    mkdir -p $outdir
    echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
    cat jobs.sh      | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
    echo "Done"
fi
