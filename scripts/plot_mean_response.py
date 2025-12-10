import matplotlib.pyplot as plt
import json
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path("experiments_10_12_2025/results_large_scale") 

def plot_waiting_time():
    json_files = sorted(RESULTS_DIR.glob("*_metrics.json"))
    data = []

    for f in json_files:
        try:
            with open(f, 'r') as file:
                content = json.load(file)
                
                # 1. Get E[R] (mean_W in your code)
                e_r = content.get("mean_W", 0.0)
                
                # 2. Get Service Rate (mu)
                mu = content.get("mu", 1.0)
                
                # 3. Calculate E[W] = E[R] - 1/mu
                avg_service_time = 1.0 / mu if mu > 0 else 0
                e_w = e_r - avg_service_time
                
                # Safety check: E[W] theoretically can't be negative, 
                # but statistical noise in low-load sims might make it slightly < 0.
                if e_w < 0: e_w = 0 

                data.append({
                    "Policy": content.get("policy", "Unknown"),
                    "Lambda": content.get("lambda", 0.0),
                    "WaitingTime": e_w
                })
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    df = pd.DataFrame(data)
    df = df.sort_values("Lambda")

    plt.figure(figsize=(10, 6))
    for pol in df["Policy"].unique():
        subset = df[df["Policy"] == pol].sort_values("Lambda")
        plt.plot(subset["Lambda"], subset["WaitingTime"], 
                 marker='o', linewidth=2, label=pol)

    plt.title("Expected Waiting Time ($E[W]$) vs. Lambda", fontsize=14)
    plt.xlabel("System Load ($\lambda$)", fontsize=12)
    plt.ylabel("Mean Waiting Time ($E[W]$)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.savefig(RESULTS_DIR / "plot_waiting_time.png", dpi=300, bbox_inches="tight")
    print(f"Plot saved to {RESULTS_DIR}/plot_waiting_time.png")

if __name__ == "__main__":
    plot_waiting_time()