import matplotlib.pyplot as plt
import pandas as pd
import json
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
RESULTS_DIR = Path("results_topology_sweep")
TOPOLOGIES = ["grid", "cycle"]
TARGET_LAMBDA = 0.95  # <--- The fix

def main():
    print(f"--- Re-plotting Summary Graphs for Lambda={TARGET_LAMBDA} ---")
    
    # 1. Load Data
    data = []
    files = sorted(RESULTS_DIR.rglob("*_metrics.json"))
    
    if not files:
        print("No result files found. Wait for simulation to finish.")
        return

    print(f"Scanning {len(files)} files...")
    
    for f in files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                
                # Check Lambda
                lam = content.get("lambda", 0.0)
                # Float comparison tolerance
                if abs(lam - TARGET_LAMBDA) > 0.001:
                    continue

                # Extract Power
                match = re.search(r"_P(\d+)_", f.name)
                power = int(match.group(1)) if match else 0
                
                topo = f.parent.name
                
                data.append({
                    "Topology": topo,
                    "Policy": content.get("policy"),
                    "Power": power,
                    "Mean_W": content.get("mean_W", 0),      # E[R]
                    "Cost": content.get("avg_req_dist", 0)   # E[c]
                })
        except:
            pass

    if not data:
        print(f"No data found for Lambda {TARGET_LAMBDA} yet.")
        return

    df = pd.DataFrame(data)

    # 2. Plotting
    for topo in TOPOLOGIES:
        subset = df[df["Topology"] == topo]
        if subset.empty: continue
        
        print(f"Plotting {topo.upper()}...")
        out_dir = RESULTS_DIR / topo
        
        # --- E[R] vs Power ---
        plt.figure(figsize=(10, 6))
        g_data = subset[subset["Policy"] == "poKL"].sort_values("Power")
        s_data = subset[subset["Policy"] == "spatialKL"].sort_values("Power")
        
        plt.plot(g_data["Power"], g_data["Mean_W"], marker='o', label="Global (poKL)", color='blue')
        plt.plot(s_data["Power"], s_data["Mean_W"], marker='s', label="Spatial (spatialKL)", color='orange')
        
        plt.title(f"Effect of Choice Power on Response Time ({topo.capitalize()}, $\lambda={TARGET_LAMBDA}$)")
        plt.xlabel("Power ($d$ choices)")
        plt.ylabel("Mean Response Time ($E[R]$)")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.savefig(out_dir / f"summary_resp_vs_power_{topo}_lam0.95.png", dpi=300)
        plt.close()

        # --- E[c] vs Power ---
        plt.figure(figsize=(10, 6))
        
        plt.plot(g_data["Power"], g_data["Cost"], marker='o', label="Global (poKL)", color='blue')
        plt.plot(s_data["Power"], s_data["Cost"], marker='s', label="Spatial (spatialKL)", color='orange')
        
        plt.title(f"Communication Cost vs. Power ({topo.capitalize()}, $\lambda={TARGET_LAMBDA}$)")
        plt.xlabel("Power ($d$ choices)")
        plt.ylabel("Avg L1 Distance ($E[c]$)")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.savefig(out_dir / f"summary_cost_vs_power_{topo}_lam0.95.png", dpi=300)
        plt.close()

    print("Done! Plots saved in topology folders.")

if __name__ == "__main__":
    main()