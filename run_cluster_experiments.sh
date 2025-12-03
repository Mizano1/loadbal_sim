#!/bin/bash

# 1. Setup
BIN="./bin/loadbal_sim"
TRACE_FILE="final_trace.csv"
OUT_DIR="results_cluster"
mkdir -p $OUT_DIR

# Compilation
echo "Compiling..."
make

if [ ! -f "$TRACE_FILE" ]; then
    echo "Error: Trace file '$TRACE_FILE' not found!"
    exit 1
fi

echo "--- Starting Cluster Experiments with Trace Data ---"

# ==========================================================
# EXPERIMENT 1: Topology Showdown (Cycle vs Cluster)
# Policy: spatialKL (uses neighbors)
# Lambda is implicitly defined by the trace, but we pass a dummy value or 
# rely on the trace reading. Note: In trace mode, lambda is ignored for arrival times 
# but might be used for some internal stat scaling if you didn't fully remove it.
# We simulate different neighbor sizes (k) to see effective connectivity.
# ==========================================================

echo "Running Experiment 1: Cycle vs Cluster..."

for K in 4 8 16; do
    # 1A. Cycle Topology
    # Neighbors are k adjacent nodes
    $BIN --n 1000 --m 200000 --policy spatialKL --topo cycle --k $K \
         --trace $TRACE_FILE --outdir $OUT_DIR --tag "cycle_k${K}"

    # 1B. Cluster Topology
    # Neighbors are all nodes in same cluster.
    # We adjust 'num_clusters' so that cluster size approx equals K for fair comparison?
    # OR we keep fixed clusters and just see how it behaves.
    # Let's use 10 clusters (100 nodes each) and varying costs.
    $BIN --n 1000 --m 200000 --policy spatialKL --topo cluster --clusters 10 --cost 1.0 \
         --trace $TRACE_FILE --outdir $OUT_DIR --tag "cluster_10_cost1.0"
done

# ==========================================================
# EXPERIMENT 2: Cost Sensitivity Analysis
# How does the "penalty" for going outside the cluster affect load?
# Policy: pot (Power of Two) - Global random choice vs Local
# Note: Your 'pot' implementation in Simulation.cpp blindly picks 2 random nodes.
# To see cluster effects with POT, your 'calculate_distance' logic needs to be 
# working (which it is) to report the 'avg_req_dist' metric.
# ==========================================================

echo "Running Experiment 2: Cost Sensitivity..."

# We fix N=1000, 10 Clusters. We vary the communication cost 'c'.
# A higher cost means 'req_dist' metric will skyrocket if we choose remote nodes.
for COST in 0.0 0.5 1.0 2.0 5.0; do
    $BIN --n 1000 --m 200000 --policy pot --topo cluster --clusters 10 --cost $COST \
         --trace $TRACE_FILE --outdir $OUT_DIR --tag "pot_cost${COST}"
done

# ==========================================================
# EXPERIMENT 3: Cluster Granularity
# Does having many small clusters work better than few large ones?
# Fixed Cost = 1.0
# ==========================================================

echo "Running Experiment 3: Cluster Granularity..."

for CLUSTERS in 2 5 10 20 50; do
    $BIN --n 1000 --m 200000 --policy spatialKL --topo cluster --clusters $CLUSTERS --cost 1.0 \
         --trace $TRACE_FILE --outdir $OUT_DIR --tag "spatial_clusters${CLUSTERS}"
done

echo "--- Experiments Done. Results in $OUT_DIR ---"