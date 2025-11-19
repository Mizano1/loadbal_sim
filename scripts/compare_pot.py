import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import sys

def calculate_theoretical_pot(rho, max_k=20):
    """
    Calculates theoretical P(Q=k) and E[Q] for Power of 2 Choices (d=2).
    Formulas:
      P(Q >= k) = rho^(2^k - 1)
      P(Q = k) = P(Q >= k) - P(Q >= k+1)
    """
    p_ge_k = []
    # Calculate P(Q >= k) for k=0 to max_k+1
    for k in range(max_k + 2):
        # Exponent: 2^k - 1
        # Use safe power to avoid overflow for very large k (though prob becomes 0)
        try:
            exponent = (2**k) - 1
            if exponent > 1000: # Optimization: rho^1000 is effectively 0
                 val = 0.0
            else:
                 val = rho ** exponent
        except OverflowError:
            val = 0.0
        p_ge_k.append(val)
    
    # Calculate PDF: P(Q=k)
    pdf = []
    for k in range(max_k + 1):
        prob = p_ge_k[k] - p_ge_k[k+1]
        pdf.append(prob)
        
    # Calculate Theoretical E[Q]
    # E[Q] = sum_{k=1 to infinity} P(Q >= k)
    # We sum the tail probabilities P(Q >= k) starting from k=1
    expected_q = sum(p_ge_k[1:]) 
    
    return pdf, expected_q

def main():
    parser = argparse.ArgumentParser(description="Compare Simulated PoT vs Theory")
    parser.add_argument("csv_file", help="Path to the simulation histogram CSV file")
    parser.add_argument("--lambda_val", type=float, default=0.95, help="Lambda value used in simulation")
    parser.add_argument("--mu_val", type=float, default=1.0, help="Mu value used in simulation")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: File {args.csv_file} not found.")
        return

    print(f"Loading data from {args.csv_file}...")

    # 1. Load Simulation Data
    try:
        # Read CSV, handling potential header variations
        df = pd.read_csv(args.csv_file)
        
        # Check if columns exist, if not, try to infer or fallback
        # Your C++ likely writes "QueueLength,Probability"
        if "QueueLength" not in df.columns or "Probability" not in df.columns:
             # Fallback: maybe it has lowercase headers or no headers?
             # Let's try to standardizing headers if they match shape
             if df.shape[1] >= 2:
                 df.columns = ["QueueLength", "Probability"] + list(df.columns[2:])
             else:
                 print("Error: CSV format not recognized. Expected 'QueueLength,Probability'")
                 return
                 
        sim_k = df["QueueLength"].values
        sim_p = df["Probability"].values
        
        # Calculate Simulated Mean from Histogram
        sim_mean_q = sum(sim_k * sim_p)
        print(f"Simulated Mean (from Hist): {sim_mean_q:.4f}")

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Calculate Theoretical Data
    rho = args.lambda_val / args.mu_val
    print(f"Calculating theory for Rho = {rho}...")
    
    max_k_sim = int(max(sim_k)) if len(sim_k) > 0 else 10
    theo_pdf, theo_mean_q = calculate_theoretical_pot(rho, max_k=max_k_sim + 2)
    
    # 3. Plotting
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot A: Probability Distribution (PDF)
    # We'll perform a bar plot for simulation and a line/marker for theory
    width = 0.6
    ax[0].plot(
    sim_k,
    sim_p,
    marker="o",
    linestyle="-",
    linewidth=2,
    color="#1f77b4",
    label="Simulated PoT",
)
    
    # Align theory plot with bars
    theo_x = range(len(theo_pdf))
    ax[0].plot(theo_x, theo_pdf, 'ro--', label='Theoretical PoT ($d=2$)', markersize=6, linewidth=2)
    
    ax[0].set_xlabel("Queue Length ($k$)")
    ax[0].set_ylabel("Probability $P(Q=k)$")
    ax[0].set_title(f"Queue Length Distribution ($\\lambda={args.lambda_val}$)")


    ax[0].legend()
    ax[0].grid(True, which="both", ls="--", alpha=0.4)

    # Plot B: Mean Queue Length Comparison (Visual Bar)
    metrics = ['Simulated', 'Theoretical']
    values = [sim_mean_q, theo_mean_q]
    colors = ['skyblue', 'salmon']
    
    bars = ax[1].bar(metrics, values, color=colors, alpha=0.8, edgecolor='black', width=0.5)
    ax[1].set_ylabel("Mean Queue Length $E[Q]$")
    ax[1].set_title(f"Mean Queue Length Comparison")
    ax[1].grid(axis='y', linestyle='--', alpha=0.4)
    
    # Add text labels on bars
    for bar in bars:
        height = bar.get_height()
        ax[1].text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    
    output_img = "comparison_pot.png"
    plt.savefig(output_img)
    print(f"Comparison plot saved to {output_img}")
    print("-" * 30)
    print(f"Simulated E[Q]:   {sim_mean_q:.5f}")
    print(f"Theoretical E[Q]: {theo_mean_q:.5f}")
    print("-" * 30)
    
    # plt.show() # Uncomment if running locally with display

if __name__ == "__main__":
    main()