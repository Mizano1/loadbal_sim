import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import json
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
DATA_FOLDERS = [
    Path("results_all_topologies"),
    Path("results_topology_sweep")
]
TOPOLOGIES = ["grid", "cycle", "cluster"]
POWERS_TO_PLOT = [3, 4, 5]

# Colors for Powers
COLORS = {3: "blue", 4: "green", 5: "red"}

def load_paired_cost_data():
    """Pairs Global vs Spatial costs to calculate % Savings."""
    grouped_data = {}
    
    for folder in DATA_FOLDERS:
        if not folder.exists(): continue
        files = list(folder.rglob("*_metrics.json"))
        
        for f in files:
            try:
                with open(f, 'r') as file:
                    content = json.load(file)
                    
                    # 1. Parse Metadata
                    match = re.search(r"_P(\d+)_", f.name)
                    power = int(match.group(1)) if match else 0
                    if power not in POWERS_TO_PLOT: continue
                    
                    topo = f.parent.name
                    if topo not in TOPOLOGIES: continue
                    
                    policy = content.get("policy")
                    lam = content.get("lambda")
                    cost = content.get("avg_req_dist", 0) # E[c]

                    key = (topo, power, lam)
                    if key not in grouped_data: grouped_data[key] = {}
                    grouped_data[key][policy] = cost
            except: pass

    records = []
    for (topo, power, lam), policies in grouped_data.items():
        if "poKL" in policies and "spatialKL" in policies:
            global_c = policies["poKL"]
            spatial_c = policies["spatialKL"]
            
            if global_c > 0:
                # Formula: (Global - Spatial) / Global * 100
                savings = ((global_c - spatial_c) / global_c) * 100.0
                records.append({
                    "Topology": topo, "Power": power, 
                    "Lambda": lam, "Savings": savings
                })

    return pd.DataFrame(records)

def plot_savings(df):
    if df.empty:
        print("No paired data found.")
        return

    # Use a standard academic style if available
    plt.style.use('seaborn-v0_8-paper') # or 'ggplot'

    for topo in TOPOLOGIES:
        subset = df[df["Topology"] == topo].copy()
        if subset.empty: continue

        fig, ax = plt.subplots(figsize=(10, 7))

        for p in POWERS_TO_PLOT:
            data = subset[subset["Power"] == p].sort_values("Lambda")
            if data.empty: continue
            
            # Academic convention: labels should use 'd' for sampling power
            ax.plot(data["Lambda"], data["Savings"], 
                    marker='o', linestyle='-', linewidth=2, 
                    color=COLORS[p], label=fr"Sampling Choices $d = {p}$")

        # --- RIGOROUS ACADEMIC LABELLING ---
        # Title describes the metric and the specific topology
        ax.set_title(f"Relative Communication Efficiency Gains: {topo.capitalize()} Topology", 
                     fontsize=16, fontweight='bold')
        
        # X-axis: Uses 'Normalized' to indicate load is relative to capacity
        ax.set_xlabel(r"Normalized System Load ($\lambda$)", fontsize=14)
        
        # Y-axis: Uses the mathematical symbol 'sigma' defined in your report
        ax.set_ylabel(r"Communication Cost Savings $\sigma$ ($\%$)", fontsize=14)
        
        # Standardize the scale for comparative analysis
        ax.set_ylim(0, 100) 
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.05))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(10.0))
        
        # Visual styling for a professional paper
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.minorticks_on()
        ax.grid(which='major', linestyle='-', alpha=0.4, linewidth=0.8)
        ax.grid(which='minor', linestyle=':', alpha=0.2, linewidth=0.5)
        
        # Legend: Frame removed or made transparent for a cleaner look
        ax.legend(fontsize=12, frameon=True, loc='lower right')

        plt.tight_layout()
        plt.savefig(f"cost_savings_{topo}.png", dpi=300, bbox_inches="tight")
        print(f"Saved: cost_savings_{topo}.png")
if __name__ == "__main__":
    df = load_paired_cost_data()
    plot_savings(df)