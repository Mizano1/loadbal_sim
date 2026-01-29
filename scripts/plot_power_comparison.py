import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # <--- Added for fixed intervals
import pandas as pd
import json
import re
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
RESULTS_DIR = Path("grid_remake")
#TOPOLOGIES = ["grid", "cycle"]
#TOPOLOGIES = ["cluster"]
TOPOLOGIES = ["grid"]
POWERS_TO_PLOT = [3, 4, 5]

# Style for Policies (Lines)
STYLES = {
    "poKL_P3":      {"color": "blue",      "marker": "o", "linestyle": "--", "label": "Global Po3"},
    "spatialKL_P3": {"color": "blue",      "marker": "s", "linestyle": "-",  "label": "Spatial Po3"},
    "poKL_P4":      {"color": "green",     "marker": "o", "linestyle": "--", "label": "Global Po4"},
    "spatialKL_P4": {"color": "green",     "marker": "s", "linestyle": "-",  "label": "Spatial Po4"},
    "poKL_P5":      {"color": "red",       "marker": "o", "linestyle": "--", "label": "Global Po5"},
    "spatialKL_P5": {"color": "red",       "marker": "s", "linestyle": "-",  "label": "Spatial Po5"},
}

# Style for Distribution Distance (One line per Power pair)
DIST_STYLES = {
    3: {"color": "blue",  "marker": "^", "linestyle": "-", "label": "Power 3 Divergence"},
    4: {"color": "green", "marker": "^", "linestyle": "-", "label": "Power 4 Divergence"},
    5: {"color": "red",   "marker": "^", "linestyle": "-", "label": "Power 5 Divergence"},
}

def load_metrics():
    """Loads E[Q], E[R], E[c] from JSON files."""
    data = []
    files = sorted(RESULTS_DIR.rglob("*_metrics.json"))
    print(f"Loading {len(files)} metric files...")
    
    for f in files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                match = re.search(r"_P(\d+)_", f.name)
                power = int(match.group(1)) if match else 0
                
                if power not in POWERS_TO_PLOT: continue

                # Fallback for topology detection
                topo = f.parent.name
                if topo not in TOPOLOGIES:
                    if "grid" in f.name: topo = "grid"
                    elif "cycle" in f.name: topo = "cycle"

                data.append({
                    "Topology": topo,
                    "Policy": content.get("policy"),
                    "Power": power,
                    "Lambda": content.get("lambda"),
                    "E_Q": content.get("mean_Q", 0),
                    "E_R": content.get("mean_W", 0),
                    "E_c": content.get("avg_req_dist", 0) 
                })
        except: pass
    return pd.DataFrame(data)

def calculate_distribution_l1():
    """Loads Histograms and calculates L1 Distance between policies."""
    results = []
    files = sorted(RESULTS_DIR.rglob("*_hist.csv"))
    print(f"Loading {len(files)} histogram files for L1 calc...")

    # Group files: groups[(topo, power, lambda)][policy] = filepath
    groups = {}
    
    for f in files:
        try:
            match = re.search(r"_P(\d+)_", f.name)
            power = int(match.group(1)) if match else 0
            if power not in POWERS_TO_PLOT: continue

            # Extract Lambda roughly from filename or assume grouping
            lam_match = re.search(r"lam(\d+\.\d+)", f.name)
            lam = float(lam_match.group(1)) if lam_match else 0.0

            # Determine Policy
            policy = "poKL" if "poKL" in f.name else "spatialKL"
            
            # Determine Topo
            topo = f.parent.name
            if topo not in TOPOLOGIES:
                if "grid" in f.name: topo = "grid"
                elif "cycle" in f.name: topo = "cycle"

            key = (topo, power, lam)
            if key not in groups: groups[key] = {}
            groups[key][policy] = f
        except: pass

    # Calculate L1 for each group
    for (topo, power, lam), pair in groups.items():
        if "poKL" in pair and "spatialKL" in pair:
            try:
                df1 = pd.read_csv(pair["poKL"])
                df2 = pd.read_csv(pair["spatialKL"])
                
                # Standardize columns
                df1.columns = [c.strip().replace("# ", "") for c in df1.columns]
                df2.columns = [c.strip().replace("# ", "") for c in df2.columns]
                
                # Align by QueueLength
                s1 = df1.set_index("QueueLength")["Probability"]
                s2 = df2.set_index("QueueLength")["Probability"]
                
                # Align and Fill 0
                df_compare = pd.DataFrame({'p1': s1, 'p2': s2}).fillna(0.0)
                
                # L1 Distance
                l1_dist = (df_compare['p1'] - df_compare['p2']).abs().sum()
                
                results.append({
                    "Topology": topo,
                    "Power": power,
                    "Lambda": lam,
                    "L1_Dist": l1_dist
                })
            except Exception as e:
                pass
                
    return pd.DataFrame(results)

