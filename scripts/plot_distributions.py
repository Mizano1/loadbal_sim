import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import sys
from matplotlib.ticker import MultipleLocator
# Directory containing results
RESULTS_DIR = Path("experiments_3-12-2025/cluster_test_d=3")

def plot_distributions():
    # Find all histogram files
    hist_files = sorted(RESULTS_DIR.glob("*_hist.csv"))
    
    if not hist_files:
        print(f"No *_hist.csv files found in {RESULTS_DIR}. Run simulations first.")
        return

    plt.figure(figsize=(10, 6))
    
    # Loop through each file and plot
    for file_path in hist_files:
        try:
            # Parse filename to get a label (e.g., "pot_cycle_n1000_lam0.95")
            label = file_path.stem.replace("_hist", "")
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Clean column names (remove leading spaces/comments)
            df.columns = [c.strip().replace("# ", "") for c in df.columns]
            
            if "QueueLength" not in df.columns or "Probability" not in df.columns:
                print(f"Skipping {file_path.name}: Unexpected columns {df.columns}")
                continue

            # Plot Line with Markers
            plt.plot(df["QueueLength"], df["Probability"], marker='o', linewidth=2, label=label)
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # Formatting
    plt.title("Queue Length Distribution Comparison", fontsize=14)
    plt.xlabel("Queue Length (k)", fontsize=12)
    plt.ylabel("Probability P(Q=k)", fontsize=12)
    # ---- AXES SETTINGS YOU WANT ----
    ax = plt.gca()

    # start at (0,0) with no extra margin
    ax.set_xlim(left=0, right=15)
    ax.set_ylim(bottom=0, top=0.5)      # or top=0.45 depending on your max prob
    ax.margins(x=0, y=0)

    # y-axis ticks: 0, 0.05, 0.10, ...
    ax.yaxis.set_major_locator(MultipleLocator(0.05))

    ax.grid(True, linestyle='--', alpha=0.7, which="both")

    plt.legend(fontsize=10)
    # Save
    output_file = RESULTS_DIR / "load_distribution_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Saved plot to {output_file}")

if __name__ == "__main__":
    if not RESULTS_DIR.exists():
        print(f"Error: {RESULTS_DIR} does not exist.")
        sys.exit(1)
    
    plot_distributions()