#!/usr/bin/env python3

import os
import re
import csv
import subprocess
from pathlib import Path
import concurrent.futures

# Configuration
NETLIST_DIR = Path("netlists")
OUTPUT_CSV = "characterization_results.csv"

# The 4 measurements defined in generate_netlists.py
MEASURE_NAMES = [
    "cell_fall",
    "cell_rise",
    "rise_transition",
    "fall_transition"
]

def run_and_parse_simulation(sp_file: Path) -> dict:
    """
    Runs ngspice in batch mode for a single netlist and parses the .measure results.
    """
    # Invoke ngspice in batch mode
    # -b: batch mode, -r: rawfile (optional, we discard it here to save space)
    cmd = ["ngspice", "-b", str(sp_file)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout
    except FileNotFoundError:
        print("Error: ngspice is not installed or not in PATH.")
        return {}

    # Extract cell name, input transition, and load cap from the filename
    # Example filename: invx1_tin_0.0100ns_cl_0.0005pf.sp
    fname = sp_file.stem
    parts = fname.split("_")
    
    # Safely parse the filename assuming the format from generate_netlists.py
    try:
        cell_name = parts[0]
        tin_ns = float(parts[2].replace("ns", ""))
        cl_pf = float(parts[4].replace("pf", ""))
    except (IndexError, ValueError):
        cell_name, tin_ns, cl_pf = "unknown", 0.0, 0.0

    # Initialize data dictionary
    data = {
        "cell": cell_name,
        "tin_ns": tin_ns,
        "cl_pf": cl_pf,
    }
    for m in MEASURE_NAMES:
        data[m] = None  # Default to None in case simulation fails

    # Parse the ngspice text output using Regex
    # ngspice .measure output looks like: cell_fall =  1.23456e-10 targ=... trig=...
    for m in MEASURE_NAMES:
        # Look for the measurement name, an equals sign, and a floating-point number
        pattern = rf"{m}\s*=\s*([+\-]?[0-9]*\.?[0-9]+(?:[eE][+\-]?[0-9]+)?)"
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            # Convert from seconds to nanoseconds for easier reading
            val_seconds = float(match.group(1))
            data[m] = val_seconds * 1e9  
        else:
            print(f"Warning: Could not find measurement '{m}' in {fname}")

    return data

def main():
    if not NETLIST_DIR.exists():
        print(f"Error: Directory '{NETLIST_DIR}' not found. Run generate_netlists.py first.")
        return

    # Find all .sp files recursively
    sp_files = list(NETLIST_DIR.rglob("*.sp"))
    total_sims = len(sp_files)
    
    print(f"Found {total_sims} netlists. Starting ngspice simulations...")

    results = []
    
    # Use ProcessPoolExecutor to run simulations in parallel (much faster!)
    # Adjust max_workers if you want to limit CPU usage.
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        # Map the function to all netlists
        for i, data in enumerate(executor.map(run_and_parse_simulation, sp_files), 1):
            if data:
                results.append(data)
            
            # Print a progress update every 50 simulations
            if i % 50 == 0 or i == total_sims:
                print(f"Completed {i}/{total_sims} simulations...")

    # Write aggregated data to CSV
    if results:
        # Sort results by cell, then load cap, then input transition
        results.sort(key=lambda x: (x["cell"], x["cl_pf"], x["tin_ns"]))
        
        fieldnames = ["cell", "tin_ns", "cl_pf"] + MEASURE_NAMES
        
        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"\nSuccess! All data extracted and saved to {OUTPUT_CSV}")
    else:
        print("\nNo results were successfully parsed.")

if __name__ == "__main__":
    main()