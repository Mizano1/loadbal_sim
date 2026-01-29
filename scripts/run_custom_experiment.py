import subprocess
import json
import matplotlib.pyplot as plt
import pandas as pd
import time
import sys
import os
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# ==========================================
# CONFIGURATION
# ==========================================
BIN_PATH = "./bin/loadbal_sim"
OUT_DIR = Path("experiments/experiments_custom/results")
PLOT_DIR = Path("experiments/experiments_custom/plots")

# System Parameters
N = 525
M = 100_000_000  # 10^8
COMM_COST = 1.0  

# Load Parameters
# Generating 0.65, 0.70, ..., 0.95
LAMBDAS = [round(x, 2) for x in np.arange(0.65, 0.96, 0.05)]

# "Power of d" Definitions
POWERS = range(2, 8) # 2 to 7

TOPOLOGIES = ["cycle", "grid"] 

# Parallel Workers
MAX_WORKERS = os.cpu_count()
# ==========================================

def get_cpp_lam_string(lam):
    """Mimics C++ std::to_string(lam).substr(0,4) behavior."""
    # C++ to_string usually gives 6 decimals: 0.650000 -> substr(0,4) -> "0.65"
    # 0.700000 -> "0.70"
    return "{:.6f}".format(lam)[:4]

def get_configs():
    configs = []
    for topo in TOPOLOGIES:
        for d in POWERS:
            # 1. Spatial Configuration
            # "Power of 2" = k=1, L=1 (Total added: 2)
            # "Power of 3" = k=2, L=1 (Total added: 3)
            k_spatial = d - 1
            L_spatial = 1
            
            configs.append({
                "topo": topo,
                "policy": "spatialKL",
                "d_label": d,
                "k": k_spatial,
                "L": L_spatial,
                "tag": f"spatial_d{d}"
            })
            
            # 2. Global Configuration
            # Matches total probes: L=d, k=0
            configs.append({
                "topo": topo,
                "policy": "poKL",
                "d_label": d,
                "k": 0,
                "L": d,
                "tag": f"global_d{d}"
            })
    return configs

