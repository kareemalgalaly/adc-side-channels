#!/bin/bash
echo "#!/bin/bash" > jobs.sh

CPU=11

for power in cascade; do
  for arch in prot; do
    for corner in tt ss; do # fs 
      ./run.sh -s 0 -S 255 -q $CPU -bkN power=$power arch=$arch corner=$corner # clean=
      echo "notify -t jobs 'Group Complete' 'power=$power arch=$arch corner=$corner '" >> jobs.sh
    done
  done
done

kbatch -c $CPU jobs.sh --project eda
