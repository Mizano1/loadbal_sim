import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import json
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
# Add ALL folders where your data might be
DATA_FOLDERS = [
    Path("results_all_topologies"),  # Folder with Po2 data
    Path("results_topology_sweep"),  # Folder with Po3, P4, P5 data
    Path("grid_remake"),             # Check here too just in case
]

# We only want to plot E[R] for these topologies
TOPOLOGIES = ["grid", "cycle", "cluster"]

# Powers to include
POWERS_TO_PLOT = [2, 3, 4, 5]

# Style Definitions
STYLES = {
    # Power 2 (Baseline) - Only Global exists
    "poKL_P2":      {"color": "black", "marker": "x", "linestyle": ":",  "label": "Global Po2 (Baseline)"},
    
    # Power 3
    "poKL_P3":      {"color": "blue",  "marker": "o", "linestyle": "--", "label": "Global Po3"},
    "spatialKL_P3": {"color": "blue",  "marker": "s", "linestyle": "-",  "label": "Spatial Po3"},
    
    # Power 4
    "poKL_P4":      {"color": "green", "marker": "o", "linestyle": "--", "label": "Global Po4"},
    "spatialKL_P4": {"color": "green", "marker": "s", "linestyle": "-",  "label": "Spatial Po4"},
    
    # Power 5
    "poKL_P5":      {"color": "red",   "marker": "o", "linestyle": "--", "label": "Global Po5"},
    "spatialKL_P5": {"color": "red",   "marker": "s", "linestyle": "-",  "label": "Spatial Po5"},
}

def load_data():
    """Scans all folders and loads relevant JSON metrics."""
    data = []
    seen_files = set() # To avoid duplicates if folders overlap

    print("Scanning directories...")
    
    for folder in DATA_FOLDERS:
        if not folder.exists():
            print(f"  [Skipping] {folder} not found.")
            continue
            
        # Find all json files recursively
        files = list(folder.rglob("*_metrics.json"))
        print(f"  Found {len(files)} files in {folder}")
        
        for f in files:
            if f.name in seen_files: continue
            seen_files.add(f.name)

            try:
                with open(f, 'r') as file:
                    content = json.load(file)
                    
                    # 1. Get Power
                    match = re.search(r"_P(\d+)_", f.name)
                    power = int(match.group(1)) if match else 0
                    if power not in POWERS_TO_PLOT: continue

                    # 2. Get Topology
                    # Try getting it from the folder structure first
                    topo = f.parent.name
                    if topo not in TOPOLOGIES:
                        # Fallback: check filename
                        if "grid" in f.name: topo = "grid"
                        elif "cycle" in f.name: topo = "cycle"
                        elif "cluster" in f.name: topo = "cluster"
                        else: continue # Unknown topology

                    # 3. Get Policy
                    policy = content.get("policy")
                    
                    # FILTER: If Power 2, only accept 'poKL' (Global)
                    if power == 2 and policy != "poKL":
                        continue 

                    data.append({
                        "Topology": topo,
                        "Policy": policy,
                        "Power": power,
                        "Lambda": content.get("lambda"),
                        "E_R": content.get("mean_W", 0)
                    })
            except Exception as e:
                pass

    return pd.DataFrame(data)

def plot_consolidated_er(df):
    if df.empty:
        print("No data found! Check your folder paths.")
        return

    print("\nGenerating Consolidated Plots...")
    
    # Create an output folder for these specific plots
    out_dir = Path("final_combined_plots")
    out_dir.mkdir(exist_ok=True)

    for topo in TOPOLOGIES:
        subset = df[df["Topology"] == topo].copy()
        if subset.empty: continue

        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Sort by Power so the legend order is logical (2, 3, 4, 5)
        for power in sorted(POWERS_TO_PLOT):
            # For Power 2, we only look for 'poKL'
            policies = ["poKL"] if power == 2 else ["poKL", "spatialKL"]
            
            for policy in policies:
                line_data = subset[
                    (subset["Power"] == power) & 
                    (subset["Policy"] == policy)
                ].sort_values("Lambda")
                
                if line_data.empty: continue

                # Get Style
                style_key = f"{policy}_P{power}"
                style = STYLES.get(style_key, {})
                
                ax.plot(line_data["Lambda"], line_data["E_R"],
                        color=style.get("color", "black"),
                        marker=style.get("marker", "o"),
                        linestyle=style.get("linestyle", "-"),
                        linewidth=2,
                        label=style.get("label", f"{policy} {power}"),
                        alpha=0.8)

        # Formatting
        ax.set_title(f"Mean Response Time Comparison - {topo.capitalize()}", fontsize=14)
        ax.set_xlabel(r"System Load ($\lambda$)", fontsize=12)
        ax.set_ylabel(r"Mean Response Time ($E[R]$)", fontsize=12)
        
        ax.set_ylim(bottom=0)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.05))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
        
        ax.minorticks_on()
        ax.grid(which='major', linestyle='--', linewidth='0.5', color='gray', alpha=0.5)
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.2)
        
        ax.legend()
        
        save_path = out_dir / f"consolidated_ER_{topo}.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Saved: {save_path}")
        plt.close(fig)

if __name__ == "__main__":
    df = load_data()
    plot_consolidated_er(df)