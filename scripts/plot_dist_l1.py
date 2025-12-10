import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import re

RESULTS_DIR = Path("experiments_10_12_2025/results_large_scale")

def get_hist_data(file_path):
    """Reads CSV and returns {QueueLength: Probability} series."""
    try:
        df = pd.read_csv(file_path)
        # Clean potential whitespace in headers
        df.columns = [c.strip() for c in df.columns] 
        return df.set_index("QueueLength")["Probability"]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def calculate_distribution_distance():
    # Find all histogram files
    files = sorted(RESULTS_DIR.glob("*_hist.csv"))
    
    # Group files by Lambda
    # We expect filenames like: policy_cluster_n525_lam0.9500_...
    # We will group by 'lam0.XXXX'
    groups = {}
    pattern = re.compile(r"(?P<policy>[a-zA-Z]+)_.*_lam(?P<lam>0\.\d+)")

    for f in files:
        match = pattern.search(f.name)
        if match:
            pol = match.group("policy")
            lam = float(match.group("lam"))
            
            if lam not in groups: groups[lam] = {}
            groups[lam][pol] = f

    results = []
    
    # Compare poKL vs spatialKL for each Lambda
    for lam, pair in sorted(groups.items()):
        if 'poKL' in pair and 'spatialKL' in pair:
            print(f"Processing Lambda {lam}...")
            
            # 1. Load Distributions
            s1 = get_hist_data(pair['poKL'])
            s2 = get_hist_data(pair['spatialKL'])
            
            if s1 is None or s2 is None: continue

            # 2. Align DataFrames (fill missing queue lengths with 0)
            df = pd.DataFrame({'p1': s1, 'p2': s2}).fillna(0.0)
            
            # 3. Calculate L1 Distance: Sum |P1 - P2|
            l1_dist = (df['p1'] - df['p2']).abs().sum()
            
            results.append({"Lambda": lam, "L1_Distance": l1_dist})

    if not results:
        print("No matching pairs (poKL vs spatialKL) found.")
        return

    # Plotting
    df_res = pd.DataFrame(results).sort_values("Lambda")
    
    plt.figure(figsize=(8, 5))
    plt.plot(df_res["Lambda"], df_res["L1_Distance"], 
             marker='o', color='purple', linewidth=2)
    
    plt.title("Distribution Divergence: poKL vs spatialKL", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel("L1 Distance ($\sum |P_{po} - P_{sp}|$)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(bottom=0)
    
    out_file = RESULTS_DIR / "plot_distribution_l1.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    print(f"Saved plot to {out_file}")

if __name__ == "__main__":
    calculate_distribution_distance()