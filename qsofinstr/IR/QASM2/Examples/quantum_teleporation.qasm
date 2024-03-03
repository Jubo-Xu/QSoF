//include "qelib1.inc";
qreg q[3];
qreg q_2[1];
creg c0[1];
creg c1[1];
creg c2[1];
// optional post-rotation for state tomography
gate post q { }
u3(0.3,0.2,0.1) q[0];
h q[1];
cx q[1],q[2];
barrier q;
cx q[0],q[1];
h q[0];
//x q[0];
//x q[1];
//x q[1];
//x q[1];
measure q[0] -> c0[0];
measure q[1] -> c1[0];
//x q[2];
//x q[2];
//x q[2];
//x q[2];
//x q[2];
if(c0==1) z q[2];
if(c1==1) x q[2];
if(c1==1) x q_2;
post q[2];
measure q[2] -> c2[0];
reset q;