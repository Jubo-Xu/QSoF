qreg q[6];
creg c1[2];
creg c2[2];

x q;
measure q[0] -> c1[0];
measure q[1] -> c1[1];
measure q[2] -> c2[0];
measure q[3] -> c2[1];

if(c1[0] == 1) x q[4];
if(c1[1] == 0) y q[5];
if(c2 == 3) z q[5];