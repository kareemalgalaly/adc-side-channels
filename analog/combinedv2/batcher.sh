#!/bin/bash
echo "#!/bin/bash" > jobs.sh

# Defaults -------------------------------------------------

CPU_MAX="$(lscpu | grep ^CPU.s.: | grep -oE '[0-9]+')"
CPU_EAC="$(grep -oE 'set num_threads=[0-9]+ ' .spiceinit | grep -oE '[0-9]+')"
SIM_CNT=$(((CPU_MAX - 4) / CPU_EAC))
MULTMOD=""

# Arguments ------------------------------------------------

local opt OPTIND
while getopts "hc:mM" opt
do
    case "$opt" in
        c ) SIM_CNT=$OPTARG ;;
        m ) MULTMOD='-m' ;;
        h ) echo "Usage: ./batcher.s [-h] [-c SIM_CNT] [-m|M]"; return 1 ;;
    esac
done
shift $((OPTIND - 1))

# Pre-run Summary ------------------------------------------

EFF_CPU=$((SIM_CNT * CPU_EAC))

echo "CPU_MAX $CPU_MAX"
echo "CPU_EAC $CPU_EAC"
echo " x SMLT $SIM_CNT = $EFF_CPU EFF_CPU"

if [ $EFF_CPU -gt $CPU_MAX ]; then
    echo "REQUESTED CPUs $EFF_CPU > MAXIMUM AVAILABLE $CPU_MAX"
    exit 1
fi

[ "$MULTMOD" ] && echo "MULTIMACHINE MODE ENABLED"

# Main -----------------------------------------------------

[ "$MULTMOD" ] && mkdir -p .multisync

for power in ideal; do
  for arch in prot; do
    for chunk in $(seq 3); do
      for corner in tt ss fs; do # fs 
        ./run.sh $MULTMOD -s $((256*(chunk-1))) -S $((256*chunk-1)) -q $SIM_CNT -kN power=$power arch=$arch corner=$corner > /dev/null
        echo "notify -t jobs 'Group Complete' 'power=$power arch=$arch corner=$corner '" >> jobs.sh
      done
    done
  done
done

kbatch -c $SIM_CNT jobs.sh --project eda
