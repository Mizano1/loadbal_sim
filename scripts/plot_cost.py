import matplotlib.pyplot as plt
import json
import pandas as pd
from pathlib import Path
import sys

# Update this path if your results are elsewhere
RESULTS_DIR = Path("experiments_10_12_2025/results_large_scale") 

def plot_cost_vs_lambda():
    json_files = sorted(RESULTS_DIR.glob("*_metrics.json"))
    
    if not json_files:
        print(f"No metrics.json files found in {RESULTS_DIR}")
        return

    data = []
    print(f"Found {len(json_files)} files. Parsing...")

    for f in json_files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                # 'avg_req_dist' is your E[c]
                if "avg_req_dist" in content:
                    data.append({
                        "Policy": content.get("policy", "Unknown"),
                        "Lambda": content.get("lambda", 0.0),
                        "Cost": content["avg_req_dist"]
                    })
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    if not data:
        print("No valid data found.")
        return

    df = pd.DataFrame(data)
    df = df.sort_values("Lambda")

    plt.figure(figsize=(10, 6))
    
    # Plot a line for each policy
    for pol in df["Policy"].unique():
        subset = df[df["Policy"] == pol]
        subset = subset.sort_values("Lambda")
        
        plt.plot(subset["Lambda"], subset["Cost"], 
                 marker='s', linewidth=2, label=pol)

    plt.title("Expected Communication Cost ($E[c]$)", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel("Avg Distance per Job ($E[c]$)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    output_file = RESULTS_DIR / "plot_expected_cost.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")

if __name__ == "__main__":
    plot_cost_vs_lambda()