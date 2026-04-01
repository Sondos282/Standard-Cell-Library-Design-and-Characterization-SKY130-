#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CSV_FILE = "characterization_results.csv"

def plot_inverter_delay():
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"Error: {CSV_FILE} not found. Ensure your simulations have finished.")
        return

    # Filter for the inverter family
    inv_cells = ['invx1', 'invx2', 'invx4', 'invx8']
    
    # Filter for the fixed input transition (tin = 0.1225ns)
    plot_data = df[(df['cell'].isin(inv_cells)) & (np.isclose(df['tin_ns'], 0.1225))]
    
    if plot_data.empty:
        print("Error: No data found for inverters at tin=0.1225ns. Check your CSV.")
        return

    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Loop through each inverter and plot its delay curve
    for cell in inv_cells:
        cell_data = plot_data[plot_data['cell'] == cell].sort_values('cl_pf')
        
        if cell_data.empty:
            continue
            
        # Calculate Average Delay: (cell_rise + cell_fall) / 2
        avg_delay_ps = ((cell_data['cell_rise'] + cell_data['cell_fall']) / 2) * 1000
        
        # Plot Load Capacitance vs Average Delay
        plt.plot(cell_data['cl_pf'], avg_delay_ps, marker='o', linewidth=2, label=cell)
        

    plt.title("Delay vs. Load Capacitance for Inverter Family\n($t_{in}$ = 0.1225 ns)", fontsize=14, pad=15)
    plt.xlabel("Load Capacitance ($C_L$) [pF]", fontsize=12)
    plt.ylabel("Average Propagation Delay [ps]", fontsize=12)
    plt.grid(True, which="both", linestyle="--", alpha=0.7)
    plt.legend(title="Cell Type", fontsize=11)
    plt.tight_layout()
    

    output_filename = "delay_vs_load_inv.png"
    plt.savefig(output_filename, dpi=300)
    print(f"Success! Plot saved as '{output_filename}'")

if __name__ == "__main__":
    plot_inverter_delay()
