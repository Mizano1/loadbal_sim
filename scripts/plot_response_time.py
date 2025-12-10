import matplotlib.pyplot as plt
import json
import pandas as pd
from pathlib import Path
import sys

# Update this path to your results folder (e.g., results_large_scale)
RESULTS_DIR = Path("experiments_10_12_2025/results_large_scale") 

def plot_response_time():
    # Find all JSON metric files
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
                
                # 'mean_W' in your code is actually E[R] (Response Time)
                if "mean_W" in content:
                    data.append({
                        "Policy": content.get("policy", "Unknown"),
                        "Lambda": content.get("lambda", 0.0),
                        "ResponseTime": content["mean_W"]
                    })
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    if not data:
        print("No valid data found.")
        return

    # Create DataFrame
    df = pd.DataFrame(data)
    df = df.sort_values("Lambda")

    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Get unique policies to plot separate lines
    policies = df["Policy"].unique()
    
    for pol in policies:
        subset = df[df["Policy"] == pol]
        subset = subset.sort_values("Lambda")
        
        plt.plot(subset["Lambda"], subset["ResponseTime"], 
                 marker='o', linewidth=2, label=pol)

    plt.title("Expected Response Time ($E[R]$) vs. Lambda", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel("Mean Response Time ($E[R]$)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    output_file = RESULTS_DIR / "plot_response_time.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")

if __name__ == "__main__":
    plot_response_time()