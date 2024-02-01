gate skip a{
    X a;
}

gate include_test2(param1, param2) a, b{
    RZ(param1) a;
    RTHETA(param2) b;
}

gate check3 a{
    Y a;
}