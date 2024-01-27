// qreg declare
qreg q[4];
qreg q_0[1];

// gate define
gate check_no_param a, b {
    X a;
    Y b;
    CX a, b;
    RTHETA (1) a;
}

gate check_with_param (param1, param2, param3, param4) a, b{
    RX(param1) a;
    RZ(param2) b;
    CRX(param3) a, b;
    RY(sqrt(param4)) b;
    RZ(param1+param2) b;
}


// gate declare
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
check_no_param q[3], q[2];
check_with_param(2.5, 1.5, 3.5, 4) q[1], q[2];
RX (sqrt(4)) q[3];
RY (1+2) q_0; // 3
RY (2*2+1) q_0; // 5
RY (2/2+1-1) q_0; // 1
RY(1+2^3*2/2-4) q_0; // 5
RY(-1) q_0;
RY (exp(0)) q_0;
RZ(sqrt(2*2/2+2)) q_0;
RZ(-(1+3)+(1*2)) q_0;
CX q[0], q[1] : q[2];
CY q[0], q[2], q[3] : q[1];