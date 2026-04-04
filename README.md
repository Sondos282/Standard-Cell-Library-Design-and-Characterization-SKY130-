# Project 1: Standard Cell Library Design and Characterization (SKY130)

## 👥 Team Members
* **Student 1:** Sondos Ahmed - 900233537
* **Student 2:** Habiba ElSayed - 900221264

## 📝 Project Overview
This repository contains the design and automated SPICE characterization of a 13-cell standard cell library using the open-source SKY130 Process Design Kit (PDK). The automated flow generates 637 SPICE netlists across varying input transitions and load capacitances, simulates them in parallel using `ngspice`, and parses the results to construct standard Non-Linear Delay Model (NLDM) tables.

### Characterized Cells
| Cell Type | Function | Drive Strengths |
| :--- | :--- | :--- |
| **Inverter** | Y = NOT(A) | invx1, invx2, invx4, invx8 |
| **NAND2** | Y = NOT(A AND B) | nand2x1, nand2x2, nand2x4 |
| **NOR2** | Y = NOT(A OR B) | nor2x1, nor2x2, nor2x4 |
| **MAJ3** | Y = AB + BC + AC | maj3x1, maj3x2, maj3x4 |

---

## 📂 Repository Structure
* `cells.sp` - The core SPICE library containing `.subckt` definitions for all 13 standard cells.
* `generate_netlists.py` - Script to generate the 637 `.sp` testbenches for all combinations of input slew and load capacitance.
* `run_simulations.py` - Automation script that executes `ngspice` in parallel and parses the `.measure` outputs into a CSV.
* `characterize.py` / `plot_delay.py` - Scripts to process the CSV data, generate NLDM Markdown tables, and plot delay curves.
* `📂 Results` - Contains all the collected results: NLDM tables, plot delay curves, rc analysis suimulation.

---

## 🚀 How to Run the Characterization Flow

### Prerequisites
Ensure you have `ngspice` installed and the SKY130 PDK accessible. Python 3 requires the `pandas`, `matplotlib`, and `numpy` libraries.

**Important:** To read the SKY130 HSPICE models correctly without double-scaling issues, ensure your local directory contains a `.spiceinit` file with the following line:
`set ngbehavior=hsa`

### Execution Steps
1. Generate the netlists: `python3 generate_netlists.py`
2. Run parallel ngspice simulations: `python3 run_simulations.py`
3. Generate NLDM tables and plots: `python3 characterize.py` and `python3 plot_delay.py`

---

## 📊 Results and Deliverables

### 1. Inverter Family Delay vs. Load
Below is the propagation delay plotted against load capacitance for the inverter family (`invx1` through `invx8`) at a fixed input transition of `tin = 0.1225 ns`.

<img width="3000" height="1800" alt="delay_vs_load_inv" src="https://github.com/user-attachments/assets/726831b4-2a9e-4c3a-8c85-505d22884f01" />


### 2. NLDM Tables
The full set of 7x7 Non-Linear Delay Model (NLDM) tables for all 13 cells can be found in:

---

## 🧮 Analytical Comparison: RC Model vs. SPICE

**Comparison Point:**
* Input Transition (tin) = 0.1225 ns
* Load Capacitance (Cload) = 0.0094 pF

### Discussion and Limitations
While the first-order RC model provides a useful baseline for hand calculations, it shows a discrepancy compared to the SPICE NLDM results. This deviation occurs because the RC model has several fundamental limitations:
**Assumption of a Perfect Step Input:** The standard RC equations assume $t_{in} = 0$ (an instantaneous step). In reality, at $t_{in} = 0.1225 ns$, the input signal ramps gradually. During this transition window, both the PMOS and NMOS transistors are partially ON simultaneously. This creates a short-circuit current path from $V_{DD}$ to ground, which steals current away from charging/discharging the load capacitance, thereby increasing the actual propagation delay. The linear RC model completely fails to capture this input slew dependency.
**Dynamic Transistor Behavior:** The RC model approximates transistors as constant linear resistors ($R_{eq}$). However, during switching, modern deep-submicron transistors (like those in SKY130) transition non-linearly through cutoff, saturation, and linear regions. Velocity saturation and short-channel effects further cause the equivalent resistance to change dynamically based on the drain-to-source voltage.
Because of these limitations, using two-dimensional NLDM tables (which index both $C_{load}$ and $t_{in}$) is strictly necessary for accurate static timing analysis in modern digital design.
