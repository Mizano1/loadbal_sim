import subprocess
import json
import matplotlib.pyplot as plt
import pandas as pd
import time
import sys
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# ==========================================
# CONFIGURATION
# ==========================================
BIN_PATH = "./bin/loadbal_sim"
BASE_OUT_DIR = Path("results_topology_sweep") 

# System Parameters
N = 525
M = 100_000_000             
COMM_COST = 1.0         

# Sweep Parameters
TOPOLOGIES = ["grid", "cycle"]
POWERS = [3, 4, 5, 6, 7, 8]
LAMBDAS = [0.6, 0.65, 0.7, 0.75, 0.8, 0.9, 0.95, 0.98, 0.99]

# Parallel Workers (Default: All CPU cores)
MAX_WORKERS = os.cpu_count() 
# ==========================================

def get_strategies(power):
    return [
        {
            "name": f"Global Po{power}",
            "policy": "poKL",
            "k": 0, "L": power - 1,   
            "color": "blue", "marker": "o"
        },
        {
            "name": f"Spatial Po{power}",
            "policy": "spatialKL",
            "k": power - 2, "L": 1,
            "color": "orange", "marker": "s"
        }
    ]

def run_single_simulation(args):
    """
    Worker function to run a single simulation.
    args is a tuple: (topo, lam, strategy, power, output_dir)
    """
    topo, lam, strategy, power, out_dir = args
    
    tag = f"{topo}_P{power}_{strategy['policy']}"
    
    # --- FIX: Changed .4f to .2f to match your C++ filenames ---
    json_filename = f"{strategy['policy']}_{topo}_n{N}_lam{lam:.2f}_{tag}_metrics.json"
    json_path = out_dir / json_filename
    
    # --- RESUME CHECK ---
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return {
                "status": "skipped",
                "Topology": topo, "Power": power, "Strategy": strategy["name"],
                "Policy": strategy["policy"], "Lambda": lam,
                "Mean_W": data.get("mean_W", 0), "Cost": data.get("avg_req_dist", 0)
            }
        except:
            pass # File corrupt, re-run

    # --- RUN SIMULATION ---
    cmd = [
        BIN_PATH,
        "--n", str(N), "--m", str(M), "--lambda", str(lam),
        "--policy", strategy["policy"], "--topo", topo,
        "--cost", str(COMM_COST),
        "--k", str(strategy["k"]), "--L", str(strategy["L"]),
        "--outdir", str(out_dir), "--tag", tag
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
        
        # If the simulation succeeded, the file MUST exist now.
        # But wait! If C++ generated .90 and Python looks for .90, we are good.
        if not json_path.exists():
             # Fallback check: maybe it generated .9000? 
             # (Unlikely given your report, but safety first)
             pass 

        with open(json_path, 'r') as f:
            data = json.load(f)
        return {
            "status": "ran",
            "Topology": topo, "Power": power, "Strategy": strategy["name"],
            "Policy": strategy["policy"], "Lambda": lam,
            "Mean_W": data.get("mean_W", 0), "Cost": data.get("avg_req_dist", 0)
        }
    except Exception as e:
        return {"status": "failed", "error": f"{str(e)} (Path: {json_path})"}

def main():
    print(f"--- PARALLEL SIMULATION SWEEP ({MAX_WORKERS} Cores) ---")
    
    # 1. Compile
    subprocess.run(["make"], check=True, stdout=subprocess.DEVNULL)
    BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Build Task List
    tasks = []
    for topo in TOPOLOGIES:
        current_out_dir = BASE_OUT_DIR / topo
        current_out_dir.mkdir(parents=True, exist_ok=True)
        
        for power in POWERS:
            for lam in LAMBDAS:
                for strat in get_strategies(power):
                    tasks.append((topo, lam, strat, power, current_out_dir))
    
    print(f"Queueing {len(tasks)} simulations...")
    
    all_results = []
    start_time = time.time()
    
    # 3. Execute in Parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = {executor.submit(run_single_simulation, t): t for t in tasks}
        
        # Monitor Progress
        completed = 0
        skipped = 0
        for future in as_completed(futures):
            res = future.result()
            completed += 1
            
            # Simple Progress Bar
            sys.stdout.write(f"\rProgress: {completed}/{len(tasks)} ")
            sys.stdout.flush()
            
            if res["status"] != "failed":
                if res["status"] == "skipped": skipped += 1
                all_results.append(res)
            else:
                print(f"\nFailed: {res.get('error')}")

    print(f"\n\nDone! (Skipped {skipped} existing files)")
    print(f"Total time: {(time.time() - start_time)/60:.1f} minutes.")

    # 4. PLOTTING
    if not all_results: return

    df = pd.DataFrame(all_results)
    target_lambda = 0.95

    print("Generating Plots...")
    for topo in TOPOLOGIES:
        plot_out_dir = BASE_OUT_DIR / topo
        
        # --- E[R] vs Lambda ---
        for power in POWERS:
            subset = df[(df["Topology"] == topo) & (df["Power"] == power)]
            if subset.empty: continue
            
            plt.figure(figsize=(8, 6))
            for pol in subset["Policy"].unique():
                data = subset[subset["Policy"] == pol].sort_values("Lambda")
                strat_name = data["Strategy"].iloc[0]
                plt.plot(data["Lambda"], data["Mean_W"], marker='o', linewidth=2, label=strat_name)
            
            plt.title(f"Response Time: {topo.capitalize()} (Power {power})")
            plt.xlabel("System Load ($\lambda$)")
            plt.ylabel("Mean Response Time ($E[R]$)")
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            plt.savefig(plot_out_dir / f"resp_vs_lambda_{topo}_P{power}.png", dpi=300)
            plt.close()

        # --- SUMMARY PLOTS ---
        subset = df[(df["Topology"] == topo) & (df["Lambda"] == target_lambda)]
        if subset.empty: continue
        
        # E[R] vs Power
        plt.figure(figsize=(10, 6))
        g_data = subset[subset["Policy"] == "poKL"].sort_values("Power")
        s_data = subset[subset["Policy"] == "spatialKL"].sort_values("Power")
        
        plt.plot(g_data["Power"], g_data["Mean_W"], marker='o', label="Global (poKL)", color='blue')
        plt.plot(s_data["Power"], s_data["Mean_W"], marker='s', label="Spatial (spatialKL)", color='orange')
        
        plt.title(f"Effect of Choice Power on Response Time ({topo.capitalize()}, $\lambda={target_lambda}$)")
        plt.xlabel("Power ($d$ choices)")
        plt.ylabel("Mean Response Time ($E[R]$)")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.savefig(plot_out_dir / f"summary_resp_vs_power_{topo}.png", dpi=300)
        plt.close()

        # Cost vs Power
        plt.figure(figsize=(10, 6))
        plt.plot(g_data["Power"], g_data["Cost"], marker='o', label="Global (poKL)", color='blue')
        plt.plot(s_data["Power"], s_data["Cost"], marker='s', label="Spatial (spatialKL)", color='orange')
        
        plt.title(f"Communication Cost vs. Power ({topo.capitalize()}, $\lambda={target_lambda}$)")
        plt.xlabel("Power ($d$ choices)")
        plt.ylabel("$E[c]$")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.savefig(plot_out_dir / f"summary_cost_vs_power_{topo}.png", dpi=300)
        plt.close()

if __name__ == "__main__":
    main()