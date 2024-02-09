qreg q[4];
creg c[4];

gate XRX (param1) a, b{
    X a;
    RX(param1) b;
}

Y q[0];
Z q[1];
H q[2];
RY(0.1) q[3];
XRX(1) q[0], q[1];
CX q[1], q[2] : q[3];
measure q[3] -> c[3];
reset q;
measure q -> c;
CRX(0.1) q[1], q[2] : q[0];
CX q[1], q[2] : q[3];
U(1, 2, 3) q[1];
id q[2];
u1(3) q[2];
id q[3];
u2(1, 2) q[3];
sdg q[3];
tdg q[3];
ccx q[0], q[2], q[3];


