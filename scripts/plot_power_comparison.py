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
POWERS_TO_PLOT = [3, 4, 5]  # The specific powers you asked for

# Plot Styling
STYLES = {
    # Power 3
    "poKL_P3":      {"color": "blue",      "marker": "o", "linestyle": "--", "label": "Global Po3"},
    "spatialKL_P3": {"color": "blue",      "marker": "s", "linestyle": "-",  "label": "Spatial Po3"},
    
    # Power 4
    "poKL_P4":      {"color": "green",     "marker": "o", "linestyle": "--", "label": "Global Po4"},
    "spatialKL_P4": {"color": "green",     "marker": "s", "linestyle": "-",  "label": "Spatial Po4"},
    
    # Power 5
    "poKL_P5":      {"color": "red",       "marker": "o", "linestyle": "--", "label": "Global Po5"},
    "spatialKL_P5": {"color": "red",       "marker": "s", "linestyle": "-",  "label": "Spatial Po5"},
}

def load_data():
    data = []
    # Recursively find all json files
    files = sorted(RESULTS_DIR.rglob("*_metrics.json"))
    
    if not files:
        print(f"No results found in {RESULTS_DIR}")
        return pd.DataFrame()

    print(f"Loading {len(files)} files...")
    
    # Regex to extract info from filename if needed, 
    # but we can rely mostly on JSON content + folder name.
    
    for f in files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                
                # Extract Power (P) from the tag or filename
                # Filename format: ..._P3_...
                match = re.search(r"_P(\d+)_", f.name)
                power = int(match.group(1)) if match else 0
                
                if power not in POWERS_TO_PLOT:
                    continue

                topo = f.parent.name # 'grid' or 'cycle'
                
                data.append({
                    "Topology": topo,
                    "Policy": content.get("policy"),
                    "Power": power,
                    "Lambda": content.get("lambda"),
                    "E_Q": content.get("mean_Q", 0),      # E[Q]
                    "E_R": content.get("mean_W", 0),      # E[R] (Response Time)
                    "E_c": content.get("avg_req_dist", 0) # E[c] (Cost)
                })
        except Exception as e:
            pass # Skip broken files

    return pd.DataFrame(data)

def plot_metric(df, topo, metric_col, ylabel, title_suffix, filename_suffix):
    subset = df[df["Topology"] == topo].copy()
    if subset.empty: return

    plt.figure(figsize=(10, 7))
    
    # Plot lines for each Power + Policy combo
    for power in POWERS_TO_PLOT:
        for policy in ["poKL", "spatialKL"]:
            # Filter
            line_data = subset[
                (subset["Power"] == power) & 
                (subset["Policy"] == policy)
            ].sort_values("Lambda")
            
            if line_data.empty: continue
            
            # Style key
            style_key = f"{policy}_P{power}"
            style = STYLES.get(style_key, {})
            
            plt.plot(line_data["Lambda"], line_data[metric_col],
                     color=style.get("color"),
                     marker=style.get("marker"),
                     linestyle=style.get("linestyle"),
                     linewidth=2,
                     label=style.get("label"),
                     alpha=0.8)

    plt.title(f"{title_suffix} - {topo.capitalize()}", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    
    out_path = RESULTS_DIR / topo / f"combined_{filename_suffix}_{topo}.png"
    plt.savefig(out_path, dpi=300)
    print(f"Saved: {out_path}")
    plt.close()

def main():
    df = load_data()
    if df.empty: return

    for topo in TOPOLOGIES:
        print(f"\nGenerating Combined Plots for {topo.upper()}...")
        
        # 1. E[Q] Plot
        plot_metric(df, topo, "E_Q", 
                    "Mean Queue Length ($E[Q]$)", 
                    "Queue Length Comparison (Po3, Po4, Po5)", 
                    "EQ_comparison")
        
        # 2. E[R] Plot
        plot_metric(df, topo, "E_R", 
                    "Mean Response Time ($E[R]$)", 
                    "Response Time Comparison (Po3, Po4, Po5)", 
                    "ER_comparison")
        
        # 3. E[c] Plot
        plot_metric(df, topo, "E_c", 
                    "Avg L1 Distance ($E[c]$)", 
                    "Communication Cost Comparison (Po3, Po4, Po5)", 
                    "Ec_comparison")

if __name__ == "__main__":
    main()