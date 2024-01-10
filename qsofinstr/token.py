TK_OPERATOR = 0
TK_NUM = 1
TK_IDENT = 2
TK_GATE = 3
TK_U = 4
TK_X = 5
TK_Y = 6
TK_Z = 7
TK_S = 8
TK_T = 9
TK_RTHETA = 10
TK_RX = 11
TK_RY = 12
TK_RZ = 13
TK_H = 14
TK_CX = 15
TK_CY = 16
TK_CZ = 17
TK_CU = 18
TK_CS = 19
TK_CT = 20
TK_CRTHETA = 21
TK_CRX = 22
TK_CRY = 23
TK_CRZ = 24
TK_CH = 25
TK_GATE = 26
TK_MEASURE = 27 
TK_IF = 28
TK_RESET = 29
TK_BARRIER = 30
TK_OPAQUE = 31
TK_QREG = 32
TK_CREG = 33

class Token(object):
    def __init__(self):
        self.qasm_str = ""
        # The element is a tuple with the structure (kind, val, exp, len, str)
        # The value is represented as scientific notation, therefore needs val and exp parts
        self.Token = []       
    
    def file2str(self, filename):
        with open(filename, 'r') as file:
            for line in file:
            # Add the processed line to the contents string with a space
                self.qasm_str += line
    
    @staticmethod
    def is_alnum(c):
        return (c.isalpha() and c.islower()) or (c.isalpha() and c.isupper()) or c == "_"
    
    @staticmethod
    def Tokenize(filename):
        TK = Token()
        TK.file2str(filename)
        i = 0
        while i < len(TK.qasm_str):
            # Skip whitespace
            if TK.qasm_str[i].isspace() or TK.qasm_str[i] == "\t":
                i += 1
                continue
            # Check for a comment
            if TK.qasm_str[i] == "/":
                if TK.qasm_str[i+1] == "/":
                    i += 2
                    while TK.qasm_str[i] != "\n":
                        i += 1
                    continue
                else:
                    raise Exception("Invalid character '/'")
            # Check for ;
            if TK.qasm_str[i] == ";":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, ";"))
                i += 1
                continue
            
            # Check for ,
            if TK.qasm_str[i] == ",":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, ","))
                i += 1
                continue
            
            # Check for some operators
            if TK.qasm_str[i] == "+" or TK.qasm_str[i] == "-" or TK.qasm_str[i] == "*" or TK.qasm_str[i] == "/" or TK.qasm_str[i] == "^" or TK.qasm_str[i] == "(" or TK.qasm_str[i] == ")":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, TK.qasm_str[i]))
                i += 1
                continue
            
            # Check for []
            if TK.qasm_str[i] == "[" or TK.qasm_str[i] == "]":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, TK.qasm_str[i]))
                i += 1
                continue
            
            # Check for pi
            if TK.qasm_str[i] == "p" and TK.qasm_str[i+1] == "i":
                if TK.qasm_str[i+2] == "," or TK.qasm_str[i+2] == ")":
                    TK.Token.append((TK_OPERATOR, 0, 0, 2, "pi"))
                    i += 2
                    continue
            
            # Check for sin
            if TK.qasm_str[i] == "s" and TK.qasm_str[i+1] == "i" and TK.qasm_str[i+2] == "n":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 3, "sin"))
                    i += 3
                    continue
            
            # Check for cos
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "o" and TK.qasm_str[i+2] == "s":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 3, "cos"))
                    i += 3
                    continue
            
            # Check for tan
            if TK.qasm_str[i] == "t" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "n":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 3, "tan"))
                    i += 3
                    continue
            
            # Check for exp
            if TK.qasm_str[i] == "e" and TK.qasm_str[i+1] == "x" and TK.qasm_str[i+2] == "p":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 3, "exp"))
                    i += 3
                    continue
            
            # Check for ln
            if TK.qasm_str[i] == "l" and TK.qasm_str[i+1] == "n":
                if TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 2, "ln"))
                    i += 2
                    continue
            
            # Check for sqrt
            if TK.qasm_str[i] == "s" and TK.qasm_str[i+1] == "q" and TK.qasm_str[i+2] == "r" and TK.qasm_str[i+3] == "t":
                if TK.qasm_str[i+4] == "(":
                    TK.Token.append((TK_OPERATOR, 0, 0, 4, "sqrt"))
                    i += 4
                    continue
            
            # Check for gate
            if TK.qasm_str[i] == "g" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "t" and TK.qasm_str[i+4] == "e":
                if TK.qasm_str[i+5].isspace():
                    TK.Token.append((TK_GATE, 0, 0, 4, "gate"))
                    i += 4
                    continue
            
            # Check for measure 
            if TK.qasm_str[i] == "m" and TK.qasm_str[i+1] == "e" and TK.qasm_str[i+2] == "a" and TK.qasm_str[i+3] == "s" and TK.qasm_str[i+4] == "u" and TK.qasm_str[i+5] == "r" and TK.qasm_str[i+6] == "e":
                if TK.qasm_str[i+7].isspace():
                    TK.Token.append((TK_MEASURE, 0, 0, 7, "measure"))
                    i += 7
                    continue
            
            # Check for if
            if TK.qasm_str[i] == "i" and TK.qasm_str[i+1] == "f":
                if TK.qasm_str[i+2].isspace() or TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_IF, 0, 0, 2, "if"))
                    i += 2
                    continue
            
            # Check for reset
            if TK.qasm_str[i] == "r" and TK.qasm_str[i+1] == "e" and TK.qasm_str[i+2] == "s" and TK.qasm_str[i+3] == "e" and TK.qasm_str[i+4] == "t":
                if TK.qasm_str[i+5].isspace():
                    TK.Token.append((TK_RESET, 0, 0, 5, "reset"))
                    i += 5
                    continue
            
            # Check for barrier
            if TK.qasm_str[i] == "b" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "r" and TK.qasm_str[i+3] == "r" and TK.qasm_str[i+4] == "i" and TK.qasm_str[i+5] == "e" and TK.qasm_str[i+6] == "r":
                if TK.qasm_str[i+7].isspace():
                    TK.Token.append((TK_BARRIER, 0, 0, 7, "barrier"))
                    i += 7
                    continue
            
            # Check for opaque
            if TK.qasm_str[i] == "o" and TK.qasm_str[i+1] == "p" and TK.qasm_str[i+2] == "a" and TK.qasm_str[i+3] == "q" and TK.qasm_str[i+4] == "u" and TK.qasm_str[i+5] == "e":
                if TK.qasm_str[i+6].isspace():
                    TK.Token.append((TK_OPAQUE, 0, 0, 6, "opaque"))
                    i += 6
                    continue
            
            # Check for qreg
            if TK.qasm_str[i] == "q" and TK.qasm_str[i+1] == "r" and TK.qasm_str[i+2] == "e" and TK.qasm_str[i+3] == "g":
                if TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_QREG, 0, 0, 4, "qreg"))
                    i += 4
                    continue
            
            # Check for creg
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "r" and TK.qasm_str[i+2] == "e" and TK.qasm_str[i+3] == "g":
                if TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_CREG, 0, 0, 4, "creg"))
                    i += 4
                    continue
            
            # Check for U
            if TK.qasm_str[i] == "U":
                if TK.qasm_str[i+1] == "(":
                    TK.Token.append((TK_U, 0, 0, 1, "U"))
                    i += 1
                    continue
            
            # Check for X
            if TK.qasm_str[i] == "X":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_X, 0, 0, 1, "X"))
                    i += 1
                    continue
            
            # Check for Y
            if TK.qasm_str[i] == "Y":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_Y, 0, 0, 1, "Y"))
                    i += 1
                    continue
            
            # Check for Z
            if TK.qasm_str[i] == "Z":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_Z, 0, 0, 1, "Z"))
                    i += 1
                    continue
            
            # Check for S
            if TK.qasm_str[i] == "S":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_S, 0, 0, 1, "S"))
                    i += 1
                    continue
            
            # Check for T
            if TK.qasm_str[i] == "T":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_T, 0, 0, 1, "T"))
                    i += 1
                    continue
            
            # Check for Rtheta
            if TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "T" and TK.qasm_str[i+2] == "H" and TK.qasm_str[i+3] == "E" and TK.qasm_str[i+4] == "T" and TK.qasm_str[i+5] == "A":
                if TK.qasm_str[i+6] == "(":
                    TK.Token.append((TK_RTHETA, 0, 0, 6, "RTHETA"))
                    i += 6
                    continue

            # Check for RX
            if TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "X":
                if TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_RX, 0, 0, 2, "RX"))
                    i += 2
                    continue
            
            # Check for RY
            if TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "Y":
                if TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_RY, 0, 0, 2, "RY"))
                    i += 2
                    continue
            
            # Check for RZ
            if TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "Z":
                if TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_RZ, 0, 0, 2, "RZ"))
                    i += 2
                    continue
            
            # Check for H
            if TK.qasm_str[i] == "H":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_H, 0, 0, 1, "H"))
                    i += 1
                    continue
            
            # Check for CX
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "X":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CX, 0, 0, 2, "CX"))
                    i += 2
                    continue
            
            # Check for CY
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "Y":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CY, 0, 0, 2, "CY"))
                    i += 2
                    continue
            
            # Check for CZ
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "Z":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CZ, 0, 0, 2, "CZ"))
                    i += 2
                    continue
            
            # Check for CU
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "U":
                if TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_CU, 0, 0, 2, "CU"))
                    i += 2
                    continue
            
            # Check for CS
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "S":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CS, 0, 0, 2, "CS"))
                    i += 2
                    continue
            
            # Check for CT
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "T":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CT, 0, 0, 2, "CT"))
                    i += 2
                    continue
            
            # Check for CRtheta
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "T" and TK.qasm_str[i+3] == "H" and TK.qasm_str[i+4] == "E" and TK.qasm_str[i+5] == "T" and TK.qasm_str[i+6] == "A":
                if TK.qasm_str[i+7] == "(":
                    TK.Token.append((TK_CRTHETA, 0, 0, 7, "CRTHETA"))
                    i += 7
                    continue
            
            # Check for CRX
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "X":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_CRX, 0, 0, 3, "CRX"))
                    i += 3
                    continue
            
            # Check for CRY
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "Y":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_CRY, 0, 0, 3, "CRY"))
                    i += 3
                    continue
            
            # Check for CRZ
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "Z":
                if TK.qasm_str[i+3] == "(":
                    TK.Token.append((TK_CRZ, 0, 0, 3, "CRZ"))
                    i += 3
                    continue
            
            # Check for CH
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "H":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CH, 0, 0, 2, "CH"))
                    i += 2
                    continue
            
            # Check for ident
            if TK.is_alnum(TK.qasm_str[i]):
                ident = TK.qasm_str[i]
                i += 1
                while TK.is_alnum(TK.qasm_str[i]) or TK.qasm_str[i].isdigit():
                    ident += TK.qasm_str[i]
                    i += 1
                TK.Token.append((TK_IDENT, 0, 0, len(ident), ident))
                continue
            
            # Check for number
            if TK.qasm_str[i].isdigit() or (TK.qasm_str[i] == "." and TK.qasm_str[i+1].isdigit()):
                i_init = i
                num = ""
                exp = 0
                while TK.qasm_str[i].isdigit() or TK.qasm_str[i] == ".":
                    num += TK.qasm_str[i]
                    i += 1
                if TK.qasm_str[i] == "e" or TK.qasm_str[i] == "E":
                    if TK.qasm_str[i+1] == "+" and TK.qasm_str[i+2].isdigit():
                        i += 2
                        while TK.qasm_str[i].isdigit():
                            exp = 10*exp + int(TK.qasm_str[i])
                            i += 1
                    elif TK.qasm_str[i+1] == "-" and TK.qasm_str[i+2].isdigit():
                        i += 2
                        while TK.qasm_str[i].isdigit():
                            exp = 10*exp - int(TK.qasm_str[i])
                            i += 1
                    elif TK.qasm_str[i+1].isdigit():
                        i += 1
                        while TK.qasm_str[i].isdigit():
                            exp = 10*exp + int(TK.qasm_str[i])
                            i += 1
                    else:
                        raise Exception("Invalid number")
                TK.Token.append((TK_NUM, float(num), float(exp), i-i_init, TK.qasm_str[i_init:i]))
                continue
            
            raise Exception("Invalid character, cannot Tokenize!")
        
        return TK.Token


filepath = "qsofinstr/check.qasm"
TK = Token.Tokenize(filepath)
# print(TK.qasm_str)
print(TK)