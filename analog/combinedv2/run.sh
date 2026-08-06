#!/bin/bash

# Arguments

# local opt OPTIND
# local interactive dvalue pixels seed corner numsim norun

sstart=0
sstop=255
queue=1
interactive=""
norun=""
runic=""
append=""
outdir=""
keepold=""
multicp=""
runanlg=1

while getopts "o:s:S:q:nNBkmiIA" opt
do
    case "$opt" in 
        o ) outdir="outfiles/${dataset}" ;;
        s ) sstart="${OPTARG}"           ;;
        S ) sstop="${OPTARG}"            ;;
        q ) queue="${OPTARG}"            ;;
        B ) interactive=1                ;;
        n ) norun=1                      ;;
        N ) norun=1;append=1             ;;
        k ) keepold=1                    ;;
        m ) multicp=1                    ;;
        i ) runic=1                      ;;
        I ) runic=force                  ;;
        A ) runanlg=""                   ;;
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

if [ -f $outdir/op.ic ] || [ "$runic" ]; then
    smode=main
else
    smode=full
fi

# Environment Variable Defaults

if [ "$PYTHON" = "" ]; then PYTHON="python3"; fi
TENG="$PYTHON ../../script/teng.py"
SARGS="'python=$(which $PYTHON)' outdir=$outdir"
SMAIN="$TENG main.tspice $@ $SARGS smode=$smode"
SPOST="$TENG post.tspice $@ $SARGS smode=$smode"
NGBCH="ngspice -b -r $outdir/rawfile"

# Main

if ! [ "$append" ]; then
    echo "#!/bin/bash" > jobs.sh
fi

if ! [ -f $outdir/*_model_op.ic ] && [ "$runic" ] || [ "$runic" = force ]; then
    echo Running Analog IC Simulation
    echo ngspice -i "<($TENG main.tspice "$@" $SARGS smode=ic start=128 stop=128)"
    if ! [ "$norun" ]; then
        ngspice -i <($TENG main.tspice "$@" $SARGS dmode=model smode=ic start=128 stop=128 cpu=8)
    fi
fi
if ! [ -f $outdir/model_*_op.ic ] && [ "$runic" ] || [ "$runic" = force ]; then
    echo Running Digital IC Simulation
    echo ngspice -i "<($TENG main.tspice "$@" $SARGS smode=ic start=128 stop=128)"
    if ! [ "$norun" ]; then
        ngspice -i <($TENG main.tspice "$@" $SARGS amode=model smode=ic start=128 stop=128 cpu=8)
    fi
fi

if ! [ "$interactive" ]; then
    COUNT=1
    echo Running in Batch mode

    for i in $(seq $sstart $sstop); do
        if [ "$multicp" ]; then echo -n "[ -f .multisync/$i ] || ( touch .multisync/$i &&"; fi
        if [ "$keepold" ]; then
            echo -n "[ -f $outdir/ptrace_d_${i}_d* ] || ( ( " >> jobs.sh
        else
            echo -n '( ( ' >> jobs.sh
        fi

        if [ "$runanlg" = 1 ]; then
            if [ "$keepold" ]; then
                echo -n "[ -f $outdir/ptrace_d_${i}_a* ] || " >> jobs.sh
            fi
        echo -n "${NGBCH}_a_${i} <($SMAIN batch= 'start=$i' 'dmode=model') && " >> jobs.sh
        echo -n         "ngspice <($SPOST batch= 'start=$i' 'dmode=model') ) && " >> jobs.sh
        fi
        echo -n "${NGBCH}_d_${i} <($SMAIN batch= 'start=$i' 'amode=model') && " >> jobs.sh
        echo -n         "ngspice <($SPOST batch= 'start=$i' 'amode=model') ) "  >> jobs.sh

        if [ "$multicp" ]; then
            echo " )" >>  jobs.sh
        else
            echo >> jobs.sh
        fi
    done

else
    # Interactive batching
    # COUNT=$(((sstop - sstart + 1) / queue))
    # echo Interactively batching $COUNT per thread $sstart-$sstop

    # for i in $(seq 1 $queue); do
    #     istop=$((sstart + COUNT))
    #     if [ $istop -gt $sstop ]; then
    #         istop=$((sstop + 1))
    #     fi
    #     echo "ngspice -i <($SMAIN start=$sstart stop=$istop)" >> jobs.sh
    #     sstart=$istop
    # done

    # Just Interactive
    if [ "$runanlg" = 1 ]; then
        echo Running Analog Interactive
        ngspice -i <($SMAIN start=$sstart stop=$sstop interactive=1 plot=1 dmode=model)
    fi
    echo Running Digital Interactive
    ngspice -i <($SMAIN start=$sstart stop=$sstop interactive=1 plot=1 amode=model)
    exit
fi
echo "Generated jobs.sh"

mkdir -p $outdir

if ! [ "$norun" ]; then
    echo "Batching with NUM_SIMULTANEOUS_JOBS=$queue"
    if command -v kbatch > /dev/null; then
        kbatch jobs.sh -c $queue --project eda -l auto
        exit $?
    else
        cat jobs.sh | xargs -I cmd -P $queue bash -c "echo 'Running cmd'; eval 'cmd'"
        echo "Done"
    fi
fi
