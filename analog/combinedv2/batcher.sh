#!/bin/bash
echo "#!/bin/bash" > jobs.sh

CPU=28

if ! grep 'set num_threads=1 ' .spiceinit; then
    echo Num threads must be 1!
    exit 1
fi

for power in ideal; do
  for arch in prot; do
    for chunk in $(seq 3); do
      for corner in tt ss fs; do # fs 
        ./run.sh -s $((256*(chunk-1))) -S $((256*chunk-1)) -q $CPU -kN power=$power arch=$arch corner=$corner # clean=
        echo "notify -t jobs 'Group Complete' 'power=$power arch=$arch corner=$corner '" >> jobs.sh
      done
    done
  done
done

kbatch -c $CPU jobs.sh --project eda
