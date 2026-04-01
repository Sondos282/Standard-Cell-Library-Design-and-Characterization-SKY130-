import csv
from pathlib import Path

RESULTS_CSV = "results/characterization_results.csv"
OUT_CSV     = "results/rc_comparison.csv"

MID_TIN   = 0.1225   # ns
MID_CLOAD = 0.0094   # pF

TN_S   = 1.240355e-10   # s  — NMOS discharge time for 25fF to 50% VDD
TP_S   = 2.943091e-10   # s  — PMOS charge time for 25fF to 50% VDD
C_TEST = 25e-15         # F  — load cap used in kp.sp

R_N_MIN = TN_S / (0.69 * C_TEST)   # W=0.42um NMOS
R_P_MIN = TP_S / (0.69 * C_TEST)   # W=1.00um PMOS

C_INT = 1.597333e-15   # F, INVx1 input cap from cinv.sp

W_MIN_N = 0.42   
W_MIN_P = 1.00   
KP      = 2.4
WU      = 1.0    

R_N_INV  = R_N_MIN * (W_MIN_N / (1     * WU))   # Wn=1u
R_P_INV  = R_P_MIN * (W_MIN_P / (KP    * WU))   # Wp=2.4u

R_N_NAND = R_N_MIN * (W_MIN_N / (2     * WU))   # Wn=2u
R_P_NAND = R_P_MIN * (W_MIN_P / (KP    * WU))   # Wp=2.4u

R_N_NOR  = R_N_MIN * (W_MIN_N / (1     * WU))   # Wn=1u
R_P_NOR  = R_P_MIN * (W_MIN_P / (2*KP  * WU))   # Wp=4.8u

R_N_MAJ  = R_N_MIN * (W_MIN_N / (2     * WU))   # Wn=2u
R_P_MAJ  = R_P_MIN * (W_MIN_P / (2.5*KP* WU))   # Wp=6.0u

# Cell definitions
CELL_DEFS = {
    "invx1":   {"size": 1, "r_n": R_N_INV,  "r_p": R_P_INV,  "r_n_mult": 1,   "r_p_mult": 1,   "type": "simple"},
    "invx2":   {"size": 2, "r_n": R_N_INV,  "r_p": R_P_INV,  "r_n_mult": 1,   "r_p_mult": 1,   "type": "simple"},
    "invx4":   {"size": 4, "r_n": R_N_INV,  "r_p": R_P_INV,  "r_n_mult": 1,   "r_p_mult": 1,   "type": "simple"},
    "invx8":   {"size": 8, "r_n": R_N_INV,  "r_p": R_P_INV,  "r_n_mult": 1,   "r_p_mult": 1,   "type": "simple"},
    "nand2x1": {"size": 1, "r_n": R_N_NAND, "r_p": R_P_NAND, "r_n_mult": 2,   "r_p_mult": 0.5, "type": "simple"},
    "nand2x2": {"size": 2, "r_n": R_N_NAND, "r_p": R_P_NAND, "r_n_mult": 2,   "r_p_mult": 0.5, "type": "simple"},
    "nand2x4": {"size": 4, "r_n": R_N_NAND, "r_p": R_P_NAND, "r_n_mult": 2,   "r_p_mult": 0.5, "type": "simple"},
    "nor2x1":  {"size": 1, "r_n": R_N_NOR,  "r_p": R_P_NOR,  "r_n_mult": 0.5, "r_p_mult": 2,   "type": "simple"},
    "nor2x2":  {"size": 2, "r_n": R_N_NOR,  "r_p": R_P_NOR,  "r_n_mult": 0.5, "r_p_mult": 2,   "type": "simple"},
    "nor2x4":  {"size": 4, "r_n": R_N_NOR,  "r_p": R_P_NOR,  "r_n_mult": 0.5, "r_p_mult": 2,   "type": "simple"},
    "maj3x1":  {"size": 1, "type": "maj3"},
    "maj3x2":  {"size": 2, "type": "maj3"},
    "maj3x4":  {"size": 4, "type": "maj3"},
}

