import subprocess
import json
import matplotlib.pyplot as plt
import pandas as pd
import time
import sys
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
BIN_PATH = "./bin/loadbal_sim"
OUT_DIR = Path("experiments_10_12_2025/results_large_scale")

# System Parameters
N = 525                     # Total Servers
SERVERS_PER_CLUSTER = 25    # Desired Cluster Size
CLUSTERS = N // SERVERS_PER_CLUSTER  # 525 / 25 = 21 Clusters

M = 100_000_000             # 10^8 Jobs (VERY LARGE!)
COST = 1.0                  # Communication Cost Penalty

# System Loads to Test
# Focusing on high load where differences matter most
LAMBDAS = [0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
LAMBDAS =[0.95]

# Policies to Compare
STRATEGIES = [
    {
        "name": "Global Po3 (poKL)",
        "policy": "poKL",
        "k": 0, "L": 2,      # 3 random choices (d=3)
        "color": "blue",
        "marker": "o"
    },
    {
        "name": "Hybrid Spatial (k=2, L=1)",
        "policy": "spatialKL",
        "k": 1, "L": 1,      # 2 local neighbors + 1 global random
        "color": "orange",
        "marker": "s"
    }
]
# ==========================================

def run_simulation(lam, strategy):
    """Runs the C++ binary and returns the parsed metrics."""
    tag = f"{strategy['policy']}_k{strategy['k']}_L{strategy['L']}"
    
    # Construct the command
    cmd = [
        BIN_PATH,
        "--n", str(N),
        "--m", str(M),
        "--lambda", str(lam),
        "--policy", strategy["policy"],
        "--topo", "cluster",
        "--clusters", str(CLUSTERS),
        "--cost", str(COST),
        "--k", str(strategy["k"]),
        "--L", str(strategy["L"]),
        "--outdir", str(OUT_DIR),
        "--tag", tag
    ]
    
    print(f"  Running {strategy['name']} (Lam={lam})...", end="", flush=True)
    start_t = time.time()
    
    try:
        # Run subprocess (suppress stdout unless error)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
        duration = time.time() - start_t
        print(f" Done ({duration:.1f}s)")
        
        # Parse Result JSON
        json_filename = f"{strategy['policy']}_cluster_n{N}_lam{lam:.4f}_{tag}_metrics.json"
        json_path = OUT_DIR / json_filename
        
        if not json_path.exists():
            print(f"    Error: Result file {json_filename} not found.")
            return None
            
        with open(json_path, 'r') as f:
            return json.load(f)
            
    except subprocess.CalledProcessError:
        print(" Failed (Runtime Error)")
        return None
    except Exception as e:
        print(f" Failed ({e})")
        return None

def main():
    # 0. Setup
    print(f"--- LARGE SCALE SIMULATION SETUP ---")
    print(f"Nodes: {N}")
    print(f"Clusters: {CLUSTERS} (Size ~{N//CLUSTERS})")
    print(f"Jobs: {M} (10^8)")
    print(f"Output: {OUT_DIR}")
    print("-" * 40)
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Compilation Check
    print("Checking compilation...")
    try:
        subprocess.run(["make"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: Compilation failed. Fix C++ errors first.")
        sys.exit(1)

    # 2. Run Experiments
    results = []
    
    total_start = time.time()
    
    for lam in LAMBDAS:
        print(f"\n[Testing Lambda = {lam}]")
        for strat in STRATEGIES:
            metrics = run_simulation(lam, strat)
            if metrics:
                results.append({
                    "Strategy": strat["name"],
                    "Lambda": lam,
                    "Mean_W": metrics.get("mean_W", 0),
                    "Cost": metrics.get("avg_req_dist", 0)
                })
    
    total_time = time.time() - total_start
    print(f"\nAll experiments completed in {total_time/60:.1f} minutes.")

    # 3. Plot Results
    if not results:
        print("No results to plot.")
        return

    df = pd.DataFrame(results)
    
    fig, ax = plt.subplots(1, 2, figsize=(16, 6))
    
    # --- Plot A: Response Time ---
    for strat in STRATEGIES:
        subset = df[df["Strategy"] == strat["name"]]
        ax[0].plot(subset["Lambda"], subset["Mean_W"], 
                   label=strat["name"], color=strat["color"], 
                   marker=strat["marker"], linewidth=2)
    
    ax[0].set_title(f"Response Time ($N={N}, M=10^8$)", fontsize=14)
    ax[0].set_xlabel("System Load ($\lambda$)", fontsize=12)
    ax[0].set_ylabel("Mean Response Time ($E[W]$)", fontsize=12)
    ax[0].legend(fontsize=11)
    ax[0].grid(True, alpha=0.3)

    # --- Plot B: Communication Cost ---
    for strat in STRATEGIES:
        subset = df[df["Strategy"] == strat["name"]]
        ax[1].plot(subset["Lambda"], subset["Cost"], 
                   label=strat["name"], color=strat["color"], 
                   marker=strat["marker"], linewidth=2)
        
    ax[1].set_title(f"Communication Overhead (Cost Factor={COST})", fontsize=14)
    ax[1].set_xlabel("System Load ($\lambda$)", fontsize=12)
    ax[1].set_ylabel("Avg Cost ($E[c]$)", fontsize=12)
    ax[1].legend(fontsize=11)
    ax[1].grid(True, alpha=0.3)
    
    # Save
    out_img = OUT_DIR / "large_scale_results.png"
    plt.tight_layout()
    plt.savefig(out_img, dpi=300)
    print(f"\nGraphs saved to: {out_img}")

if __name__ == "__main__":
    main()