def run_simulation(args):
    """Worker function for parallel execution."""
    cfg, lam = args
    
    # Unique tag for filename
    full_tag = f"{cfg['tag']}_d{cfg['d_label']}"
    
    # --- FIX: Match C++ Filename Format ---
    lam_str = get_cpp_lam_string(lam)
    json_filename = f"{cfg['policy']}_{cfg['topo']}_n{N}_lam{lam_str}_{full_tag}_metrics.json"
    json_path = OUT_DIR / json_filename

    # Skip if already exists
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return {
                "status": "skipped",
                "topo": cfg["topo"], "policy": cfg["policy"], "d": cfg["d_label"],
                "lambda": lam,
                "E_R": data.get("mean_W", 0),
                "Cost": data.get("avg_req_dist", 0)
            }
        except:
            pass # Re-run if corrupt

    cmd = [
        BIN_PATH,
        "--n", str(N), "--m", str(M), "--lambda", str(lam),
        "--policy", cfg["policy"], "--topo", cfg["topo"],
        "--cost", str(COMM_COST),
        "--k", str(cfg["k"]), "--L", str(cfg["L"]),
        "--outdir", str(OUT_DIR), "--tag", full_tag
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
        
        if not json_path.exists():
            return {"status": "failed", "error": f"File not found: {json_path}"}

        with open(json_path, 'r') as f:
            data = json.load(f)
            
        return {
            "status": "ran",
            "topo": cfg["topo"], "policy": cfg["policy"], "d": cfg["d_label"],
            "lambda": lam,
            "E_R": data.get("mean_W", 0),
            "Cost": data.get("avg_req_dist", 0)
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def main():
    print(f"--- STARTING CUSTOM EXPERIMENT ---")
    print(f"Nodes: {N}, Jobs: {M}")
    print(f"Lambdas: {LAMBDAS}")
    print(f"Powers: {list(POWERS)}")
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Compile
    print("Compiling...")
    subprocess.run(["make"], check=True, stdout=subprocess.DEVNULL)
    
    # 2. Build Task Queue
    configs = get_configs()
    tasks = []
    for cfg in configs:
        for lam in LAMBDAS:
            tasks.append((cfg, lam))
            
    print(f"Queued {len(tasks)} simulations using {MAX_WORKERS} workers...")
    
    results = []
    
    # 3. Execute
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_simulation, t): t for t in tasks}
        
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            res = future.result()
            if res["status"] != "failed":
                results.append(res)
                # Simple progress bar
                sys.stdout.write(f"\rProgress: {done_count}/{len(tasks)}")
                sys.stdout.flush()
            else:
                print(f"\nFailed: {res.get('error')}")

    print("\nSimulations Complete. Generating Plots...")
    
    if not results: 
        print("No results collected.")
        return

    df = pd.DataFrame(results)
    
    # ==========================================
    # PLOTTING
    # ==========================================
    
    # Color map for Powers
    colors = plt.cm.viridis(np.linspace(0, 1, len(POWERS)))
    color_map = {d: c for d, c in zip(POWERS, colors)}
    
    # --- PLOT 1 & 2: E[R] vs Lambda (One plot per Topology) ---
    for topo in TOPOLOGIES:
        plt.figure(figsize=(12, 8))
        topo_data = df[df["topo"] == topo]
        
        # Plot Global (Dashed) and Spatial (Solid) for each d
        for d in POWERS:
            c = color_map[d]
            
            # Global Line
            g_data = topo_data[(topo_data["d"] == d) & (topo_data["policy"] == "poKL")].sort_values("lambda")
            if not g_data.empty:
                plt.plot(g_data["lambda"], g_data["E_R"], 
                         label=f"Global d={d}", color=c, linestyle="--", marker='x', alpha=0.7)
            
            # Spatial Line
            s_data = topo_data[(topo_data["d"] == d) & (topo_data["policy"] == "spatialKL")].sort_values("lambda")
            if not s_data.empty:
                plt.plot(s_data["lambda"], s_data["E_R"], 
                         label=f"Spatial d={d}", color=c, linestyle="-", marker='o', linewidth=2)
                
        plt.title(f"Response Time vs Load ({topo.capitalize()})", fontsize=16)
        plt.xlabel("System Load ($\lambda$)", fontsize=14)
        plt.ylabel("Mean Response Time ($E[R]$)", fontsize=14)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(PLOT_DIR / f"resp_vs_lambda_{topo}.png", dpi=300)
        plt.close()
        print(f"Saved {topo} plot.")

    # --- PLOT 3 & 4: E[R] and Cost vs d (at Lambda=0.95) ---
    target_lam = 0.95
    # Use close comparison for floats
    subset = df[np.isclose(df["lambda"], target_lam)]
    
    if not subset.empty:
        # 3. Response Time vs d
        plt.figure(figsize=(10, 6))
        for topo in TOPOLOGIES:
            t_data = subset[subset["topo"] == topo]
            
            # Global
            g_data = t_data[t_data["policy"] == "poKL"].sort_values("d")
            plt.plot(g_data["d"], g_data["E_R"], linestyle="--", marker='x', label=f"{topo}-Global")
            
            # Spatial
            s_data = t_data[t_data["policy"] == "spatialKL"].sort_values("d")
            plt.plot(s_data["d"], s_data["E_R"], linestyle="-", marker='o', linewidth=2, label=f"{topo}-Spatial")

        plt.title(f"Response Time vs Power $d$ ($\lambda={target_lam}$)", fontsize=14)
        plt.xlabel("Power ($d$)", fontsize=12)
        plt.ylabel("Mean Response Time ($E[R]$)", fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.savefig(PLOT_DIR / "summary_resp_vs_d.png", dpi=300)
        plt.close()

        # 4. Cost vs d
        plt.figure(figsize=(10, 6))
        for topo in TOPOLOGIES:
            t_data = subset[subset["topo"] == topo]
            
            # Global
            g_data = t_data[t_data["policy"] == "poKL"].sort_values("d")
            plt.plot(g_data["d"], g_data["Cost"], linestyle="--", marker='x', label=f"{topo}-Global")
            
            # Spatial
            s_data = t_data[t_data["policy"] == "spatialKL"].sort_values("d")
            plt.plot(s_data["d"], s_data["Cost"], linestyle="-", marker='o', linewidth=2, label=f"{topo}-Spatial")

        plt.title(f"Communication Cost vs Power $d$ ($\lambda={target_lam}$)", fontsize=14)
        plt.xlabel("Power ($d$)", fontsize=12)
        plt.ylabel("Avg Request Distance ($E[c]$)", fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.savefig(PLOT_DIR / "summary_cost_vs_d.png", dpi=300)
        plt.close()

    print(f"All plots saved to {PLOT_DIR}")

if __name__ == "__main__":
    main()