# analytical RC delay calculations
def compute_rc_delay(r_base: float, r_mult: float, size: int,
                     c_int_f: float, c_load_pf: float) -> float:
    R_eff   = r_base * r_mult / size
    C_total = c_int_f + c_load_pf * 1e-12
    return 0.69 * R_eff * C_total * 1e9   # ns


def compute_maj3_rc(size: int, c_int_f: float, c_load_pf: float):
    c_int_pf = c_int_f * 1e12

    stage1_rise = compute_rc_delay(R_P_MAJ, 0.5, size, c_int_f, c_int_pf)
    stage1_fall = compute_rc_delay(R_N_MAJ, 2,   size, c_int_f, c_int_pf)

    stage2_rise = compute_rc_delay(R_P_MAJ, 1/3, size, c_int_f, c_load_pf)
    stage2_fall = compute_rc_delay(R_N_MAJ, 3,   size, c_int_f, c_load_pf)

    return stage1_rise + stage2_rise, stage1_fall + stage2_fall

# Load NLDM mid-point values from CSV
def load_spice_midpoints(csv_path: str) -> dict:
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
                    "nldm_cell_rise": float(row["cell_rise"]) if row["cell_rise"] else None,
                    "nldm_cell_fall": float(row["cell_fall"]) if row["cell_fall"] else None,
                }
    return midpoints

def main():
    print(f"\nSKY130 parameters:")
    print(f"  R_N_MIN = {R_N_MIN:.1f} Ω  (W={W_MIN_N}um NMOS)")
    print(f"  R_P_MIN = {R_P_MIN:.1f} Ω  (W={W_MIN_P}um PMOS)")
    print(f"  C_int   = {C_INT*1e15:.3f} fF")
    print(f"  Mid-point: tin={MID_TIN}ns, cload={MID_CLOAD}pF\n")

    nldm = load_spice_midpoints(RESULTS_CSV)

    if not nldm:
        print(f"No mid-point rows found in {RESULTS_CSV}")
        return
    print(f"  RC Model Calculation vs NLDM Mid-Point")
    print(f"\n  {'Cell':<12}  {'RC_rise':>10}  {'NLDM_rise':>10}  {'RC_fall':>10}  {'NLDM_fall':>10}")

    rows = []

    for cell_name, defs in CELL_DEFS.items():
        size = defs["size"]

        # Analytical RC calculation
        if defs["type"] == "maj3":
            rc_rise, rc_fall = compute_maj3_rc(size, C_INT, MID_CLOAD)
        else:
            rc_rise = compute_rc_delay(defs["r_p"], defs["r_p_mult"], size, C_INT, MID_CLOAD)
            rc_fall = compute_rc_delay(defs["r_n"], defs["r_n_mult"], size, C_INT, MID_CLOAD)

        # NLDM mid-point values
        sp         = nldm.get(cell_name, {})
        nldm_rise  = sp.get("nldm_cell_rise")
        nldm_fall  = sp.get("nldm_cell_fall")

        def fmt(v):
            return f"{v:.5f}" if v is not None else "    N/A"

        print(f"  {cell_name:<12}  {fmt(rc_rise):>10}  {fmt(nldm_rise):>10}"
              f"  {fmt(rc_fall):>10}  {fmt(nldm_fall):>10}")

        rows.append({
            "cell":         cell_name,
            "rc_rise_ns":   round(rc_rise, 7),
            "nldm_rise_ns": nldm_rise,
            "rc_fall_ns":   round(rc_fall, 7),
            "nldm_fall_ns": nldm_fall,
        })

    # Save to CSV
    Path(OUT_CSV).parent.mkdir(exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved to {OUT_CSV}\n")


if __name__ == "__main__":
    main()