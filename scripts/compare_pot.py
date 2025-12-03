import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import sys

def calculate_theoretical_pot(rho, d, max_k=20):
    """Calculates theoretical P(Q=k) and E[Q]."""
    if d <= 1:
        # M/M/1 Case
        pdf = [(1-rho) * (rho**k) for k in range(max_k + 1)]
        expected_q = rho / (1 - rho)
        return pdf, expected_q
        
    p_ge_k = []
    # Super-exponential formula for d >= 2
    for k in range(max_k + 2):
        try:
            exponent = (d**k - 1) / (d - 1)
            if exponent > 500: # Overflow protection
                 val = 0.0
            else:
                 val = rho ** exponent
        except OverflowError:
            val = 0.0
        p_ge_k.append(val)
    
    pdf = []
    for k in range(max_k + 1):
        prob = p_ge_k[k] - p_ge_k[k+1]
        pdf.append(prob)
        
    expected_q = sum(p_ge_k[1:]) 
    return pdf, expected_q

def main():
    parser = argparse.ArgumentParser(description="Compare Simulated PoT vs Theory")
    parser.add_argument("csv_file", help="Path to the simulation histogram CSV file")
    parser.add_argument("--lambda_val", type=float, default=0.95, help="Lambda used")
    parser.add_argument("--mu_val", type=float, default=1.0, help="Mu used")
    parser.add_argument("--d_choices", type=int, default=2, help="d parameter")
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        print(f"Error: File {args.csv_file} not found.")
        return

    print(f"Loading {args.csv_file}...")

    try:
        df = pd.read_csv(args.csv_file)
        # Handle header variations
        if "QueueLength" not in df.columns:
             if df.shape[1] >= 2:
                 df.columns = ["QueueLength", "Probability"] + list(df.columns[2:])
        
        sim_k = df["QueueLength"].values
        sim_p = df["Probability"].values
        sim_mean_q = sum(sim_k * sim_p)

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Theoretical Calculation
    rho = args.lambda_val / args.mu_val
    d = args.d_choices
    
    max_k = int(max(sim_k)) if len(sim_k) > 0 else 10
    theo_pdf, theo_mean_q = calculate_theoretical_pot(rho, d=d, max_k=max_k + 5)
    
    # --- CRITICAL CHECK: P(Q=0) ---
    # Find Simulated P(Q=0)
    sim_p0 = 0.0
    if 0 in sim_k:
        idx_0 = list(sim_k).index(0)
        sim_p0 = sim_p[idx_0]
    
    # Theoretical P(Q=0) is simply 1 - rho (for d=1)
    # For d >= 2, it's calculated by the formula, but usually close to 1-rho.
    theo_p0 = theo_pdf[0]

    print("-" * 40)
    print(f"--- START VALUE CHECK (Target ~{1.0-rho:.2f}) ---")
    print(f"Simulated P(Q=0):   {sim_p0:.5f}")
    print(f"Theoretical P(Q=0): {theo_p0:.5f}")
    print("-" * 40)

    # Plotting
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot A: Distribution (Linear Scale)
    ax[0].plot(sim_k, sim_p, 'o-', linewidth=2, label=f"Simulated")
    ax[0].plot(range(len(theo_pdf)), theo_pdf, 'r--', label=f"Theory")
    
    ax[0].set_xlabel("Queue Length ($k$)")
    ax[0].set_ylabel("Probability $P(Q=k)$")
    ax[0].set_title(f"Queue Distribution ($\\rho={rho:.2f}, d={d}$)")
    ax[0].set_xlim(left=0, right=10)
    ax[0].set_ylim(bottom=0)
    ax[0].margins(x=0, y=0)
    ax[0].grid(True, alpha=0.4)
    ax[0].legend()

    # Plot B: Mean Comparison
    metrics = ['Simulated', 'Theoretical']
    values = [sim_mean_q, theo_mean_q]
    bars = ax[1].bar(metrics, values, color=['skyblue', 'salmon'], alpha=0.8, edgecolor='black', width=0.5)
    ax[1].set_ylabel("$E[Q]$")
    ax[1].set_title(f"Mean Queue Length")
    
    for bar in bars:
        height = bar.get_height()
        ax[1].text(bar.get_x() + bar.get_width()/2., height, f'{height:.4f}',
                   ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    output_img = f"comparison_pot_d{d}.png"
    plt.savefig(output_img)
    print(f"Plot saved to {output_img}")

if __name__ == "__main__":
    main()