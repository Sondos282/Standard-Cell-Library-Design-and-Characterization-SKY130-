* =========================================================
* cells.sp
* SKY130 standard cell library for Project 1
* =========================================================
*
* Pin order:
*   invx*   : A Y VDD GND
*   nand2x* : A B Y VDD GND
*   nor2x*  : A B Y VDD GND
*   maj3x*  : A B C Y VDD GND
*
* Sizing assumptions:
*   Kp = 2.4
*   invx1   : Wn=1,  Wp=Kp
*   nand2x1 : Wn=2,  Wp=2Kp
*   nor2x1  : Wn=1,  Wp=2Kp
*   maj3x1  : Wn=2,  Wp=2.5Kp
*
* Scaling:
*   x2 = 2x widths
*   x4 = 4x widths
*   x8 = 8x widths
*
* SPICE units used here:
*   WU  = 1u
*   LCH = 0.15u
*
* Model names:
*   sky130_fd_pr__nfet_01v8
*   sky130_fd_pr__pfet_01v8
* =========================================================

.param KP=2.4
.param WU=1u
.param LCH=0.15u

* =========================================================
* Core helper cells
* =========================================================

* -------------------------
* Inverter core
* Base x1: Wn=1, Wp=Kp
* -------------------------
.subckt inv_core A Y VDD GND params: SCALE=1
XMp0 Y A VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*KP*WU} L={LCH}
XMn0 Y A GND GND sky130_fd_pr__nfet_01v8 W={SCALE*1*WU}  L={LCH}
.ends inv_core


* -------------------------
* NAND2 core
* Base x1: Wn=2, Wp=Kp
* -------------------------
.subckt nand2_core A B Y VDD GND params: SCALE=1
* Pull-up: PMOS in parallel
XMp0 Y A VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*KP*WU} L={LCH}
XMp1 Y B VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*KP*WU} L={LCH}

* Pull-down: NMOS in series
XMn0 Y  A N1  GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU} L={LCH}
XMn1 N1 B GND GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU} L={LCH}
.ends nand2_core


* -------------------------
* NOR2 core
* Base x1: Wn=1, Wp=2Kps
* -------------------------
.subckt nor2_core A B Y VDD GND params: SCALE=1
* Pull-up: PMOS in series
XMp0 Y  A N1  VDD sky130_fd_pr__pfet_01v8 W={SCALE*2*KP*WU} L={LCH}
XMp1 N1 B VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2*KP*WU} L={LCH}

* Pull-down: NMOS in parallel
XMn0 Y A GND GND sky130_fd_pr__nfet_01v8 W={SCALE*1*WU} L={LCH}
XMn1 Y B GND GND sky130_fd_pr__nfet_01v8 W={SCALE*1*WU} L={LCH}
.ends nor2_core


* -------------------------
* MAJ3 core
* Y = AB + AC + BC
*
* Implemented as:
*   nAB = NAND(A,B)
*   nAC = NAND(A,C)
*   nBC = NAND(B,C)
*   Y   = NAND(nAB,nAC,nBC)
*
* Base x1: Wn=2, Wp=2.5Kp = 6.0
* Every transistor in this cell uses that requested base size,
* then scales by SCALE.
* -------------------------
.subckt maj3_core A B C Y VDD GND params: SCALE=1

* ----- NAND(A,B) -> nAB
XMpAB0 nAB A   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMpAB1 nAB B   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMnAB0 nAB A   NAB1 GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}
XMnAB1 NAB1 B  GND  GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}

* ----- NAND(A,C) -> nAC
XMpAC0 nAC A   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMpAC1 nAC C   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMnAC0 nAC A   NAC1 GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}
XMnAC1 NAC1 C  GND  GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}

* ----- NAND(B,C) -> nBC
XMpBC0 nBC B   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMpBC1 nBC C   VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMnBC0 nBC B   NBC1 GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}
XMnBC1 NBC1 C  GND  GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}

* ----- NAND(nAB,nAC,nBC) -> Y
XMpY0 Y   nAB VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMpY1 Y   nAC VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}
XMpY2 Y   nBC VDD VDD sky130_fd_pr__pfet_01v8 W={SCALE*2.5*KP*WU} L={LCH}

XMnY0 Y   nAB NY1 GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}
XMnY1 NY1 nAC NY2 GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}
XMnY2 NY2 nBC GND GND sky130_fd_pr__nfet_01v8 W={SCALE*2*WU}      L={LCH}

.ends maj3_core


* =========================================================
* Public library cells (13 required cells)
* =========================================================

* -------------------------
* Inverter
* -------------------------
.subckt invx1 A Y VDD GND
XINV1 A Y VDD GND inv_core SCALE=1
.ends invx1

.subckt invx2 A Y VDD GND
XINV2 A Y VDD GND inv_core SCALE=2
.ends invx2

.subckt invx4 A Y VDD GND
XINV4 A Y VDD GND inv_core SCALE=4
.ends invx4

.subckt invx8 A Y VDD GND
XINV8 A Y VDD GND inv_core SCALE=8
.ends invx8


* -------------------------
* NAND2
* -------------------------
.subckt nand2x1 A B Y VDD GND
XNAND21 A B Y VDD GND nand2_core SCALE=1
.ends nand2x1

.subckt nand2x2 A B Y VDD GND
XNAND22 A B Y VDD GND nand2_core SCALE=2
.ends nand2x2

.subckt nand2x4 A B Y VDD GND
XNAND24 A B Y VDD GND nand2_core SCALE=4
.ends nand2x4


* -------------------------
* NOR2
* -------------------------
.subckt nor2x1 A B Y VDD GND
XNOR21 A B Y VDD GND nor2_core SCALE=1
.ends nor2x1

.subckt nor2x2 A B Y VDD GND
XNOR22 A B Y VDD GND nor2_core SCALE=2
.ends nor2x2

.subckt nor2x4 A B Y VDD GND
XNOR24 A B Y VDD GND nor2_core SCALE=4
.ends nor2x4


* -------------------------
* MAJ3
* -------------------------
.subckt maj3x1 A B C Y VDD GND
XMAJ31 A B C Y VDD GND maj3_core SCALE=1
.ends maj3x1

.subckt maj3x2 A B C Y VDD GND
XMAJ32 A B C Y VDD GND maj3_core SCALE=2
.ends maj3x2

.subckt maj3x4 A B C Y VDD GND
XMAJ34 A B C Y VDD GND maj3_core SCALE=4
.ends maj3x4
