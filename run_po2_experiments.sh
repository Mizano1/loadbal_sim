#!/bin/bash

# ==========================================
# CONFIGURATION
# ==========================================
BIN="./bin/loadbal_sim"
OUT_DIR="results_all_topologies"
N=525
M=10000000
COST=1.0

# Lambdas to sweep (matching your python scripts)
LAMBDAS=(0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 )

# Topologies to run
TOPOLOGIES=("grid" "cycle" "cluster")

# Cluster specifics (only used when topo is cluster)
CLUSTERS=21

# Make sure the output directory exists
mkdir -p $OUT_DIR

echo "--- STARTING POWER-OF-2 DATA GENERATION ---"
echo "N=$N, M=$M, Cost=$COST"
echo "Output Directory: $OUT_DIR"
echo "-------------------------------------------"

# 1. Loop over Topologies
for TOPO in "${TOPOLOGIES[@]}"; do
    echo "Processing Topology: $TOPO"
    
    # Create topology subdirectory (e.g., results_all_topologies/grid)
    TOPO_DIR="$OUT_DIR/$TOPO"
    mkdir -p $TOPO_DIR

    # Set Cluster Flag if needed
    EXTRA_FLAGS=""
    if [ "$TOPO" == "cluster" ]; then
        EXTRA_FLAGS="--clusters $CLUSTERS"
    fi

    # 2. Loop over Lambdas
    for LAM in "${LAMBDAS[@]}"; do
        # -----------------------------------------------------------------
        # STRATEGY 1: Global Po2 (Baseline)
        # Logic: 1 Source + 1 Global Random = 2 choices (d=2)
        # Params: k=0, L=1
        # -----------------------------------------------------------------
        POLICY="poKL"
        TAG="${TOPO}_P2_${POLICY}"
        
        echo "  Running Global Po2 (Lam=$LAM)..."
        $BIN --n $N --m $M --lambda $LAM \
             --policy $POLICY --topo $TOPO \
             --cost $COST \
             --k 0 --L 1 \
             $EXTRA_FLAGS \
             --outdir $TOPO_DIR --tag $TAG > /dev/null

    

    done
    echo "  [Done with $TOPO]"
done

echo "-------------------------------------------"
echo "All Po2 experiments finished."