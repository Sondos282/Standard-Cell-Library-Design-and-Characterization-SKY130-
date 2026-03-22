#!/usr/bin/env python3

from pathlib import Path
from textwrap import dedent

# Project configuration

VDD = 1.8
TEMP_C = 25

SKY130_LIB_PATH = "/home/sondos/work/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice"
SKY130_CORNER = "tt"

INPUT_TRANSITIONS_NS = [0.0100, 0.0231, 0.0531, 0.1225, 0.2823, 0.6507, 1.5000]
OUTPUT_CAPS_PF       = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]

# Cell list
CELLS = [
    "invx1", "invx2", "invx4", "invx8",
    "nand2x1", "nand2x2", "nand2x4",
    "nor2x1", "nor2x2", "nor2x4",
    "maj3x1", "maj3x2", "maj3x4",
]

# Pin order for .subckt definitions
PIN_ORDERS = {
    "invx1":   ["A", "Y", "VDD", "VSS"],
    "invx2":   ["A", "Y", "VDD", "VSS"],
    "invx4":   ["A", "Y", "VDD", "VSS"],
    "invx8":   ["A", "Y", "VDD", "VSS"],

    "nand2x1": ["A", "B", "Y", "VDD", "VSS"],
    "nand2x2": ["A", "B", "Y", "VDD", "VSS"],
    "nand2x4": ["A", "B", "Y", "VDD", "VSS"],

    "nor2x1":  ["A", "B", "Y", "VDD", "VSS"],
    "nor2x2":  ["A", "B", "Y", "VDD", "VSS"],
    "nor2x4":  ["A", "B", "Y", "VDD", "VSS"],

    "maj3x1":  ["A", "B", "C", "Y", "VDD", "VSS"],
    "maj3x2":  ["A", "B", "C", "Y", "VDD", "VSS"],
    "maj3x4":  ["A", "B", "C", "Y", "VDD", "VSS"],
}

# For each cell, define the input toggled for characterization and the static values
# on non-switching inputs to force a valid output rise/fall arc.
ARC_CONFIGS = {
    # inverter: toggle A
    "inv": {
        "toggle_pin": "A",
        "static_inputs": {},
        # output fall when A rises, output rise when A falls
    },

    # NAND2: characterize A while B=1
    "nand2": {
        "toggle_pin": "A",
        "static_inputs": {"B": 1},
    },

    # NOR2: characterize A while B=0
    "nor2": {
        "toggle_pin": "A",
        "static_inputs": {"B": 0},
    },

    # MAJ3: characterize A while B=1, C=0
    # Then Y follows A (majority of A,1,0 = A)
    "maj3": {
        "toggle_pin": "A",
        "static_inputs": {"B": 1, "C": 0},
    },
}

# Utility functions
def classify_cell(cell_name: str) -> str:
    if cell_name.startswith("inv"):
        return "inv"
    if cell_name.startswith("nand2"):
        return "nand2"
    if cell_name.startswith("nor2"):
        return "nor2"
    if cell_name.startswith("maj3"):
        return "maj3"
    raise ValueError(f"Unknown cell type: {cell_name}")

def ns_to_s(ns: float) -> float:
    return ns * 1e-9

def pf_to_f(pf: float) -> float:
    return pf * 1e-12

def fmt_float(x: float) -> str:
    return f"{x:.6g}"

def build_pulse_source(slew_ns: float) -> str:
    """
    Build a pulse source with rise time = fall time = slew_ns.
    """
    tr = ns_to_s(slew_ns)
    tf = ns_to_s(slew_ns)

    # Long enough period for one clean switching event
    td = 2e-9
    pw = 8e-9
    per = 20e-9

    return f"PULSE(0 {VDD} {fmt_float(td)} {fmt_float(tr)} {fmt_float(tf)} {fmt_float(pw)} {fmt_float(per)})"

def build_dc_source(value: int) -> str:
    return f"DC {VDD if value else 0}"

def build_instance_line(cell_name: str) -> str:
    """
    Create the XUUT line according to PIN_ORDERS.
    External nodes use the same names as pins, except power uses vdd/vss.
    """
    pins = PIN_ORDERS[cell_name]
    node_map = {
        "A": "a",
        "B": "b",
        "C": "c",
        "Y": "y",
        "VDD": "vdd",
        "VSS": "vss",
    }
    nodes = [node_map[p] for p in pins]
    return f"XUUT {' '.join(nodes)} {cell_name}"

