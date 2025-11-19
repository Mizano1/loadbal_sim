#!/bin/bash

# Compilation
make

# Common Parameters
N=1000
M=1000000
OUT_DIR="results"

echo "--- Starting Experiments ---"

# 1. Response Time Sweep (Lambda 0.65 to 0.95)
# Goal: Plot Mean Response Time (Mean_W) vs Lambda
for LAMBDA in 0.65 0.75 0.85 0.95; do
    # PoT (d=2 -> k=0 local, L=1 global)
    ./bin/loadbal_sim --n $N --m $M --lambda $LAMBDA --policy poKL --k 0 --L 1 --outdir $OUT_DIR --tag d2
    
    # SpatialKL (d=2 -> k=1 local, L=0 global)
    ./bin/loadbal_sim --n $N --m $M --lambda $LAMBDA --policy spatialKL --k 1 --L 0 --outdir $OUT_DIR --tag d2
done

# 2. Queue Length Distribution (High Load)
# Goal: Get histogram CSV for comparison
LAMBDA=0.95
./bin/loadbal_sim --n $N --m $M --lambda $LAMBDA --policy poKL --k 0 --L 1 --outdir $OUT_DIR --tag dist_check

echo "--- Done. Results saved in $OUT_DIR/ ---"