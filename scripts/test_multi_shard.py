import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
BIN_PATH = "./bin/loadbal_sim"
OUT_DIR = Path("results_multi_shard_test")
N = 1000
M = 100_000         
TARGET_RHO = 0.80   
TOPO = "cycle"

# Test Cases: Maximum Shards per Job
X_VALUES = [1, 3, 5] 

STRATEGIES = [
    {
        "name": "Global Random",
        "policy": "poKL",
        "color": "blue",
        "marker": "o",
        "k": 0,
        "L": 5 
    },
    {
        "name": "Spatial (Neighbors)",
        "policy": "spatialKL",
        "color": "orange",
        "marker": "s",
        "k": 10,
        "L": 2   
    }
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def calculate_lambda(max_shards, target_rho):
    avg_job_size = (1 + max_shards) / 2.0
    return target_rho / avg_job_size

def get_cpp_lam_string(lam):
    """
    Mimics C++'s std::to_string(lam).substr(0,4).
    Examples: 
      0.8  -> "0.80"
      0.4  -> "0.40"
      0.2666 -> "0.26"
    """
    return "{:.6f}".format(lam)[:4]

def run_simulation(x, strat):
    lam = calculate_lambda(x, TARGET_RHO)
    
    # Tag logic matches your run command
    tag = f"x{x}_{strat['policy']}"
    
    cmd = [
        BIN_PATH,
        "--n", str(N),
        "--m", str(M),
        "--lambda", f"{lam:.4f}", # Pass precise lambda to binary
        "--policy", strat["policy"],
        "--topo", TOPO,
        "--k", str(strat["k"]),
        "--L", str(strat["L"]),
        "--x", str(x),
        "--outdir", str(OUT_DIR),
        "--tag", tag
    ]

    print(f"Running X={x} ({strat['name']}): Lambda={lam:.4f} ...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        
        # --- FIX IS HERE ---
        # Match C++ filename format: lam + first 4 chars of string
        lam_str = get_cpp_lam_string(lam)
        base_name = f"{strat['policy']}_{TOPO}_n{N}_lam{lam_str}_{tag}_hist.csv"
        return OUT_DIR / base_name
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        return None

def plot_results(results_map):
    fig, axes = plt.subplots(1, len(X_VALUES), figsize=(6 * len(X_VALUES), 6), sharey=True)
    if len(X_VALUES) == 1: axes = [axes]

    for i, x in enumerate(X_VALUES):
        ax = axes[i]
        
        for strat in STRATEGIES:
            csv_path = results_map.get((x, strat["name"]))
            
            if csv_path and csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    # Clean columns just in case
                    df.columns = [c.strip().replace("# ", "") for c in df.columns]
                    
                    # Plot
                    ax.semilogy(df["QueueLength"], df["Probability"], 
                                label=strat["name"], 
                                color=strat["color"], 
                                marker=strat["marker"], 
                                linewidth=2, alpha=0.7)
                except Exception as e:
                    print(f"Error reading {csv_path}: {e}")
            else:
                print(f"Warning: File not found: {csv_path}")

        avg_size = (1 + x) / 2
        ax.set_title(f"Max Shards = {x}\n(Avg Job Size = {avg_size:.1f})", fontsize=14, fontweight='bold')
        ax.set_xlabel("Queue Length ($k$)", fontsize=12)
        if i == 0:
            ax.set_ylabel("Probability $P(Q=k)$ (Log Scale)", fontsize=12)
        
        ax.grid(True, which="both", linestyle="--", alpha=0.4)
        ax.set_ylim(1e-5, 1.0)
        ax.set_xlim(0, 20)
        ax.legend()

    plt.suptitle(f"Multi-Server Job Distribution (Constant Load $\\rho={TARGET_RHO}$)", fontsize=16)
    plt.tight_layout()
    
    out_img = OUT_DIR / "multi_server_comparison.png"
    plt.savefig(out_img, dpi=300)
    print(f"\nPlot saved to: {out_img}")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("Compiling...")
    subprocess.run(["make"], check=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results_map = {} 

    for x in X_VALUES:
        for strat in STRATEGIES:
            csv_path = run_simulation(x, strat)
            results_map[(x, strat["name"])] = csv_path

    plot_results(results_map)