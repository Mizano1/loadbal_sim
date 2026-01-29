import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import json
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
RESULTS_DIR = Path("results_cluster_sweep")
TOPOLOGIES = ["cluster"]
#TOPOLOGIES = ["grid", "cycle"]
POWERS_TO_PLOT = [3, 4, 5]

# Colors for the Powers
COLORS = {
    3: "blue",
    4: "green",
    5: "red"
}

def load_paired_data():
    """
    Loads data and pairs Global vs Spatial to calculate % Error.
    """
    records = []
    files = sorted(RESULTS_DIR.rglob("*_metrics.json"))
    
    # We need to group files by: (Topology, Power, Lambda)
    # Dictionary structure: grouped_data[(topo, power, lam)][policy] = mean_W
    grouped_data = {}

    print(f"Scanning {len(files)} files...")

    for f in files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                
                # 1. Parse Metadata
                topo = f.parent.name
                if topo not in TOPOLOGIES: continue
                
                policy = content.get("policy") # "poKL" or "spatialKL"
                lam = content.get("lambda")
                mean_w = content.get("mean_W", 0)

                # Extract Power from filename (e.g., _P3_)
                match = re.search(r"_P(\d+)_", f.name)
                power = int(match.group(1)) if match else 0
                if power not in POWERS_TO_PLOT: continue

                # 2. Grouping
                key = (topo, power, lam)
                if key not in grouped_data: grouped_data[key] = {}
                
                grouped_data[key][policy] = mean_w
                
        except Exception:
            pass

    # 3. Calculate Error Percentage
    for (topo, power, lam), policies in grouped_data.items():
        if "poKL" in policies and "spatialKL" in policies:
            global_w = policies["poKL"]
            spatial_w = policies["spatialKL"]
            
            if global_w > 0:
                # Formula: (Spatial - Global) / Global * 100
                pct_error = ((spatial_w - global_w) / global_w) * 100.0
                
                records.append({
                    "Topology": topo,
                    "Power": power,
                    "Lambda": lam,
                    "Error_Pct": pct_error
                })

    return pd.DataFrame(records)

def plot_error_percentage(df):
    if df.empty:
        print("No paired data found to calculate error.")
        return

    print("Generating Error Percentage Plots...")

    for topo in TOPOLOGIES:
        subset = df[df["Topology"] == topo]
        if subset.empty: continue

        fig, ax = plt.subplots(figsize=(10, 7))

        for power in POWERS_TO_PLOT:
            data = subset[subset["Power"] == power].sort_values("Lambda")
            if data.empty: continue
            
            c = COLORS.get(power, "black")
            
            ax.plot(data["Lambda"], data["Error_Pct"], 
                    marker='o', linestyle='-', linewidth=2, 
                    color=c, label=f"Power {power} Error")

        # --- AXIS FORMATTING ---
        ax.set_title(f"Response Time Error % (Spatial vs Global) - {topo.capitalize()}", fontsize=14)
        ax.set_xlabel(r"System Load ($\lambda$)", fontsize=12)
        ax.set_ylabel(r"% Increase in Response Time", fontsize=12)
        
        # Start Y at 0 (or lower if spatial beats global, which is rare)
        ax.set_ylim(bottom=0)
        
        # Ticks
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.05))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1.0)) # 1% intervals
        
        # Grid
        ax.minorticks_on()
        ax.grid(which='major', linestyle='--', linewidth='0.5', color='gray', alpha=0.5)
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.2)
        
        ax.legend()

        out_path = RESULTS_DIR / topo / f"combined_error_pct_{topo}.png"
        fig.savefig(out_path, dpi=300)
        print(f"Saved: {out_path}")
        plt.close(fig)

if __name__ == "__main__":
    df = load_paired_data()
    plot_error_percentage(df)