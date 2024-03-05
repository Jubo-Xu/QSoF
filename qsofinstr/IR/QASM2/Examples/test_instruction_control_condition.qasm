OPENQASM 2.0;
include "qelib1.inc";

qreg q[7];
creg c1[2];
creg c2[2];

cx q[0], q[1];
cx q[2], q[3], q[4], q[5] : q[6];
h q;
measure q[0] -> c1[0];
measure q[1] -> c1[1];
x q[2];
x q[2];
x q[2];
measure q[2] -> c2[0];
if(c1[0] == 1) CX q[6], q[5] : q[4];
CRX(1) q[3], q[5];
measure q[3] -> c2[1];
h q[4];
if(c1[0] == 1) cx q[5], q[4];
if(c1[1] == 0) CRX(0.75) q[4], q[6];
if(c1[1] == 0) cx q[5], q[6] : q[4];
if(c1 == 3) cx q[4], q[6];
if(c2 == 2) cx q[4], q[5] : q[6];

