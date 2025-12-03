import matplotlib.pyplot as plt
import json
import pandas as pd
from pathlib import Path
import sys

RESULTS_DIR = Path("experiments_3-12-2025/lambda_by_response_time")

def plot_mean_response_vs_lambda():
    # Find all JSON metric files
    json_files = sorted(RESULTS_DIR.glob("*_metrics.json"))
    
    if not json_files:
        print(f"No *_metrics.json files found in {RESULTS_DIR}.")
        return

    data = []

    print(f"Found {len(json_files)} metric files. Parsing...")

    for f in json_files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                
                # Extract relevant fields
                policy = content.get("policy", "Unknown")
                lam = content.get("lambda", 0.0)
                mean_w = content.get("mean_W", 0.0)
                
                data.append({
                    "Policy": policy,
                    "Lambda": lam,
                    "Mean_Response_Time": mean_w
                })
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    if not data:
        print("No valid data found.")
        return

    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Sort by Lambda
    df = df.sort_values("Lambda")

    # Plotting
    plt.figure(figsize=(10, 6))
    
    policies = df["Policy"].unique()
    
    for pol in policies:
        subset = df[df["Policy"] == pol]
        plt.plot(subset["Lambda"], subset["Mean_Response_Time"], 
                 marker='o', linewidth=2, label=pol)

    plt.title("Mean Response Time vs. Lambda", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel("Mean Response Time ($E[W]$)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    output_file = RESULTS_DIR / "plot_mean_response_json.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")

if __name__ == "__main__":
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} does not exist.")
        sys.exit(1)
        
    plot_mean_response_vs_lambda()