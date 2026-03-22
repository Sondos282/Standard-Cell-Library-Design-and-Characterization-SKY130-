    * ==========================================================
    * nand2x4 characterization, tin=0.0231ns, cload=0.0094pF
    * ==========================================================
    .title nand2x4 characterization, tin=0.0231ns, cload=0.0094pF

    .lib "/home/sondos/work/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
    .temp 25

    * Include your standard-cell library file
    .include "cells.sp"

    VDD vdd 0 DC 1.8
VSS vss 0 DC 0
VA a 0 PULSE(0 1.8 2e-09 2.31e-11 2.31e-11 8e-09 2e-08)
VB b 0 DC 1.8

    XUUT a b y vdd vss nand2x4

    Cload y 0 9.4e-15

    * ---- Measurements ----
* Propagation delays
.measure tran cell_fall TRIG v(a) VAL=0.9 RISE=1 TARG v(y) VAL=0.9 FALL=1
.measure tran cell_rise TRIG v(a) VAL=0.9 FALL=1 TARG v(y) VAL=0.9 RISE=1

* Output transition times
.measure tran rise_transition TRIG v(y) VAL=0.36 RISE=1 TARG v(y) VAL=1.44 RISE=1
.measure tran fall_transition TRIG v(y) VAL=1.44 FALL=1 TARG v(y) VAL=0.36 FALL=1


    .tran 1.155e-12 6e-08

    .end