def plot_standard_metric(df, topo, metric_col, ylabel, title_suffix, filename_suffix):
    """Plots E[Q], E[R], E[c] with formatted axes."""
    subset = df[df["Topology"] == topo].copy()
    if subset.empty: return

    # Use 'subplots' to get the axis object explicitly
    fig, ax = plt.subplots(figsize=(10, 7))

    max_val = 0 # Track max value for scaling logic

    for power in POWERS_TO_PLOT:
        for policy in ["poKL", "spatialKL"]:
            line_data = subset[(subset["Power"] == power) & (subset["Policy"] == policy)].sort_values("Lambda")
            if line_data.empty: continue
            
            # Update max tracking
            current_max = line_data[metric_col].max()
            if current_max > max_val: max_val = current_max

            style = STYLES.get(f"{policy}_P{power}", {})
            ax.plot(line_data["Lambda"], line_data[metric_col],
                      color=style.get("color"), marker=style.get("marker"),
                      linestyle=style.get("linestyle"), linewidth=2,
                      label=style.get("label"), alpha=0.8)

    # --- AXIS FORMATTING ---
    ax.set_title(f"{title_suffix} - {topo.capitalize()}", fontsize=14)
    ax.set_xlabel(r"System Load ($\lambda$)", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    
    # 1. Start Y-axis at 0
    ax.set_ylim(bottom=0)

    # 2. X-Axis Ticks (Every 0.05)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.05))

    # 3. Y-Axis Ticks (Dynamic based on metric)
    if metric_col == "E_c":
        # Cost often has a much larger range (e.g. 80 for Cycle, 5 for Grid)
        if max_val > 20:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(10.0)) # Cycle cost
        else:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1.0))  # Grid cost
    else:
        # Response Time / Queue Length (usually small, < 10)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))

    # 4. Grid Lines
    ax.minorticks_on()
    ax.grid(which='major', linestyle='--', linewidth='0.5', color='gray', alpha=0.5)
    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.2)
    
    ax.legend()
    
    out_dir = RESULTS_DIR / topo
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"combined_{filename_suffix}_{topo}.png", dpi=300)
    plt.close(fig)

def plot_distribution_l1(df, topo):
    """Plots the Statistical L1 Distance with formatted axes."""
    subset = df[df["Topology"] == topo].copy()
    if subset.empty: return

    fig, ax = plt.subplots(figsize=(10, 7))

    for power in POWERS_TO_PLOT:
        line_data = subset[subset["Power"] == power].sort_values("Lambda")
        if line_data.empty: continue
        
        style = DIST_STYLES.get(power, {})
        ax.plot(line_data["Lambda"], line_data["L1_Dist"],
                  color=style.get("color"), marker=style.get("marker"),
                  linestyle=style.get("linestyle"), linewidth=2,
                  label=style.get("label"), alpha=0.8)

    # --- AXIS FORMATTING ---
    ax.set_title(f"Distribution Divergence (L1) - {topo.capitalize()}", fontsize=14)
    ax.set_xlabel(r"System Load ($\lambda$)", fontsize=12)
    ax.set_ylabel(r"L1 Distance ($\sum |P_{po} - P_{sp}|$)", fontsize=12)
    
    # 1. Start Y-axis at 0
    ax.set_ylim(bottom=0)

    # 2. Ticks
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.05))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.02)) # Specific interval for L1

    # 3. Grid
    ax.minorticks_on()
    ax.grid(which='major', linestyle='--', linewidth='0.5', color='gray', alpha=0.5)
    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.2)
    
    ax.legend()
    
    out_dir = RESULTS_DIR / topo
    fig.savefig(out_dir / f"combined_dist_l1_{topo}.png", dpi=300)
    plt.close(fig)

def main():
    print("--- Generating Summary Plots ---")
    
    # 1. Standard Metrics
    df_metrics = load_metrics()
    if not df_metrics.empty:
        for topo in TOPOLOGIES:
            print(f"Plotting Standard Metrics for {topo}...")
            # E[Q]
            plot_standard_metric(df_metrics, topo, "E_Q", 
                               r"Mean Queue Length ($E[Q]$)", 
                               "Queue Length Comparison", "EQ")
            # E[R]
            plot_standard_metric(df_metrics, topo, "E_R", 
                               r"Mean Response Time ($E[R]$)", 
                               "Response Time Comparison", "ER")
            # E[c]
            plot_standard_metric(df_metrics, topo, "E_c", 
                               r"Avg Hop Distance ($E[c]$)", 
                               "Communication Cost Comparison", "Ec")

    # 2. Distribution L1 Distance
    df_l1 = calculate_distribution_l1()
    if not df_l1.empty:
        for topo in TOPOLOGIES:
            print(f"Plotting Distribution L1 for {topo}...")
            plot_distribution_l1(df_l1, topo)

    print("Done. Check the topology folders.")

if __name__ == "__main__":
    main()