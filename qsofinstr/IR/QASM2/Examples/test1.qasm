include "qsofinstr/test2.qasm";
gate include_test1(param1, param2) a, b {
    RX(param1) a;
    RY(param2) b;
    include_test2(param1, param2) a, b;
}

//gate test3 a{
//    W a;
//}