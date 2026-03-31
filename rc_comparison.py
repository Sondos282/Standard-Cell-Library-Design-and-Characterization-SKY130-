
import csv
import json
from pathlib import Path

RESULTS_CSV = "results/characterization_results.csv"

MID_TIN  = 0.1225   # ns
MID_CLOAD = 0.0094  # pF

TN_S    = 1.240355e-10   # s
TP_S    = 2.943091e-10   # s
C_TEST  = 25e-15         # F 

# R = T / (0.69 × C)  for the minimum-size transistor 
R_N_MIN = TN_S / (0.69 * C_TEST)   # smallest NMOS  
R_P_MIN = TP_S / (0.69 * C_TEST)   # smallest PMOS  
KP      = TP_S / TN_S 

C_INV   = 1.597333e-15 

print(f"  R_N (min NMOS, W=0.42um) = {R_N_MIN:.1f} Ω")
print(f"  R_P (min PMOS, W=1.00um) = {R_P_MIN:.1f} Ω")
print(f"  Kp                       = {KP:.4f}")
print(f"  C_inv (INVx1 input)      = {C_INV*1e15:.4f} fF")

CELL_DEFS = {
    # Inverters
    "invx1":   {"size": 1, "r_n_eff": 1,   "r_p_eff": 1  },
    "invx2":   {"size": 2, "r_n_eff": 1,   "r_p_eff": 1  },
    "invx4":   {"size": 4, "r_n_eff": 1,   "r_p_eff": 1  },
    "invx8":   {"size": 8, "r_n_eff": 1,   "r_p_eff": 1  },
    # NAND2: 2 NMOS in series (×2), 2 PMOS in parallel (×0.5)
    "nand2x1": {"size": 1, "r_n_eff": 2,   "r_p_eff": 0.5},
    "nand2x2": {"size": 2, "r_n_eff": 2,   "r_p_eff": 0.5},
    "nand2x4": {"size": 4, "r_n_eff": 2,   "r_p_eff": 0.5},
    # NOR2: 2 NMOS in parallel (×0.5), 2 PMOS in series (×2)
    "nor2x1":  {"size": 1, "r_n_eff": 0.5, "r_p_eff": 2  },
    "nor2x2":  {"size": 2, "r_n_eff": 0.5, "r_p_eff": 2  },
    "nor2x4":  {"size": 4, "r_n_eff": 0.5, "r_p_eff": 2  },
    # MAJ3
    "maj3x1":  {"size": 1, "r_n_eff": 2,   "r_p_eff": 2  },
    "maj3x2":  {"size": 2, "r_n_eff": 2,   "r_p_eff": 2  },
    "maj3x4":  {"size": 4, "r_n_eff": 2,   "r_p_eff": 2  },
}


def rc_delay_ns(r_base_ohm: float, r_eff_mult: float,
                size: int, c_int_f: float, c_load_pf: float) -> float:
    R_eff  = r_base_ohm * r_eff_mult / size          # effective resistance Ω
    C_total = c_int_f + c_load_pf * 1e-12            # total capacitance F
    t_s    = 0.69 * R_eff * C_total                  # delay in seconds
    return t_s * 1e9                                 # ns

# Load SPICE mid-point values from CSV
def load_midpoint(csv_path: str) -> dict:
    midpoints = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tin = float(row["tin_ns"])
                cl  = float(row["cl_pf"])
            except (ValueError, KeyError):
                continue
            if abs(tin - MID_TIN) < 1e-6 and abs(cl - MID_CLOAD) < 1e-6:
                midpoints[row["cell"]] = {
                    "cell_rise":       float(row["cell_rise"])       if row["cell_rise"]       else None,
                    "cell_fall":       float(row["cell_fall"])       if row["cell_fall"]       else None,
                    "rise_transition": float(row["rise_transition"]) if row["rise_transition"] else None,
                    "fall_transition": float(row["fall_transition"]) if row["fall_transition"] else None,
                }
    return midpoints

# comparison
def main():
    print(f"  RC Model vs SPICE Comparison  —  mid-point: tin={MID_TIN}ns, cload={MID_CLOAD}pF")

    spice_data = load_midpoint(RESULTS_CSV)

    if not spice_data:
        print(f"[ERROR] No mid-point data found in {RESULTS_CSV}")
        print(f"        Make sure tin={MID_TIN} and cl={MID_CLOAD} rows exist.")
        return

    hdr = (f"{'Cell':<12} {'RC_tpLH':>10} {'SP_rise':>10} {'err_rise%':>10}"
           f"  {'RC_tpHL':>10} {'SP_fall':>10} {'err_fall%':>10}")
    print(hdr)
    print("─" * len(hdr))

    results = []

    for cell_name, defs in CELL_DEFS.items():
        size      = defs["size"]
        r_n_eff   = defs["r_n_eff"]
        r_p_eff   = defs["r_p_eff"]

        # RC model predictions
        rc_tpLH = rc_delay_ns(R_N_MIN, r_n_eff, size, C_INV, MID_CLOAD)  # pull-down → rising output for inv
        rc_tpHL = rc_delay_ns(R_P_MIN, r_p_eff, size, C_INV, MID_CLOAD)  # pull-up  → falling output for inv

        sp = spice_data.get(cell_name, {})
        sp_rise = sp.get("cell_rise")
        sp_fall = sp.get("cell_fall")

        def pct_err(rc, sp_val):
            if sp_val and sp_val > 0:
                return (rc - sp_val) / sp_val * 100
            return None

        err_rise = pct_err(rc_tpLH, sp_rise)
        err_fall = pct_err(rc_tpHL, sp_fall)

        def fmt(v, unit=""):
            return f"{v:.4f}{unit}" if v is not None else "   N/A"
        def fmt_pct(v):
            return f"{v:+.1f}%" if v is not None else "   N/A"

        print(f"{cell_name:<12} "
              f"{fmt(rc_tpLH, ' ns'):>10} {fmt(sp_rise, ' ns'):>10} {fmt_pct(err_rise):>10}  "
              f"{fmt(rc_tpHL, ' ns'):>10} {fmt(sp_fall, ' ns'):>10} {fmt_pct(err_fall):>10}")

        results.append({
            "cell": cell_name,
            "rc_tpLH_ns": rc_tpLH,
            "rc_tpHL_ns": rc_tpHL,
            "spice_rise_ns": sp_rise,
            "spice_fall_ns": sp_fall,
            "err_rise_pct": err_rise,
            "err_fall_pct": err_fall,
        })

    # Save to CSV
    out_path = Path("results/rc_comparison.csv")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"  Saved comparison table to {out_path}\n")


if __name__ == "__main__":
    main()
