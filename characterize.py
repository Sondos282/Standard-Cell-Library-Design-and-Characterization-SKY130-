import re
import csv
import subprocess
import numpy as np
import json
from pathlib import Path

SKY130_LIB   = "/home/hab20034/work/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice"
CELLS_SP     = "/home/hab20034/DD2 Project/Standard-Cell-Library-Design-and-Characterization-SKY130-/cells.sp"
NETLISTS_DIR = Path("/home/hab20034/DD2 Project/Standard-Cell-Library-Design-and-Characterization-SKY130-/netlists")
FIXED_DIR    = Path("simulations_fixed")
RESULTS_DIR  = Path("results")
CSV_FLAT     = RESULTS_DIR / "characterization_results.csv"
CSV_TABLES   = RESULTS_DIR / "nldm_tables.csv"
NGSPICE_CMD  = "ngspice"


INPUT_TRANSITIONS = [0.0100, 0.0231, 0.0531, 0.1225, 0.2823, 0.6507, 1.5000]  # ns
OUTPUT_CAPS       = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]  # pF

CELL_NAMES = [
    "invx1", "invx2", "invx4", "invx8",
    "nand2x1", "nand2x2", "nand2x4",
    "nor2x1",  "nor2x2",  "nor2x4",
    "maj3x1",  "maj3x2",  "maj3x4",
]

TABLE_NAMES  = ["cell_rise", "cell_fall", "rise_transition", "fall_transition"]
FLAT_HEADER  = ["cell", "tin_ns", "cl_pf", "cell_fall", "cell_rise", "rise_transition", "fall_transition"]


# fix paths inside a netlis
def fix_and_copy_netlist(src: Path, dst: Path) -> None:
    text = src.read_text()
    text = re.sub(r'\.lib\s+"[^"]+"\s+tt',  f'.lib "{SKY130_LIB}" tt', text)
    text = re.sub(r'\.include\s+"[^"]+"',    f'.include "{CELLS_SP}"',  text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)


#run ngspice
def run_ngspice(sim_file: Path) -> str:
    result = subprocess.run(
        [NGSPICE_CMD, "-b", str(sim_file)],
        capture_output=True, text=True, timeout=180
    )
    if result.returncode != 0:
        print(f"  [WARN] ngspice error for {sim_file.name}")
        print(result.stderr[-300:])
    return result.stdout + result.stderr


# parse .meas result
MEASURE_RE = re.compile(
    r"^(cell_rise|cell_fall|rise_transition|fall_transition)\s*=\s*([\d.eE+\-]+)",
    re.IGNORECASE | re.MULTILINE
)

def parse_measures(output: str) -> dict:
    values = {}
    for m in MEASURE_RE.finditer(output):
        key   = m.group(1).lower()
        val_s = float(m.group(2))
        if val_s < 1e30:
            values[key] = val_s * 1e9
    return values


#aggregate into 7×7 matrices
def aggregate_matrices(cell_name: str) -> dict:
    tables = {
        "cell_rise":       np.full((7, 7), np.nan),
        "cell_fall":       np.full((7, 7), np.nan),
        "rise_transition": np.full((7, 7), np.nan),
        "fall_transition": np.full((7, 7), np.nan),
    }

    cell_netlist_dir = NETLISTS_DIR / cell_name
    cell_fixed_dir   = FIXED_DIR / cell_name
    cell_fixed_dir.mkdir(parents=True, exist_ok=True)

    total = 7 * 7
    done  = 0

    for i, tin in enumerate(INPUT_TRANSITIONS):
        for j, cl in enumerate(OUTPUT_CAPS):
            done += 1

            pattern = f"{cell_name}_tin_{tin:.4f}ns_cl_{cl:.4f}pf.sp"
            src = cell_netlist_dir / pattern

            if not src.exists():
                matches = list(cell_netlist_dir.glob(f"{cell_name}_tin_{tin}*_cl_{cl}*.sp"))
                if not matches:
                    print(f"  [MISSING] {pattern}")
                    continue
                src = matches[0]

            dst = cell_fixed_dir / src.name
            fix_and_copy_netlist(src, dst)

            print(f"  [{cell_name}] {done}/{total}  tin={tin}ns  cl={cl}pF")

            output   = run_ngspice(dst)
            measures = parse_measures(output)

            if not measures:
                print(f"    [WARN] No measurements parsed — check {dst}")

            for key, val in measures.items():
                if key == "cell_rise":        tables["cell_rise"][i, j]       = val
                if key == "cell_fall":        tables["cell_fall"][i, j]       = val
                if key == "rise_transition":  tables["rise_transition"][i, j] = val
                if key == "fall_transition":  tables["fall_transition"][i, j] = val

    return tables


