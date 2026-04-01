#!/usr/bin/env python3

import os
import re
import csv
import subprocess
from pathlib import Path
import concurrent.futures


NETLIST_DIR = Path("netlists")
OUTPUT_CSV = "characterization_results.csv"


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
    cmd = ["ngspice", "-b", str(sp_file)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout
    except FileNotFoundError:
        print("Error: ngspice is not installed or not in PATH.")
        return {}

    # Extract cell name, input transition, and load cap from the filename
    fname = sp_file.stem
    parts = fname.split("_")
    
    # Parse the filename assuming the format from generate_netlists.py
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
        data[m] = None

    # Parse the ngspice text output
    for m in MEASURE_NAMES:

        pattern = rf"{m}\s*=\s*([+\-]?[0-9]*\.?[0-9]+(?:[eE][+\-]?[0-9]+)?)"
        match = re.search(pattern, output, re.IGNORECASE)
        if match:

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
    
    # ProcessPoolExecutor to run simulations in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        for i, data in enumerate(executor.map(run_and_parse_simulation, sp_files), 1):
            if data:
                results.append(data)
            
            if i % 50 == 0 or i == total_sims:
                print(f"Completed {i}/{total_sims} simulations...")

    # Write aggregated data to CSV
    if results:

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