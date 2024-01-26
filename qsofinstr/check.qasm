qreg q[4];
qreg q_0[1];

gate check a, b {
    X a;
    Y b;
    CX a, b;
    RTHETA (1) a;
}

X q[0];
X q[1];
X q[3];
Y q_0;
X q[1];
Y q[1];
X q[3];
H q[2];
RX(1) q[2];
RX(3) q[2];
RY(1) q[3];
RZ(1) q_0;
RTHETA(1) q[0];
U(1, 2, 1) q[2];
CX q[1], q[0];
CX q[1], q[3];
CX q_0, q[2];
CRX(1) q_0, q[3];
check q[3], q[2];