def build_sources(cell_name: str, slew_ns: float) -> str:
    family = classify_cell(cell_name)
    cfg = ARC_CONFIGS[family]
    toggle_pin = cfg["toggle_pin"]
    static_inputs = cfg["static_inputs"]

    src_lines = []

    # Power sources
    src_lines.append(f"VDD vdd 0 DC {VDD}")
    src_lines.append("VSS vss 0 DC 0")

    # Input sources
    for pin in ["A", "B", "C"]:
        pin_l = pin.lower()
        if pin not in [p for p in PIN_ORDERS[cell_name] if p in ("A", "B", "C")]:
            continue

        if pin == toggle_pin:
            src_lines.append(f"V{pin} {pin_l} 0 {build_pulse_source(slew_ns)}")
        else:
            dc_val = static_inputs.get(pin, 0)
            src_lines.append(f"V{pin} {pin_l} 0 {build_dc_source(dc_val)}")

    return "\n".join(src_lines)

def build_load(cap_pf: float) -> str:
    cap_f = pf_to_f(cap_pf)
    return f"Cload y 0 {fmt_float(cap_f)}"

def build_measures() -> str:
    v20 = 0.2 * VDD
    v50 = 0.5 * VDD
    v80 = 0.8 * VDD

    return dedent(f"""\
    * ---- Measurements ----
    * Propagation delays
    .measure tran cell_fall TRIG v(a) VAL={fmt_float(v50)} RISE=1 TARG v(y) VAL={fmt_float(v50)} FALL=1
    .measure tran cell_rise TRIG v(a) VAL={fmt_float(v50)} FALL=1 TARG v(y) VAL={fmt_float(v50)} RISE=1

    * Output transition times
    .measure tran rise_transition TRIG v(y) VAL={fmt_float(v20)} RISE=1 TARG v(y) VAL={fmt_float(v80)} RISE=1
    .measure tran fall_transition TRIG v(y) VAL={fmt_float(v80)} FALL=1 TARG v(y) VAL={fmt_float(v20)} FALL=1
    """)

def build_tran_control(slew_ns: float, cap_pf: float) -> str:
    """
    Choose a conservative transient stop time.
    For larger slews/loads, simulation may need longer settling.
    """
    # Heuristic runtime
    tstep = min(ns_to_s(slew_ns) / 20, 5e-12)
    tstop = 60e-9
    return f".tran {fmt_float(tstep)} {fmt_float(tstop)}"

def build_netlist(cell_name: str, slew_ns: float, cap_pf: float) -> str:
    title = f"{cell_name} characterization, tin={slew_ns}ns, cload={cap_pf}pF"

    return dedent(f"""\
    * ==========================================================
    * {title}
    * ==========================================================
    .title {title}

    .lib "{SKY130_LIB_PATH}" {SKY130_CORNER}
    .temp {TEMP_C}

    * Include your standard-cell library file
    .include "cells.sp"

    {build_sources(cell_name, slew_ns)}

    {build_instance_line(cell_name)}

    {build_load(cap_pf)}

    {build_measures()}

    {build_tran_control(slew_ns, cap_pf)}

    .end
    """)

# File generation

def write_one_netlist(out_dir: Path, cell_name: str, slew_ns: float, cap_pf: float) -> Path:
    family_dir = out_dir / cell_name
    family_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{cell_name}_tin_{slew_ns:.4f}ns_cl_{cap_pf:.4f}pf.sp"
    path = family_dir / fname
    path.write_text(build_netlist(cell_name, slew_ns, cap_pf))
    return path

def generate_all(out_root: str = "netlists") -> None:
    out_dir = Path(out_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    for cell in CELLS:
        for tin_ns in INPUT_TRANSITIONS_NS:
            for cl_pf in OUTPUT_CAPS_PF:
                write_one_netlist(out_dir, cell, tin_ns, cl_pf)
                generated += 1

    print(f"Generated {generated} netlists in: {out_dir.resolve()}")

if __name__ == "__main__":
    generate_all()