# SAVE CSV helpers
def save_json(cell_name: str, tables: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "cell": cell_name,
        "input_transitions_ns": INPUT_TRANSITIONS,
        "output_caps_pf": OUTPUT_CAPS,
        "tables": {k: v.tolist() for k, v in tables.items()}
    }
    (RESULTS_DIR / f"{cell_name}.json").write_text(json.dumps(out, indent=2))
    print(f"  → Saved results/{cell_name}.json")


def append_to_flat_csv(cell_name: str, tables: dict) -> None:
    file_exists = CSV_FLAT.exists()
    with open(CSV_FLAT, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(FLAT_HEADER)
        for i, tin in enumerate(INPUT_TRANSITIONS):
            for j, cl in enumerate(OUTPUT_CAPS):
                def fmt(v):
                    return "" if np.isnan(v) else v
                writer.writerow([
                    cell_name, tin, cl,
                    fmt(tables["cell_fall"][i, j]),
                    fmt(tables["cell_rise"][i, j]),
                    fmt(tables["rise_transition"][i, j]),
                    fmt(tables["fall_transition"][i, j]),
                ])
    print(f"  → Appended to {CSV_FLAT}")


def append_to_tables_csv(cell_name: str, tables: dict) -> None:
    with open(CSV_TABLES, "a", newline="") as f:
        writer = csv.writer(f)
        for tname in TABLE_NAMES:
            matrix = tables[tname]

            # Title row
            writer.writerow([f"{cell_name}  |  {tname}  (rows=input_transition, cols=cload)  [ns]"])

            # Column header row: blank label cell + 7 cload values
            writer.writerow(["tin \\ cload"] + OUTPUT_CAPS)

            # Data rows: tin value + 7 matrix values
            for i, tin in enumerate(INPUT_TRANSITIONS):
                row = [f"{tin:.4f} ns"]
                for j in range(7):
                    val = matrix[i, j]
                    row.append("" if np.isnan(val) else round(float(val), 10))
                writer.writerow(row)

            # Blank row between tables
            writer.writerow([])

        # Extra blank row between cells
        writer.writerow([])

    print(f"  → Appended to {CSV_TABLES}")


def load_json(cell_name: str) -> dict | None:
    path = RESULTS_DIR / f"{cell_name}.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    raw["tables"] = {k: np.array(v) for k, v in raw["tables"].items()}
    return raw

# PRINT helper
def print_table(cell_name: str, table_name: str, matrix: np.ndarray) -> None:
    print(f"\n{'─'*70}")
    print(f"  {cell_name}  |  {table_name}  (rows=input_transition, cols=cload)  [ns]")
    print(f"{'─'*70}")
    print("           " + "".join(f"{c:>10.4f}" for c in OUTPUT_CAPS))
    for i, tin in enumerate(INPUT_TRANSITIONS):
        row = f"{tin:7.4f} ns  " + "".join(
            f"{matrix[i,j]:>10.4f}" if not np.isnan(matrix[i,j]) else "      N/A "
            for j in range(7)
        )
        print(row)

def main():
    FIXED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove old CSVs so we don't double-append on re-runs
    for f in [CSV_FLAT, CSV_TABLES]:
        if f.exists():
            f.unlink()
            print(f"  Removed old {f} — will regenerate\n")

    for cell_name in CELL_NAMES:
        print(f"\n{'='*70}")
        print(f"  Characterizing  {cell_name}")
        print(f"{'='*70}")

        existing = load_json(cell_name)
        if existing:
            print(f"  [SKIP] Found existing results at results/{cell_name}.json")
            tables = existing["tables"]
        else:
            tables = aggregate_matrices(cell_name)
            save_json(cell_name, tables)

        append_to_flat_csv(cell_name, tables)
        append_to_tables_csv(cell_name, tables)

        for tname, matrix in tables.items():
            print_table(cell_name, tname, matrix)

    print(f"\n\n{'='*70}")
    print(f"  Done! Results saved to:")
    print(f"    {RESULTS_DIR}/<cell>.json   — per-cell 7x7 matrices")
    print(f"    {CSV_FLAT}  — flat format (one row per combination)")
    print(f"    {CSV_TABLES}  — matrix format (7x7 blocks)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()