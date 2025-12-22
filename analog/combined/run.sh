#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

sstart=0
sstop=256
queue=1
norun=""
outdir="outfiles/dataset"

while getopts "o:s:S:q:N" opt
do
    case "$opt" in 
        o ) outdir="outfiles/${dataset}" ;;
        s ) sstart="${OPTARG}"           ;;
        S ) sstop="${OPTARG}"            ;;
        q ) queue="${OPTARG}"            ;;
        N ) norun=1                      ;;
    esac
done

shift $((OPTIND - 1))

# Environment Variable Defaults

if [ "$PYTHON" = "" ]; then PYTHON="python3"; fi
TENG="$PYTHON ../../script/teng.py"
SMAIN="$TENG main.temp.cir $@"
SPOST="$TENG post.temp.cir $@"
NGBATCH="ngspice -b -r $outdir/rawfile"

# Main

echo "#!/bin/bash" > jobs.sh
mkdir -p $outdir

for s in $(seq $sstart $sstop); do echo "${NGBATCH}_a_${s} <($SMAIN 'seed=eval:$s' 'ddir=$outdir' 'dmode=model')" >> jobs.sh; done
for s in $(seq $sstart $sstop); do echo "ngspice <($SPOST 'seed=eval:$s' 'ddir=$outdir' 'mode=a')"                >> jobs.sh; done
for s in $(seq $sstart $sstop); do echo "${NGBATCH}_d_${s} <($SMAIN 'seed=eval:$s' 'ddir=$outdir' 'amode=model')" >> jobs.sh; done
for s in $(seq $sstart $sstop); do echo "ngspice <($SPOST 'seed=eval:$s' 'ddir=$outdir' 'mode=d')"                >> jobs.sh; done

echo "Generated jobs.sh, jobs_post.sh"
if ! [ "$norun" ]; then
    echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
    cat jobs.sh      | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
    echo "Done"
fi
