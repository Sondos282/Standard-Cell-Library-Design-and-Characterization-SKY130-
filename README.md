# Project 1: Standard Cell Library Design and Characterization (SKY130)

## 👥 Team Members
* **Student 1:** Sondos Ahmed - 900233537
* **Student 2:** Habiba ElSayed - 900

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
* `generate_report.py` / `plot_delay.py` - Scripts to process the CSV data, generate NLDM Markdown tables, and plot delay curves.
* `characterization_results.csv` - The raw parsed simulation data.

---

## 🚀 How to Run the Characterization Flow

### Prerequisites
Ensure you have `ngspice` installed and the SKY130 PDK accessible. Python 3 requires the `pandas`, `matplotlib`, and `numpy` libraries.

**Important:** To read the SKY130 HSPICE models correctly without double-scaling issues, ensure your local directory contains a `.spiceinit` file with the following line:
```bash
set ngbehavior=hsa

### Execution Steps
1. Generate the netlists: `python3 generate_netlists.py`
2. Run parallel ngspice simulations: `python3 run_simulations.py`
3. Generate NLDM tables and plots: `python3 generate_report.py` and `python3 plot_delay.py`

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

### Theoretical First-Order Linear RC Delay
* **Theoretical tpHL:**  ps
* **Theoretical tpLH:**  ps

### Simulated SPICE Delay (From NLDM Tables)
* **Simulated `cell_fall` (tpHL):**  ps
* **Simulated `cell_rise` (tpLH):**  ps

### Discussion and Limitations
