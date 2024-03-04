import sys
from pathlib import Path

TK_OPERATOR = 0
TK_NUM = 1
TK_IDENT = 2
TK_PI = 3
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
TK_EOF = 34
TK_SIN = 35
TK_COS = 36
TK_TAN = 37
TK_LN = 38
TK_SQRT = 39
TK_EXP = 40
TK_U1 = 41
TK_U2 = 42
TK_ID = 43
TK_SDG = 44
TK_TDG = 45
TK_CCX = 46
TK_CU1 = 47


class Token(object):
    def __init__(self):
        self.qasm_str = ""
        # The element is a tuple with the structure (kind, val, exp, len, str)
        # The value is represented as scientific notation, therefore needs val and exp parts
        self.Token = []    
        self.name = ""   
        self.line_count = 1
        self.err_line_idx = 0
        self.kind_idx = 0
        self.val_idx = 1
        self.exp_idx = 2
        self.len_idx = 3
        self.str_idx = 4
        self.line_count_idx = 5
        self.err_line_idx_idx = 6
        self.idx_idx = 7
        # The list of the files
        self.include_file_list = []
        
    def file2str(self, filename0):
        root_dir = Path(__file__).resolve().parents[2]
        filename = root_dir / filename0
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
        TK.name = filename
        i = 0
        while i < len(TK.qasm_str):
            # Skip whitespace
            if TK.qasm_str[i].isspace() or TK.qasm_str[i] == "\t" or TK.qasm_str[i] == "\n":
                if TK.qasm_str[i] == "\n":
                    TK.line_count += 1
                    TK.err_line_idx = i+1
                i += 1
                continue
            # Check for a comment
            if TK.qasm_str[i] == "/":
                if TK.qasm_str[i+1] == "/":
                    i += 2
                    while (i < len(TK.qasm_str)) and TK.qasm_str[i] != "\n":
                        i += 1
                    continue
            # Get rid of OPENQASM 2.0
            if TK.qasm_str[i]=="O" and TK.qasm_str[i+1]=="P" and TK.qasm_str[i+2]=="E" and TK.qasm_str[i+3]=="N" and TK.qasm_str[i+4]=="Q" and TK.qasm_str[i+5]=="A" and TK.qasm_str[i+6]=="S" and TK.qasm_str[i+7]=="M":
                # Skip the spaces to find 2.0
                i += 8
                while (i < len(TK.qasm_str)) and TK.qasm_str[i].isspace():
                    i += 1
                # Check for 2.0
                if len(TK.qasm_str) - i < 2:
                    TK.annotate_error(TK.name, TK.qasm_str, i, "The version of OpenQASM should be 2.0", TK.line_count, TK.err_line_idx)
                if (TK.qasm_str[i] != "2") and (TK.qasm_str[i+1] != ".") and (TK.qasm_str[i+2] != "0"):
                    TK.annotate_error(TK.name, TK.qasm_str, i, "The version of OpenQASM should be 2.0", TK.line_count, TK.err_line_idx)
                i += 2
                # Check for missing ; if the current token index is at the end of the file
                if i == len(TK.qasm_str)-1:
                    TK.annotate_error(TK.name, TK.qasm_str, i, "Expect ;", TK.line_count, TK.err_line_idx)
                # Skip the spaces to find ;
                i += 1
                while (i < len(TK.qasm_str)) and TK.qasm_str[i].isspace():
                    i += 1
                # Check for ;
                if TK.qasm_str[i] != ";":
                    TK.annotate_error(TK.name, TK.qasm_str, i, "Expect ;", TK.line_count, TK.err_line_idx)
                i += 1
                continue
            
            # Check for include files
            if TK.qasm_str[i]=="i"and TK.qasm_str[i+1]=="n"and TK.qasm_str[i+2]=="c"and TK.qasm_str[i+3]=="l"and TK.qasm_str[i+4]=="u"and TK.qasm_str[i+5]=="d"and TK.qasm_str[i+6]=="e":
                if TK.qasm_str[i+7].isspace() or TK.qasm_str[i+7]=="\"":
                    i += 7
                    # Skip whitespaces
                    while (i < len(TK.qasm_str)) and (TK.qasm_str[i].isspace()):
                        i += 1
                    # Check for "
                    if TK.qasm_str[i] != "\"":
                        TK.annotate_error(TK.name, TK.qasm_str, i, "Expect \"", TK.line_count, TK.err_line_idx)
                    i += 1
                    # Get the filename
                    filename = ""
                    file_i = i
                    while (i < len(TK.qasm_str)) and (TK.qasm_str[i] != "\""):
                        filename += TK.qasm_str[i]
                        i += 1
                    # Check whether the file exists
                    file_path = Path(filename)
                    if not file_path.exists():
                        # Skip the include "qelib1.inc";
                        if filename != "qelib1.inc":
                            TK.annotate_error(TK.name, TK.qasm_str, file_i, "File not found", TK.line_count, TK.err_line_idx)
                    i += 1
                    # Skip whitespaces
                    while (i < len(TK.qasm_str)) and (TK.qasm_str[i].isspace()):
                        i += 1
                    # Check for ;
                    if TK.qasm_str[i] != ";":
                        TK.annotate_error(TK.name, TK.qasm_str, i, "Expect ;", TK.line_count, TK.err_line_idx)
                    i += 1
                    # Add the file to the list
                    TK.include_file_list.append(filename)
                    continue
                    
            # Check for ;
            if TK.qasm_str[i] == ";":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, ";", TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for : this is for separate the control qubits and target qubit of multi-qubit controlled gates
            if TK.qasm_str[i] == ":":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, ":", TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for ,
            if TK.qasm_str[i] == ",":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, ",", TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for {
            if TK.qasm_str[i] == "{":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, "{", TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for }
            if TK.qasm_str[i] == "}":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, "}", TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for ->
            if TK.qasm_str[i] == "-" and TK.qasm_str[i+1] == ">":
                if TK.qasm_str[i+2].isspace() or (TK.is_alnum(TK.qasm_str[i+2]) and TK.qasm_str[i+2] != "_"):
                    TK.Token.append((TK_OPERATOR, 0, 0, 2, "->", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for ==
            if TK.qasm_str[i] == "=" and TK.qasm_str[i+1] == "=":
                if TK.qasm_str[i+2].isspace() or TK.qasm_str[i+2].isdigit():
                    TK.Token.append((TK_OPERATOR, 0, 0, 2, "==", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for some operators
            if TK.qasm_str[i] == "+" or TK.qasm_str[i] == "-" or TK.qasm_str[i] == "*" or TK.qasm_str[i] == "/" or TK.qasm_str[i] == "^" or TK.qasm_str[i] == "(" or TK.qasm_str[i] == ")":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, TK.qasm_str[i], TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for []
            if TK.qasm_str[i] == "[" or TK.qasm_str[i] == "]":
                TK.Token.append((TK_OPERATOR, 0, 0, 1, TK.qasm_str[i], TK.line_count, TK.err_line_idx, i))
                i += 1
                continue
            
            # Check for +
            if TK.qasm_str[i] == "+":
                if TK.qasm_str[i+1].isspace() or TK.qasm_str[i+1].isdigit() or TK.qasm_str[i+1] == ".":
                    TK.Token.append((TK_OPERATOR, 0, 0, 1, "+", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for -
            if TK.qasm_str[i] == "-":
                if TK.qasm_str[i+1].isspace() or TK.qasm_str[i+1].isdigit() or TK.qasm_str[i+1] == ".":
                    TK.Token.append((TK_OPERATOR, 0, 0, 1, "-", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for *
            if TK.qasm_str[i] == "*":
                if TK.qasm_str[i+1].isspace() or TK.qasm_str[i+1].isdigit() or TK.qasm_str[i+1] == ".":
                    TK.Token.append((TK_OPERATOR, 0, 0, 1, "*", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for /
            if TK.qasm_str[i] == "/":
                if TK.qasm_str[i+1].isspace() or TK.qasm_str[i+1].isdigit() or TK.qasm_str[i+1] == ".":
                    TK.Token.append((TK_OPERATOR, 0, 0, 1, "/", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for ^
            if TK.qasm_str[i] == "^":
                if TK.qasm_str[i+1].isspace() or TK.qasm_str[i+1].isdigit() or TK.qasm_str[i+1] == ".":
                    TK.Token.append((TK_OPERATOR, 0, 0, 1, "^", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for pi
            if TK.qasm_str[i] == "p" and TK.qasm_str[i+1] == "i":
                if not TK.is_alnum(TK.qasm_str[i+2]):
                    TK.Token.append((TK_PI, 0, 0, 2, "pi", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for sin
            if TK.qasm_str[i] == "s" and TK.qasm_str[i+1] == "i" and TK.qasm_str[i+2] == "n":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_SIN, 0, 0, 3, "sin", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for cos
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "o" and TK.qasm_str[i+2] == "s":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_COS, 0, 0, 3, "cos", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for tan
            if TK.qasm_str[i] == "t" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "n":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_TAN, 0, 0, 3, "tan", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for exp
            if TK.qasm_str[i] == "e" and TK.qasm_str[i+1] == "x" and TK.qasm_str[i+2] == "p":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_EXP, 0, 0, 3, "exp", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for ln
            if TK.qasm_str[i] == "l" and TK.qasm_str[i+1] == "n":
                if TK.qasm_str[i+2] == "(" or TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_LN, 0, 0, 2, "ln", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for sqrt
            if TK.qasm_str[i] == "s" and TK.qasm_str[i+1] == "q" and TK.qasm_str[i+2] == "r" and TK.qasm_str[i+3] == "t":
                if TK.qasm_str[i+4] == "(" or TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_SQRT, 0, 0, 4, "sqrt", TK.line_count, TK.err_line_idx, i))
                    i += 4
                    continue
            
            # Check for gate
            if TK.qasm_str[i] == "g" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "t" and TK.qasm_str[i+3] == "e":
                if TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_GATE, 0, 0, 4, "gate", TK.line_count, TK.err_line_idx, i))
                    i += 4
                    continue
            
            # Check for measure 
            if TK.qasm_str[i] == "m" and TK.qasm_str[i+1] == "e" and TK.qasm_str[i+2] == "a" and TK.qasm_str[i+3] == "s" and TK.qasm_str[i+4] == "u" and TK.qasm_str[i+5] == "r" and TK.qasm_str[i+6] == "e":
                if TK.qasm_str[i+7].isspace():
                    TK.Token.append((TK_MEASURE, 0, 0, 7, "measure", TK.line_count, TK.err_line_idx, i))
                    i += 7
                    continue
            
            # Check for if
            if TK.qasm_str[i] == "i" and TK.qasm_str[i+1] == "f":
                if TK.qasm_str[i+2].isspace() or TK.qasm_str[i+2] == "(":
                    TK.Token.append((TK_IF, 0, 0, 2, "if", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for reset
            if TK.qasm_str[i] == "r" and TK.qasm_str[i+1] == "e" and TK.qasm_str[i+2] == "s" and TK.qasm_str[i+3] == "e" and TK.qasm_str[i+4] == "t":
                if TK.qasm_str[i+5].isspace():
                    TK.Token.append((TK_RESET, 0, 0, 5, "reset", TK.line_count, TK.err_line_idx, i))
                    i += 5
                    continue
            
            # Check for barrier
            if TK.qasm_str[i] == "b" and TK.qasm_str[i+1] == "a" and TK.qasm_str[i+2] == "r" and TK.qasm_str[i+3] == "r" and TK.qasm_str[i+4] == "i" and TK.qasm_str[i+5] == "e" and TK.qasm_str[i+6] == "r":
                if TK.qasm_str[i+7].isspace():
                    TK.Token.append((TK_BARRIER, 0, 0, 7, "barrier", TK.line_count, TK.err_line_idx, i))
                    i += 7
                    continue
            
            # Check for opaque
            if TK.qasm_str[i] == "o" and TK.qasm_str[i+1] == "p" and TK.qasm_str[i+2] == "a" and TK.qasm_str[i+3] == "q" and TK.qasm_str[i+4] == "u" and TK.qasm_str[i+5] == "e":
                if TK.qasm_str[i+6].isspace():
                    TK.Token.append((TK_OPAQUE, 0, 0, 6, "opaque", TK.line_count, TK.err_line_idx, i))
                    i += 6
                    continue
            
            # Check for qreg
            if TK.qasm_str[i] == "q" and TK.qasm_str[i+1] == "r" and TK.qasm_str[i+2] == "e" and TK.qasm_str[i+3] == "g":
                if TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_QREG, 0, 0, 4, "qreg", TK.line_count, TK.err_line_idx, i))
                    i += 4
                    continue
            
            # Check for creg
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "r" and TK.qasm_str[i+2] == "e" and TK.qasm_str[i+3] == "g":
                if TK.qasm_str[i+4].isspace():
                    TK.Token.append((TK_CREG, 0, 0, 4, "creg", TK.line_count, TK.err_line_idx, i))
                    i += 4
                    continue
            
            # Check for id
            if TK.qasm_str[i] == "i" and TK.qasm_str[i+1] == "d":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_ID, 0, 0, 2, "id", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for sdg
            if TK.qasm_str[i] == "s" and TK.qasm_str[i+1] == "d" and TK.qasm_str[i+2] == "g":
                if TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_SDG, 0, 0, 3, "sdg", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for tdg
            if TK.qasm_str[i] == "t" and TK.qasm_str[i+1] == "d" and TK.qasm_str[i+2] == "g":
                if TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_TDG, 0, 0, 3, "tdg", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for U
            if TK.qasm_str[i] == "U":
                if (TK.qasm_str[i+1] == "(") or (TK.qasm_str[i+1].isspace()):
                    TK.Token.append((TK_U, 0, 0, 1, "U", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for U3
            if TK.qasm_str[i] == "u" and TK.qasm_str[i+1] == "3":
                if (TK.qasm_str[i+2] == "(") or (TK.qasm_str[i+2].isspace()):
                    TK.Token.append((TK_U, 0, 0, 1, "U", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for U1
            if TK.qasm_str[i] == "u" and TK.qasm_str[i+1] == "1":
                if (TK.qasm_str[i+2] == "(") or (TK.qasm_str[i+2].isspace()):
                    TK.Token.append((TK_U1, 0, 0, 2, "U1", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for U2
            if TK.qasm_str[i] == "u" and TK.qasm_str[i+1] == "2":
                if (TK.qasm_str[i+2] == "(") or (TK.qasm_str[i+2].isspace()):
                    TK.Token.append((TK_U2, 0, 0, 2, "U2", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for X
            if TK.qasm_str[i] == "X" or TK.qasm_str[i] == "x":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_X, 0, 0, 1, "X", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for Y
            if TK.qasm_str[i] == "Y" or TK.qasm_str[i] == "y":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_Y, 0, 0, 1, "Y", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for Z
            if TK.qasm_str[i] == "Z" or TK.qasm_str[i] == "z":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_Z, 0, 0, 1, "Z", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for S
            if TK.qasm_str[i] == "S" or TK.qasm_str[i] == "s":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_S, 0, 0, 1, "S", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for T
            if TK.qasm_str[i] == "T" or TK.qasm_str[i] == "t":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_T, 0, 0, 1, "T", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for Rtheta
            if TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "T" and TK.qasm_str[i+2] == "H" and TK.qasm_str[i+3] == "E" and TK.qasm_str[i+4] == "T" and TK.qasm_str[i+5] == "A":
                if TK.qasm_str[i+6] == "(" or TK.qasm_str[i+6].isspace():
                    TK.Token.append((TK_RTHETA, 0, 0, 6, "RTHETA", TK.line_count, TK.err_line_idx, i))
                    i += 6
                    continue
            
            # Check for RX
            if (TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "X") or (TK.qasm_str[i]=="r" and TK.qasm_str[i+1]=="x"):
                if TK.qasm_str[i+2] == "(" or TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_RX, 0, 0, 2, "RX", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for RY
            if (TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "Y") or (TK.qasm_str[i]=="r" and TK.qasm_str[i+1]=="y"):
                if TK.qasm_str[i+2] == "(" or TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_RY, 0, 0, 2, "RY", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for RZ
            if (TK.qasm_str[i] == "R" and TK.qasm_str[i+1] == "Z") or (TK.qasm_str[i]=="r" and TK.qasm_str[i+1]=="z"):
                if TK.qasm_str[i+2] == "(" or TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_RZ, 0, 0, 2, "RZ", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for H
            if TK.qasm_str[i] == "H" or TK.qasm_str[i] == "h":
                if TK.qasm_str[i+1].isspace():
                    TK.Token.append((TK_H, 0, 0, 1, "H", TK.line_count, TK.err_line_idx, i))
                    i += 1
                    continue
            
            # Check for CX
            if (TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "X") or (TK.qasm_str[i]=="c" and TK.qasm_str[i+1]=="x"):
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CX, 0, 0, 2, "CX", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for CCX 
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "c" and TK.qasm_str[i+2] == "x":
                if TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CCX, 0, 0, 3, "CCX", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for CY
            if (TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "Y") or (TK.qasm_str[i]=="c" and TK.qasm_str[i+1]=="y"):
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CY, 0, 0, 2, "CY", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for CZ
            if (TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "Z") or (TK.qasm_str[i]=="c" and TK.qasm_str[i+1]=="z"):
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CZ, 0, 0, 2, "CZ", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for CU
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "U":
                if TK.qasm_str[i+2] == "(" or TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CU, 0, 0, 2, "CU", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for cu3
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "u" and TK.qasm_str[i+2] == "3":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CU, 0, 0, 2, "CU", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for cu1
            if TK.qasm_str[i] == "c" and TK.qasm_str[i+1] == "u" and TK.qasm_str[i+2] == "1":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CU1, 0, 0, 3, "CU1", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for CS
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "S":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CS, 0, 0, 2, "CS", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for CT
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "T":
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CT, 0, 0, 2, "CT", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for CRtheta
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "T" and TK.qasm_str[i+3] == "H" and TK.qasm_str[i+4] == "E" and TK.qasm_str[i+5] == "T" and TK.qasm_str[i+6] == "A":
                if TK.qasm_str[i+7] == "(" or TK.qasm_str[i+7].isspace():
                    TK.Token.append((TK_CRTHETA, 0, 0, 7, "CRTHETA", TK.line_count, TK.err_line_idx, i))
                    i += 7
                    continue
            
            # Check for CRX
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "X":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CRX, 0, 0, 3, "CRX", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for CRY
            if TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "Y":
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CRY, 0, 0, 3, "CRY", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for CRZ
            if (TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "R" and TK.qasm_str[i+2] == "Z") or (TK.qasm_str[i]=="c" and TK.qasm_str[i+1]=="r" and TK.qasm_str[i+2]=="z"):
                if TK.qasm_str[i+3] == "(" or TK.qasm_str[i+3].isspace():
                    TK.Token.append((TK_CRZ, 0, 0, 3, "CRZ", TK.line_count, TK.err_line_idx, i))
                    i += 3
                    continue
            
            # Check for CH
            if (TK.qasm_str[i] == "C" and TK.qasm_str[i+1] == "H") or (TK.qasm_str[i]=="c" and TK.qasm_str[i+1]=="h"):
                if TK.qasm_str[i+2].isspace():
                    TK.Token.append((TK_CH, 0, 0, 2, "CH", TK.line_count, TK.err_line_idx, i))
                    i += 2
                    continue
            
            # Check for ident
            if TK.is_alnum(TK.qasm_str[i]):
                ident = TK.qasm_str[i]
                err_i = i
                i += 1
                while (i < len(TK.qasm_str))and(TK.is_alnum(TK.qasm_str[i]) or TK.qasm_str[i].isdigit()):
                    ident += TK.qasm_str[i]
                    i += 1
                TK.Token.append((TK_IDENT, 0, 0, len(ident), ident, TK.line_count, TK.err_line_idx, err_i))
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
                        TK.annotate_error(TK.name, TK.qasm_str, i, "Invalid number", TK.line_count, TK.err_line_idx)
                TK.Token.append((TK_NUM, float(num), float(exp), i-i_init, TK.qasm_str[i_init:i], TK.line_count, TK.err_line_idx, i_init))
                continue
            
            # raise Exception("Invalid character, cannot Tokenize!")
            TK.annotate_error(TK.name, TK.qasm_str, i, "Invalid character, cannot Tokenize!", TK.line_count, TK.err_line_idx)
        TK.Token.append((TK_EOF, 0, 0, 0, "EOF", TK.line_count, TK.err_line_idx, i))
        return TK.name, TK.qasm_str, TK.Token, TK.include_file_list
    
    @staticmethod
    def make_string_red(input_string):
        return "\033[91m" + input_string + "\033[0m"

    @staticmethod
    def annotate_error(string_name, input_string, error_index, error_message, line_idx, line_start):
        # Check if the index is within the bounds of the string
        if error_index < 0 or error_index > len(input_string):
            raise ValueError("Error index out of bounds")
        # Find the end index of the line containing the error
        line_end = 0
        while ((error_index+line_end) < len(input_string)) and (input_string[error_index+line_end] != "\n"):
            line_end += 1
        # Prepare the error annotation
        # string_init = f"[line: "{line_idx}"] "
        string_init = f"[file: {string_name}] "+f"[line: \"{line_idx}\"] "
        input_line = string_init + input_string[line_start:error_index+line_end]
        hat_line = " "*(len(string_init)+error_index-line_start) + Token.make_string_red("^")
        err_line = " "*(len(string_init)+error_index-line_start) + Token.make_string_red(error_message+"!")
        # Combine and return the annotated string
        annotated_string = input_line + "\n" + hat_line + "\n" + err_line
        sys.exit(annotated_string)


# filepath = "qsofinstr/check.qasm"
# str, TK = Token.Tokenize(filepath)
# # print(TK.qasm_str)
# # print(str)
# print(TK)