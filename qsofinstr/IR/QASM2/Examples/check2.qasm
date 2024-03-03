qreg q[4];
creg c[4];

gate XRX (param1) a, b{
    X a;
    RX(param1) b;
}

opaque mixamp(param1) a;
opaque mixphase(param1) a;

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
mixamp(1) q[0];
mixphase(2) q[1];
measure q[0] -> c[0];
if (c[0] == 1) XRX(1) q[1], q[0];
if (c[0] == 1) measure q[1] -> c[1];
if (c[0] == 1) mixamp(1) q[2];
if (c == 3) reset q[2];

