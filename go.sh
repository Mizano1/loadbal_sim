#!/usr/bin/env bash
set -euo pipefail

# ----------------------
# Edit these few lines:
# ----------------------
# If you have a Makefile you want to use, set USE_MAKE=1
USE_MAKE=1

SRC_DIR="src"
BIN="./sim"
CXX=${CXX:-g++}
CXXFLAGS="-O3 -std=c++17"

# Common sim parameters:
N=200
M=100000
LAMBDA=0.95
MU=1.0
GRAPH=grid
K=1
L=1
OUTDIR=plots

# Policies to run (space-separated):
POLICIES=("spatialKL" "pot" "poKL")

# Number of seeds per policy:
SEEDS=1
# ----------------------

mkdir -p "$OUTDIR"

echo "[1/3] Compiling..."
if [[ "$USE_MAKE" -eq 1 ]]; then
  make
else
  $CXX $CXXFLAGS -o "$BIN" "$SRC_DIR/main.cpp" "$SRC_DIR/Simulation.cpp"
fi

echo "[2/3] Running simulations..."
for policy in "${POLICIES[@]}"; do
  for ((s=1; s<=SEEDS; ++s)); do
    "$BIN" \
      --n "$N" --m "$M" --lambda "$LAMBDA" --mu "$MU" \
      --graph "$GRAPH" --policy "$policy" --k "$K" --L "$L" \
      --seed "$s" --outdir "$OUTDIR"
  done
done

echo "[3/3] Plotting..."
python3 plot_all.py

echo "Done. See plots/ for PNGs."
