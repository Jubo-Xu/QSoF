from token import Token
import token
from quantumcircuit import Quantum_circuit
from quantumcircuit import Time_slice_node
import quantumcircuit
import math
from collections import deque

# Define the node kinds
ND_NUM = 0
ND_QREG = 1
ND_CREG = 2
ND_OPAQUE = 3
ND_IF = 4
ND_EQUAL = 5
ND_QREG_DEC = 6
ND_CREG_DEC = 7
ND_GATE_DEC = 8
ND_MEASURE = 9
ND_RESET = 10
ND_U = 11
ND_CX = 12
ND_X = 13
ND_Y = 14
ND_Z = 15
ND_S = 16
ND_T = 17
ND_RTHETA = 18
ND_RX = 19
ND_RY = 20
ND_RZ = 21
ND_H = 22
ND_CY = 23 
ND_CZ = 24
ND_CU = 25
ND_CS = 26
ND_CT = 27
ND_CRTHETA = 28
ND_CRX = 29
ND_CRY = 30
ND_CRZ = 31
ND_CH = 32
ND_GATE_NOEXP = 33
ND_GATE_EXP = 34
ND_SUB = 35
ND_ADD = 36
ND_MUL = 37
ND_DIV = 38
ND_POW = 39
ND_EXP = 40
ND_SIN = 41
ND_COS = 42
ND_TAN = 43
ND_LN = 44
ND_SQRT = 45
ND_PI = 46
ND_IDENT = 47
ND_EXP_LIST = 48
ND_BARRIER = 49
ND_U1 = 50
ND_U2 = 51
ND_SDG = 52
ND_TDG = 53
ND_CCX = 54
ND_OPAQUE_NOEXP = 55
ND_OPAQUE_EXP = 56
# Dictionary for binary operator precedences
binop_precedence = {
    ",": -1,
    ")": -1,
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "^": 3
}

class Node:
    def __init__(self, kind):
        self.kind = kind
        self.val = 0
        self.str = ""
        # The qregs is a list of tuples, where each tuple is (name, index), if the index is -1, then it's not indexed
        self.qregs = []
        # The cregs has the same form as qregs
        self.cregs = []
        self.left = None
        self.right = None
        self.controlled_with_parameter = False # This is a flag to indicate whether the gate is controlled with parameter, mainly for circuit generation
    
    def add_str(self, str):
        self.str = str
    
    def add_left(self, node):
        self.left = node
    
    def add_right(self, node):
        self.right = node

class Opaque:
    def __init__(self, name):
        self.name = name
        self.params = []
        self.args = []
    
    def add_params(self, param):
        if isinstance(param, list):
            self.params.extend(param)
        else:
            self.params.append(param)

    def add_args(self, arg):
        if isinstance(arg, list):
            self.args.extend(arg)
        else:
            self.args.append(arg)

class Gate:
    def __init__(self, name):
        self.name = name
        self.params = None
        self.args = None
        self.contents = []
        self.filename = ""
    
    def add_params(self, param):
        # The parameters of Gate declaration is a dictionary, which is used for two things: 
        # 1. check whether the parameter is defined for the gate operations inside the contents
        # 2. easy to replace the parameter with the actual value during the code generation
        if isinstance(param, list):
            self.params = {}
            for i in range(len(param)):
                self.params[param[i]] = 0
        else:
            self.params = {param: 0}
    
    def add_args(self, arg):
        # The arguments of Gate declaration is a dictionary, which is served for the same purpose as the parameters
        if isinstance(arg, list):
            self.args = {}
            for i in range(len(arg)):
                # The value of the argument is a tuple, where the first element is the qreg name, and the second element is the index, if the index is -1, then it's not indexed
                self.args[arg[i][0]] = ()
        else:
            self.args = {arg[0]: ()}
    
    def add_contents(self, content_node):
        self.contents.append(content_node)
    
    def add_filename(self, filename):
        self.filename = filename

# The expressions would be represented as a list, where each element is a binary operation node
class Explist(Node):
    def __init__(self, kind):
        super().__init__(kind)
        self.exps = []
    
    def add_exps(self, exp):
        if isinstance(exp, list):
            self.exps.extend(exp)
        else:
            self.exps.append(exp)


# The class for the filesystem
class Filesystem:
    def __init__(self, filename, input_str, TK):
        self.name = filename
        self.file_str = input_str # The string of the file
        self.token = TK # The token list of the file
        self.token_idx = 0 # The index of the current token list
        self.PARSE_FINISH = False # The flag to indicate whether the parsing is finished
        self.include_dict = None # The dictionary for the include files of current file
    
    def set_include_dict(self, dic):
        self.include_dict = {file: None for file in dic}


class Parser(Token):
    def __init__(self, filenode):
        super().__init__()
        # Set up the Hash table for opaques, qregs, and cregs
        # For opaques, the key is the name of the opaque, and the element is a tuple of 
        self.opaques = {}
        self.qregs = {}
        self.cregs = {}
        self.gates = {}
        self.code = []
        # This is a flag to indicate whether the current state is a gate definition, which is 
        # mainly used for some error checks
        self.GATE_define = False 
        # This is a flag to indicate whether the current state is a gate declaration, which is 
        # mainly used for the error checks for whether the number of parameters sent is correct
        self.GATE_declare = False
        # This is a flag to indicate whether the current state is an opaque declaration, which serves
        # as the same purpose as the GATE_declare flag
        self.OPAQUE_declare = False
        # This is a flag to indicate that the current state is a Measurement operation
        self.MEASURE = False
        # This is a flag to indicate that the current state is a Reset operation
        self.RESET = False
        # This is a flag to indicate that the current state has the if condition, which is used for circuit generation
        self.IF = False
        self.IF_creg = None
        self.IF_num = 0
        # This variable is used in together with the Gate declare and Opaque declare flags
        self.GATE_name = ""
        # This variable is used for the gate definition
        self.GATE_DEF_name = ""
        # This variable is used for the supported gate 
        self.GATE_name_support = ""
        # The current file node for parsing
        self.current_file = filenode
        self.gate_name_find = "" # The gate name that needs to be found
        self.file_need_find = filenode
        self.GATE_FOUND = True # The flag to indicate whether the gate is found
        # The dictionary for the multi-controlled qubits, where the key is the qubit name, and the element is the index of the qubit
        self.MULTI_CONTROL_QUBITS = {}
        
        
    @staticmethod
    def create_node(kind, leftnode=None, rightnode=None):
        node = Node(kind)
        node.add_left(leftnode)
        node.add_right(rightnode)
        return node
    
    @staticmethod
    def create_node_num(val):
        node = Node(ND_NUM)
        node.val = val
        return node
    
    @staticmethod
    def create_node_qreg(qreg):
        node = Node(ND_QREG)
        if isinstance(qreg, list):
            node.qregs.extend(qreg)
        else:
            node.qregs.append(qreg)
        return node
    
    @staticmethod
    def create_node_creg(creg):
        node = Node(ND_CREG)
        if isinstance(creg, list):
            node.cregs.extend(creg)
        else:
            node.cregs.append(creg)
        return node
    
    @staticmethod
    def create_node_explist(exp):
        node = Explist(ND_EXP_LIST)
        node.add_exps(exp)
        return node
    
    def expect(self, op):
        if self.current_file.token[self.current_file.token_idx][self.kind_idx] != token.TK_OPERATOR or self.current_file.token[self.current_file.token_idx][self.str_idx] != op:
            Token.annotate_error(self.current_file.name, self.current_file.file_str, self.current_file.token[self.current_file.token_idx-1][self.idx_idx], "missing operator: "\
                + op, self.current_file.token[self.current_file.token_idx-1][self.line_count_idx], self.current_file.token[self.current_file.token_idx-1][self.err_line_idx_idx])
        self.current_file.token_idx += 1
        
    def consume_operator_str(self, op):
        if self.current_file.token[self.current_file.token_idx][self.kind_idx] != token.TK_OPERATOR or self.current_file.token[self.current_file.token_idx][self.str_idx] != op:
            return False
        self.current_file.token_idx += 1
        return True
    
    def check_TK_kind(self, idx):
        return self.current_file.token[idx][self.kind_idx]

    def check_operator_str(self, idx, str):
        return self.current_file.token[idx][self.kind_idx] == token.TK_OPERATOR and self.current_file.token[idx][self.str_idx] == str
    
    def error_at(self, idx, message):
        Token.annotate_error(self.current_file.name, self.current_file.file_str, self.current_file.token[idx][self.idx_idx], message, self.current_file.token[idx][self.line_count_idx], self.current_file.token[idx][self.err_line_idx_idx])
    
    def check_num_error(self, name):
        # Check whether the qreg or creg size is missing or wrong type is used
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_NUM:
            if self.check_operator_str(self.current_file.token_idx, "]"):
                self.error_at(self.current_file.token_idx, "There has to be a number for the "+name)
            else:
                self.error_at(self.current_file.token_idx, "The "+name+" should be a number")
        # Check whether the qreg or creg size is an integer
        if self.current_file.token[self.current_file.token_idx][self.val_idx] != int(self.current_file.token[self.current_file.token_idx][self.val_idx]) or self.current_file.token[self.current_file.token_idx][self.exp_idx] != 0:
            self.error_at(self.current_file.token_idx, "The "+name+" should be an integer")
    
    def get_next_token(self, i=1):
        self.current_file.token_idx += i
    
    # Define the function for checking the included files if the gate declared is not defined in current file
    def check_include_files_current(self, filenode):
        # should iterate through all the child files layer by layer
        for file in filenode.include_dict:
            # if the file is not tokenized, first tokenize it
            if filenode.include_dict[file] is None:
                filename, file_str, TK, include_dic = Token.Tokenize(file)
                file_node = Filesystem(filename, file_str, TK)
                file_node.set_include_dict(include_dic)
                filenode.include_dict[file] = file_node
            # if the file is already completely parsed, then skip it
            if filenode.include_dict[file].token[filenode.include_dict[file].token_idx][self.kind_idx] == token.TK_EOF:
                continue
            # parsing the file and if the gate definition is found, the while loop will be terminated
            # set the current filenode of the parser to this file
            self.current_file = filenode.include_dict[file]
            while (not self.GATE_FOUND) and (filenode.include_dict[file].token[filenode.include_dict[file].token_idx][self.kind_idx] != token.TK_EOF):
                self.statement()
            # if the gate is found, then return True
            if self.GATE_FOUND:
                return True
        # if all the included files of current file are checked and the gate is not found, then return False
        return False
    
    # The basic logic of searching the gate is to first check whether the gate is defined in the included files of current file,
    # if not, then check whether the gate is defined in the included files of the included files of current file, and so on. So it's
    # a recursive checking of the tree-structured filesystem layer by layer, that's because normally the gate used is defined in the 
    # included files of the current file, so it's more efficient to check the included files of current file first. Based on this logic,
    # Breadth-first search(BFS) algorithm is used here.
    def check_included_files(self, filenode):
        # starting from the current file
        queue_file = deque([filenode])
        
        while queue_file:
            # pop the first element in the queue
            current_filenode = queue_file.popleft()
            # visiting the current file
            # if the gate is found, then directly return True
            if self.check_include_files_current(current_filenode):
                return True
            # add the included files of current file to the queue
            for file in current_filenode.include_dict:
                queue_file.append(current_filenode.include_dict[file])
        # if all the files are checked and the gate is not found, then return False
        return False
        
            
    
    ### Recursive descent parsing ###
    ''' BNF of modified OpenQASM
    mainprogram := OPENQASM real; program
    program     := statement | program statement
    statement   := decl 
                   | gatedecl 
                   | opaque id idlist ;
                   | opaque id "(" ")" idlist ";" | opaque id "("idlist")" idlist ";"
                   | qop
                   | if "("condition")" qop
                   | barrier idlist ";"
    condition   := id == nninteger

    decl        := qreg id "["nninteger"]" ";" | creg id "["nninteger"]" ";"
    gatedecl    := gate id idlist "{" goplist "}"
                   | gate id "("")" idlist "{"goplist"}"
                   | gate id "("idlist")" idlist "{"goplist"}"
    goplist     := uop 
                   | goplist uop 
    qop         := uop 
                   | measure argument "->" argument_c ";"
                   | reset argument ";"
    uop         := U "("explist")" argument ";"
                   | CX argument "," argument ";"
                   | CX idlist ":" argument ";"
                   | X argument ";"
                   | Y argument ";"
                   | Z argument ";"
                   | S argument ";"
                   | T argument ";"
                   | RTHETA "("explist")" argument ";"
                   | RX "("explist")" argument ";"
                   | RY "("explist")" argument ";"
                   | RZ "("explist")" argument ";"
                   | H argument ";"
                   | CY argument "," argument ";"
                   | CY idlist ":" argument ";"
                   | CZ argument "," argument ";"
                   | CZ idlist ":" argument ";"
                   | CU "("explist")" argument "," argument ";"
                   | CU "("explist")" idlist ":" argument ";"
                   | CS argument "," argument ";"
                   | CS idlist ":" argument ";"
                   | CT argument "," argument ";"
                   | CT idlist ":" argument ";"
                   | CRTHETA "("explist")" argument "," argument ";"
                   | CRTHETA "("explist")" idlist ":" argument ";"
                   | CRX "("explist")" argument "," argument ";"
                   | CRX "("explist")" idlist ":" argument ";"
                   | CRY "("explist")" argument "," argument ";"
                   | CRY "("explist")" idlist ":" argument ";"
                   | CRZ "("explist")" argument "," argument ";"
                   | CRZ "("explist")" idlist ":" argument ";"
                   | CH argument "," arugment ";"
                   | CH idlist ":" argument ";"
                   | id idlist ";" | id "("")" idlist ";"
                   | id "("explist")" idlist ";"
    idlist      := id | id "["nninteger"]" "," idlist
    argument_c  := id | id "["nninteger"]"
    argument    := id | id "["nninteger"]"
    explist     := exp | explist "," exp
    exp         := ( "+" | "-" )? primary
    primary     := real | nninteger | pi | id | unaryop"("exp")" | "("binaryop")" | binaryop
    binaryop    := exp "+" exp | exp "-" exp | exp "*" exp 
                   | exp "/" exp | exp "^" exp
    unaryop     := sin | cos | tan | exp | ln | sqrt
    
    id          := [a-z][A-Za-z0-9_]*
    real        := ([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?
    nninteger   := [1-9]+[0-9]*|0
                   
    '''
    #===========================================================================
    # Define the AST and the recursive descent parsing
    #===========================================================================
    
    # Recursive descent parsing of program
    def program(self):
        while self.current_file.token[self.current_file.token_idx][self.kind_idx] != token.TK_EOF:
            self.code.append(self.statement())

    # Recursive descent parsing of statement
    def statement(self):
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_QREG or self.check_TK_kind(self.current_file.token_idx) == token.TK_CREG:
            return self.decl()
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_GATE:
            return self.gatedecl()
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_OPAQUE:
            # Check whether the opaque is already defined
            if self.current_file.token[self.current_file.token_idx+1][self.str_idx] in self.opaques:
                self.error_at(self.current_file.token_idx+1, "opaque "+self.current_file.token[self.current_file.token_idx+1][self.str_idx]+" already defined")
            # Check whether the opaque defined is supported by QSoF
            if self.current_file.token[self.current_file.token_idx+1][self.str_idx] not in quantumcircuit.Opaque_Table:
                self.error_at(self.current_file.token_idx+1, "opaque "+self.current_file.token[self.current_file.token_idx+1][self.str_idx]+" is not supported by QSoF")
            if self.check_operator_str(self.current_file.token_idx+2, "("):
                # Recursive descent parsing for 'opaque id (idlist) idlist ;'
                if self.check_TK_kind(self.current_file.token_idx+3) == token.TK_IDENT:
                    name = self.current_file.token[self.current_file.token_idx+1][self.str_idx]
                    self.get_next_token(3)
                    opaque_instance = Opaque(name)
                    params = self.idlist_param()
                    opaque_instance.add_params(params)
                    # Check whether the number of parameters is incorrect 
                    if len(params) != quantumcircuit.Opaque_Table[name]:
                        # Check whether the number of parameters is larger than the maximum number of parameters
                        if len(params) > quantumcircuit.Opaque_Table[name]:
                            self.error_at(self.current_file.token_idx-1, "The number of parameters exceeds the maximum number of parameters of opaque "+name)
                        else:
                            self.error_at(self.current_file.token_idx-1, "The number of parameters is less than the number of parameters required for opaque "+name)
                    self.expect(")")
                    args = self.idlist_qubit().qregs
                    opaque_instance.add_args(args)
                    self.expect(";")
                    self.opaques[name] = opaque_instance
                    node_stmt = Parser.create_node(ND_OPAQUE)
                    node_stmt.add_str(name)
                    self.MULTI_CONTROL_QUBITS.clear()
                    return node_stmt
                # Recursive descent parsing for 'opaque id () idlist ;'
                elif self.check_operator_str(self.current_file.token_idx+3, ")"):
                    self.get_next_token()
                    name = self.current_file.token[self.current_file.token_idx][self.str_idx]
                    # Check whether the opaque should have parameters
                    if quantumcircuit.Opaque_Table[name] != 0:
                        self.error_at(self.current_file.token_idx+2, "The number of parameters should be "+str(quantumcircuit.Opaque_Table[name]))
                    self.get_next_token(3)
                    opaque_instance = Opaque(name)
                    args = self.idlist_qubit().qregs
                    opaque_instance.add_args(args)
                    self.expect(";")
                    self.opaques[name] = opaque_instance
                    node_stmt = Parser.create_node(ND_OPAQUE)
                    node_stmt.add_str(name)
                    self.MULTI_CONTROL_QUBITS.clear()
                    return node_stmt
                else:
                    self.error_at(self.current_file.token_idx+3, "The parameters could only be identifiers or empty")
            # Recursive descent parsing for 'opaque id idlist ;'
            elif self.check_TK_kind(self.current_file.token_idx+2) == token.TK_IDENT:
                self.get_next_token()
                name = self.current_file.token[self.current_file.token_idx][self.str_idx]
                # Check whether the opaque should have parameters
                if quantumcircuit.Opaque_Table[name] != 0:
                    self.error_at(self.current_file.token_idx, "The number of parameters should be "+str(quantumcircuit.Opaque_Table[name]))
                self.get_next_token(2)
                opaque_instance = Opaque(name)
                args = self.idlist_qubit().qregs
                opaque_instance.add_args(args)
                self.expect(";")
                self.opaques[name] = opaque_instance
                node_stmt = Parser.create_node(ND_OPAQUE)
                node_stmt.add_str(name)
                self.MULTI_CONTROL_QUBITS.clear()
                return node_stmt
            # Check for some errors
            else:
                if self.check_operator_str(self.current_file.token_idx+2, ";"):
                    self.error_at(self.current_file.token_idx+2, "The arguments cannot be empty")
                elif self.check_operator_str(self.current_file.token_idx+2, ","):
                    self.error_at(self.current_file.token_idx+2, "The opaque name cannot be empty")
                else:
                    self.error_at(self.current_file.token_idx+2, "The arguments or parameters cannot be this type")
        # Recursive descent parsing for 'if (condition) qop'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_IF:
            self.get_next_token()
            self.expect("(")
            condition = self.condition()
            self.expect(")")
            if self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The statement of if cannot be empty")
            qop = self.qop()
            node_stmt = Parser.create_node(ND_IF, condition, qop)
            return node_stmt
        # Recursive descent parsing for 'barrier idlist ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_BARRIER:
            self.get_next_token()
            args = self.idlist_qubit()
            self.expect(";")
            self.MULTI_CONTROL_QUBITS.clear()
            return Parser.create_node(ND_BARRIER, args)
        # Recursive descent parsing for 'qop'
        else:
            return self.qop()
    
    # Recursive descent parsing for 'condition := id == nninteger'
    def condition(self):
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.current_file.token_idx, ")"):
                self.error_at(self.current_file.token_idx, "The condition cannot be empty")
            else:
                self.error_at(self.current_file.token_idx, "The condition cannot be this type")
        condition_lhs = self.argument_c()
        # Check whether the size of the creg is 1 if it's not indexed
        if condition_lhs.cregs[0][1] == -1:
            if self.cregs[condition_lhs.cregs[0][0]] != 1:
                self.error_at(self.current_file.token_idx, "The condition should be a single bit")
        self.expect("==")
        condition_rhs = self.create_node_num(self.current_file.token[self.current_file.token_idx][self.val_idx])
        self.get_next_token()
        node_condition = Parser.create_node(ND_EQUAL, condition_lhs, condition_rhs)
        return node_condition
    
    # Recursive descent parsing for 'decl := qreg id [nninteger] ; | creg id [nninteger] ;'
    def decl(self):
        # Recursive descent parsing for 'qreg id [nninteger] ;'
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_QREG:
            self.get_next_token()
            # Check whether the qreg name is missing or wrong type is used
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.current_file.token_idx, "["):
                    self.error_at(self.current_file.token_idx, "The qreg name is missing")
                else:
                    self.error_at(self.current_file.token_idx, "The qreg name cannot be this type")
            # Check whether the qreg name is already defined
            if self.current_file.token[self.current_file.token_idx][self.str_idx] in self.qregs:
                self.error_at(self.current_file.token_idx, "qreg "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" already defined")
            name = self.current_file.token[self.current_file.token_idx][self.str_idx]
            self.get_next_token()
            self.expect("[")
            self.check_num_error("qreg size")
            size = int(self.current_file.token[self.current_file.token_idx][self.val_idx])
            self.qregs[name] = size
            self.get_next_token()
            self.expect("]")
            self.expect(";")
            node_decl = Parser.create_node(ND_QREG_DEC)
            node_decl.add_str(name)
            return node_decl
        # Recursive descent parsing for 'creg id [nninteger] ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CREG:
            self.get_next_token()
            # Check whether the creg name is missing or wrong type is used
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.current_file.token_idx, "["):
                    self.error_at(self.current_file.token_idx, "The creg name is missing")
                else:
                    self.error_at(self.current_file.token_idx, "The creg name cannot be this type")
            # Check whether the creg name is already defined
            if self.current_file.token[self.current_file.token_idx][self.str_idx] in self.cregs:
                self.error_at(self.current_file.token_idx, "creg "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" already defined")
            name = self.current_file.token[self.current_file.token_idx][self.str_idx]
            self.get_next_token()
            self.expect("[")
            self.check_num_error("creg size")
            size = int(self.current_file.token[self.current_file.token_idx][self.val_idx])
            self.cregs[name] = size
            self.get_next_token()
            self.expect("]")
            self.expect(";")
            node_decl = Parser.create_node(ND_CREG_DEC)
            node_decl.add_str(name)
            return node_decl
        # Check for some errors
        else:
            if self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The declaration cannot be empty")
            elif self.check_operator_str(self.current_file.token_idx, "["):
                self.error_at(self.current_file.token_idx, "The qreg name cannot be empty")
            else:
                self.error_at(self.current_file.token_idx, "The declaration cannot be this type")
    
    # Recursive descent parsing for 'gatedecl := gate id idlist {goplist}|gate id () idlist {goplist}|gate id (idlist) idlist {goplist}'
    def gatedecl(self):
        # Check whether the gate keyword is missing
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_GATE:
            self.error_at(self.current_file.token_idx, "The gate keyword is missing")
        self.get_next_token()
        # Check whether the gate name is missing or wrong type is used 
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.current_file.token_idx, "("):
                self.error_at(self.current_file.token_idx, "The gate name is missing")
            elif self.check_operator_str(self.current_file.token_idx, "{") or self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The gate name and the arguments are missing")
            else:
                self.error_at(self.current_file.token_idx, "The gate name cannot be this type")
                return
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_IDENT and self.check_operator_str(self.current_file.token_idx+1, ","):
            self.error_at(self.current_file.token_idx, "The gate name is missing")
        # Check whether the gate is already defined 
        if self.current_file.token[self.current_file.token_idx][self.str_idx] in self.gates:
            self.error_at(self.current_file.token_idx, "gate "+self.current_file.token[self.current_file.token_idx][self.str_idx]+\
                f" already defined in {self.gates[self.current_file.token[self.current_file.token_idx][self.str_idx]].filename}")
        name = self.current_file.token[self.current_file.token_idx][self.str_idx] 
        # Set the current gate name
        GATE_DEF_name_pre = self.GATE_DEF_name
        GATE_define_pre = self.GATE_define
        self.GATE_define = False
        self.GATE_DEF_name = name
        self.get_next_token()
        params = []
        if self.check_operator_str(self.current_file.token_idx, "("):
            self.get_next_token()
            # Check for some errors 
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT and not self.check_operator_str(self.current_file.token_idx, ")"):
                self.error_at(self.current_file.token_idx, "The parameters should be identifiers")
            # Check for nonempty parameters
            if self.check_TK_kind(self.current_file.token_idx) == token.TK_IDENT:
                params.extend(self.idlist_param())
            self.expect(")")
        # Check whether the arguments are missing or wrong type is used
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.current_file.token_idx, "{"):
                self.error_at(self.current_file.token_idx, "The arguments are missing")
            elif self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The arguments and the contents are missing")
            else:
                self.error_at(self.current_file.token_idx, "The arguments cannot be this type")
        args = self.idlist_qubit().qregs
        gate_val = Gate(name)
        gate_val.add_params(params)
        gate_val.add_args(args)
        gate_val.add_filename(self.current_file.name)
        self.gates[name] = gate_val # Add the node to the dictionary here because the error check inside the contents need to use the parameters and arguments
        # Set the gate_define flag to true to indicate that the current state is a gate definition
        self.GATE_define = True
        self.expect("{")
        while not self.check_operator_str(self.current_file.token_idx, "}"):
            self.gates[name].add_contents(self.uop())
        self.expect("}")
        # recover the gate_define flag and gate_def name to come back to the previous state
        self.GATE_define = GATE_define_pre
        self.GATE_DEF_name = GATE_DEF_name_pre
        node_gatedecl = Parser.create_node(ND_GATE_DEC)
        node_gatedecl.add_str(name)
        # Check whether the gate defined is the gate we want to find if the gate is not found for the parent file
        if (not self.GATE_FOUND) and (self.gate_name_find == name):
            self.GATE_FOUND = True
        self.MULTI_CONTROL_QUBITS.clear()
        return node_gatedecl
                
    # Recursive descent parsing for 'qop := uop | measure argument -> argument ; | reset argument ;'
    def qop(self):
        # Recursive descent parsing for 'measure argument -> argument ;'
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_MEASURE:
            self.get_next_token()
            # Check whether the argument is missing or wrong type is used 
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.current_file.token_idx, "->"):
                    self.error_at(self.current_file.token_idx, "The qreg argument is missing")
                elif self.check_operator_str(self.current_file.token_idx, ";"):
                    self.error_at(self.current_file.token_idx, "The qreg argument and the destination are missing")
                else:
                    self.error_at(self.current_file.token_idx, "The qreg argument cannot be this type")
            self.MEASURE = True
            node_lhs = self.argument()
            self.expect("->")
            # Check whether the destination is missing or wrong type is used
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.current_file.token_idx, ";"):
                    self.error_at(self.current_file.token_idx, "The creg destination is missing")
                else:
                    self.error_at(self.current_file.token_idx, "The creg destination cannot be this type")
            node_rhs = self.argument_c()
            # Check whether the qreg and creg are of the same size if they are not indexed
            if node_lhs.qregs[0][1] == -1 and node_rhs.cregs[0][1] == -1:
                if self.qregs[node_lhs.qregs[0][0]] != self.cregs[node_rhs.cregs[0][0]]:
                    self.error_at(self.current_file.token_idx-1, "The qreg and creg should be of the same size for measurement")
            # Check whether the qreg and creg are of the same size if only one of them is indexed
            if node_lhs.qregs[0][1] == -1 and node_rhs.cregs[0][1] != -1:
                if self.qregs[node_lhs.qregs[0][0]] != 1:
                    self.error_at(self.current_file.token_idx-4, "Multiple qubits cannot be measured into a single bit")
            if node_lhs.qregs[0][1] != -1 and node_rhs.cregs[0][1] == -1:
                if self.cregs[node_rhs.cregs[0][0]] != 1:
                    self.error_at(self.current_file.token_idx-1, "Single qubit cannot be measured into multiple bits")
            self.MEASURE = False
            self.expect(";")
            node_qof = Parser.create_node(ND_MEASURE, node_lhs, node_rhs)
            return node_qof
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_RESET:
            self.get_next_token()
            # Check whether the argument is missing or wrong type is used
            if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.current_file.token_idx, ";"):
                    self.error_at(self.current_file.token_idx, "The qreg argument is missing")
                else:
                    self.error_at(self.current_file.token_idx, "The qreg argument cannot be this type")
            self.RESET = True
            node_lhs = self.argument()
            self.expect(";")
            self.RESET = False
            node_qof = Parser.create_node(ND_RESET, node_lhs)
            return node_qof
        else:
            return self.uop()
    
    # Recursive descent parsing for 'argument := id | id [nninteger]'
    def argument(self):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            self.error_at(self.current_file.token_idx, "The qreg argument should be an identifier")
        # Check whether the argument is declared for the gate definition
        if self.GATE_define:
            if not self.current_file.token[self.current_file.token_idx][self.str_idx] in self.gates[self.GATE_DEF_name].args:
                self.error_at(self.current_file.token_idx, "The argument "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" is not declared in gate "+self.GATE_DEF_name)
        # Check whether the argument is already defined 
        if (not self.GATE_define) and (not self.current_file.token[self.current_file.token_idx][self.str_idx] in self.qregs):
            self.error_at(self.current_file.token_idx, "qreg "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" not defined")
        name = self.current_file.token[self.current_file.token_idx][self.str_idx]
        self.get_next_token()
        # Check whether the argument is indexed
        if self.check_operator_str(self.current_file.token_idx, "["):
            # Error happens if the argument is indexed in the gate definition
            if self.GATE_define:
                self.error_at(self.current_file.token_idx, "The argument of gate definition cannot be indexed")
            # Check whether the qreg size is missing or wrong type is used
            self.get_next_token()
            self.check_num_error("qreg index")
            index = int(self.current_file.token[self.current_file.token_idx][self.val_idx])
            # Check whether the qreg index exceeds the size
            if index >= self.qregs[name]:
                self.error_at(self.current_file.token_idx, "The qreg index exceeds the size")
            node_argument = Parser.create_node_qreg((name, index))
            self.get_next_token()
            self.expect("]")
            return node_argument
        else:
            # Check if the qreg is not indexed then it should be a qubit instead of a register
            if (not self.GATE_define) and (self.qregs[name] != 1) and (not self.MEASURE) and (not self.RESET):
                self.error_at(self.current_file.token_idx, "The qreg "+name+" should be indexed")
            node_argument = Parser.create_node_qreg((name, -1))
            return node_argument
    
    # Recursive descent parsing for 'argument_c := id | id [nninteger]'
    def argument_c(self):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            self.error_at(self.current_file.token_idx, "The creg argument should be an identifier")
        # Check whether the argument is already defined 
        if not self.current_file.token[self.current_file.token_idx][self.str_idx] in self.cregs:
            self.error_at(self.current_file.token_idx, "creg "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" not defined")
        name = self.current_file.token[self.current_file.token_idx][self.str_idx]
        self.get_next_token()
        # Check whether the argument is indexed
        if self.check_operator_str(self.current_file.token_idx, "["):
            # Check whether the creg size is missing or wrong type is used
            self.get_next_token()
            self.check_num_error("creg index")
            index = int(self.current_file.token[self.current_file.token_idx][self.val_idx])
            # Check whether the creg index exceeds the size
            if index >= self.cregs[name]:
                self.error_at(self.current_file.token_idx, "The creg index exceeds the size")
            node_argument = Parser.create_node_creg((name, index))
            self.get_next_token()
            self.expect("]")
            return node_argument
        else:
            # Check if the creg is not indexed then it should be a bit instead of a register
            if (self.cregs[name] != 1) and (not self.MEASURE):
                self.error_at(self.current_file.token_idx, "The creg "+name+" should be indexed")
            node_argument = Parser.create_node_creg((name, -1))
            return node_argument
    
    '''Recursive descent parsing for 
        uop     := U (explist) argument ;
                   | CX argument , argument ;
                   | X argument ;
                   | Y argument ;
                   | Z argument ;
                   | S argument ;
                   | T argument ;
                   | RTHETA (explist) argument ;
                   | RX (explist) argument
                   | RY (explist) argument
                   | RZ (explist) argument
                   | H argument ;
                   | CY argument, argument ;
                   | CZ argument, argument ;
                   | CU (explist) argument, argument ;
                   | CS argument, argument ;
                   | CT argument, argument ;
                   | CRTHETA (explist) argument, argument ;
                   | CRX (explist) argument, argument ;
                   | CRY (explist) argument, argument ;
                   | CRZ (explist) argument, argument ;
                   | CH argument, arugment ;
                   | id idlist ; | id () idlist ;
                   | id (explist) idlist ;'''
    
    def uop_with_explist_single(self, kind, name):
        self.get_next_token()
        # Set the current gate name
        self.GATE_name_support = name
        self.expect("(")
        # Check whether the explist is missing
        if self.check_operator_str(self.current_file.token_idx, ")"):
            self.error_at(self.current_file.token_idx, "The explist of "+name+" is missing")
        explist = self.explist()
        self.expect(")")
        # Check whether the argument is missing
        if self.check_operator_str(self.current_file.token_idx, ";"):
            self.error_at(self.current_file.token_idx, "The argument of "+name+" is missing")
        argument = self.argument()
        self.expect(";")
        node_uop = Parser.create_node(kind, explist, argument)
        return node_uop
    
    def uop_without_explist_single(self, kind, name):
        self.get_next_token()
        # Check whether the argument is missing
        if self.check_operator_str(self.current_file.token_idx, ";"):
            self.error_at(self.current_file.token_idx, "The argument of"+name+"is missing")
        argument = self.argument()
        self.expect(";")
        node_uop = Parser.create_node(kind, argument)
        return node_uop
    
    def uop_without_explist_controlled(self, kind, name):
        self.get_next_token()
        # Check whether the first argument is missing
        if self.check_operator_str(self.current_file.token_idx, ","):
            self.error_at(self.current_file.token_idx, "The first argument of "+name+" is missing")
        # argument_lhs = self.argument()
        # self.expect(",")
        argument_rhs = None
        argument_lhs = self.idlist_qubit()
        if len(argument_lhs.qregs) == 2 and self.check_operator_str(self.current_file.token_idx, ";"):
            argument_rhs = Parser.create_node_qreg(argument_lhs.qregs[1])
            argument_lhs.qregs.pop()
            target_idx = self.current_file.token_idx
            # Check whether the first argument is equal to the second argument
            if argument_lhs.qregs[0][0] == argument_rhs.qregs[0][0] and argument_lhs.qregs[0][1] == argument_rhs.qregs[0][1]:
                self.error_at(target_idx, "The control qubit and the target qubit of "+name+" cannot be the same")
        else:
            self.expect(":")
            # Check whether the second argument is missing
            if self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The second argument of "+name+" is missing")
            arg_idx = self.current_file.token_idx  
            argument_rhs = self.argument()
            targetname = argument_rhs.qregs[0][0]+f"[{argument_rhs.qregs[0][1]}]" if argument_rhs.qregs[0][1] != -1 else argument_rhs.qregs[0][0]
            if (targetname in self.MULTI_CONTROL_QUBITS) and (argument_rhs.qregs[0][1] == self.MULTI_CONTROL_QUBITS[targetname]):
                self.error_at(arg_idx, "The control qubit of "+name+" cannot be the target qubit")
        self.expect(";")
        node_uop = Parser.create_node(kind, argument_lhs, argument_rhs)
        self.MULTI_CONTROL_QUBITS.clear()
        return node_uop
    
    def uop_with_explist_controlled(self, kind, name):
        self.get_next_token()
        # Set the current gate name
        self.GATE_name_support = name
        self.expect("(")
        # Check whether the explist is missing
        if self.check_operator_str(self.current_file.token_idx, ")"):
            self.error_at(self.current_file.token_idx, "The explist of "+name+" is missing")
        explist = self.explist()
        self.expect(")")
        # Check whether the first argument is missing
        if self.check_operator_str(self.current_file.token_idx, ","):
            self.error_at(self.current_file.token_idx, "The first argument of "+name+" is missing")
        # argument_control = self.argument()
        # self.expect(",")
        argument_target = None
        argument_control = self.idlist_qubit()
        if len(argument_control.qregs) == 2 and self.check_operator_str(self.current_file.token_idx, ";"):
            argument_target = Parser.create_node_qreg(argument_control.qregs[1])
            argument_control.qregs.pop()
            target_idx = self.current_file.token_idx
            # Check whether the first argument is equal to the second argument
            if argument_control.qregs[0][0] == argument_target.qregs[0][0] and argument_control.qregs[0][1] == argument_target.qregs[0][1]:
                self.error_at(target_idx, "The control qubit and the target qubit of "+name+" cannot be the same")
        else:
            self.expect(":")
            # Check whether the second argument is missing
            if self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The second argument of "+name+" is missing")
            arg_idx = self.current_file.token_idx
            argument_target = self.argument()
            targetname = argument_target.qregs[0][0]+f"[{argument_target.qregs[0][1]}]" if argument_target.qregs[0][1] != -1 else argument_target.qregs[0][0]
            if (targetname in self.MULTI_CONTROL_QUBITS) and (argument_target.qregs[0][1] == self.MULTI_CONTROL_QUBITS[targetname]):
                self.error_at(arg_idx, "The control qubit of "+name+" cannot be the target qubit")
            
        argument_control.controlled_with_parameter = True
        self.expect(";")
        argument_control.add_left(argument_target)
        node_uop = Parser.create_node(kind, explist, argument_control)
        self.MULTI_CONTROL_QUBITS.clear()
        return node_uop
    
    def uop(self):
        # Recursive descent parsing for 'U (explist) argument ;'
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_U:
            node_uop = self.uop_with_explist_single(ND_U, "U")
            return node_uop
        # Recursive descent parsing for u1
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_U1:
            node_uop = self.uop_with_explist_single(ND_U1, "U1")
            return node_uop
        # Recursive descent parsing for u2
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_U2:
            node_uop = self.uop_with_explist_single(ND_U2, "U2")
            return node_uop
        # Recursive descent parsing for 'CX argument , argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CX:
            node_uop = self.uop_without_explist_controlled(ND_CX, "CX")
            return node_uop
        # Recursive descent parsing for 'X argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_X:
            node_uop = self.uop_without_explist_single(ND_X, "X")
            return node_uop
        # Recursive descent parsing for 'Y argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_Y:
            node_uop = self.uop_without_explist_single(ND_Y, "Y")
            return node_uop
        # Recursive descent parsing for 'Z argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_Z:
            node_uop = self.uop_without_explist_single(ND_Z, "Z")
            return node_uop
        # Recursive descent parsing for 'S argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_S:
            node_uop = self.uop_without_explist_single(ND_S, "S") 
            return node_uop
        # Recursive descent parsing for 'T argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_T:
            node_uop = self.uop_without_explist_single(ND_T, "T")
            return node_uop
        # Recursive descent parsing for 'RTHETA (explist) argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_RTHETA:
            node_uop = self.uop_with_explist_single(ND_RTHETA, "RTHETA")
            return node_uop
        # Recursive descent parsing for 'RX (explist) argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_RX:
            node_uop = self.uop_with_explist_single(ND_RX, "RX")
            return node_uop
        # Recursive descent parsing for 'RY (explist) argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_RY:
            node_uop = self.uop_with_explist_single(ND_RY, "RY")
            return node_uop
        # Recursive descent parsing for 'RZ (explist) argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_RZ:
            node_uop = self.uop_with_explist_single(ND_RZ, "RZ")
            return node_uop
        # Recursive descent parsing for 'H argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_H:
            node_uop = self.uop_without_explist_single(ND_H, "H")
            return node_uop
        # Recursive descent parsing for 'CY argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CY:
            node_uop = self.uop_without_explist_controlled(ND_CY, "CY")
            return node_uop
        # Recursive descent parsing for 'CZ argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CZ:
            node_uop = self.uop_without_explist_controlled(ND_CZ, "CZ")
            return node_uop
        # Recursive descent parsing for 'CU (explist) argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CU:
            node_uop = self.uop_with_explist_controlled(ND_CU, "CU")
            return node_uop
        # Recursive descent parsing for 'CS argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CS:
            node_uop = self.uop_without_explist_controlled(ND_CS, "CS")
            return node_uop
        # Recursive descent parsing for 'CT argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CT:
            node_uop = self.uop_without_explist_controlled(ND_CT, "CT")
            return node_uop
        # Recursive descent parsing for 'CRTHETA (explist) argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CRTHETA:
            node_uop = self.uop_with_explist_controlled(ND_CRTHETA, "CRTHETA")
            return node_uop
        # Recursive descent parsing for 'CRX (explist) argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CRX:
            node_uop = self.uop_with_explist_controlled(ND_CRX, "CRX")
            return node_uop
        # Recursive descent parsing for 'CRY (explist) argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CRY:
            node_uop = self.uop_with_explist_controlled(ND_CRY, "CRY")
            return node_uop
        # Recursive descent parsing for 'CRZ (explist) argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CRZ:
            node_uop = self.uop_with_explist_controlled(ND_CRZ, "CRZ")
            return node_uop
        # Recursive descent parsing for 'CH argument, argument ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CH:
            node_uop = self.uop_without_explist_controlled(ND_CH, "CH")
            return node_uop
        # Recursive descent parsing for idle gate
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_ID:
            node_uop = self.uop_without_explist_single(-1, "ID")
            return
        # Recursive descent parsing for sdg gate
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_SDG:
            node_uop = self.uop_without_explist_single(ND_SDG, "SDG")
            return node_uop
        # Recursive descent parsing for tdg gate
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_TDG:
            node_uop = self.uop_without_explist_single(ND_TDG, "TDG")
            return node_uop
        # Recursive descent parsing for ccx gate
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_CCX:
            self.get_next_token()
            # Check whether there are parameters
            if self.check_operator_str(self.current_file.token_idx, "("):
                self.error_at(self.current_file.token_idx, "The parameters of CCX are not allowed")
            argument = self.idlist_qubit()
            # Check whether the number of arguments is correct
            if len(argument.qregs) != 3:
                if len(argument.qregs) > 3:
                    self.error_at(self.current_file.token_idx, "There should not be more than 2 control qubits for CCX")
                else:
                    self.error_at(self.current_file.token_idx, "There should not be less than 2 control qubits for CCX")
            self.expect(";")
            node_uop = Parser.create_node(ND_CCX, argument)
            return node_uop
        # Recursive descent parsing for 'id idlist ; | id () idlist ; | id (explist) idlist ;'
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_IDENT:
            name = self.current_file.token[self.current_file.token_idx][self.str_idx]
            # Check whether the gate is a gate declare or an opaque declare
            Gate_declare_pre = self.GATE_declare
            Opaque_declare_pre = self.OPAQUE_declare
            ND_NOEXP_type = ND_GATE_NOEXP
            ND_EXP_type = ND_GATE_EXP
            if name in self.gates:
                self.GATE_declare = True
            elif name in self.opaques:
                self.OPAQUE_declare = True
                ND_NOEXP_type = ND_OPAQUE_NOEXP
                ND_EXP_type = ND_OPAQUE_EXP
            else:
                gate_found_pre = self.GATE_FOUND
                gate_name_find_pre = self.gate_name_find
                self.GATE_FOUND = False
                self.gate_name_find = name
                file_need_find_pre = self.file_need_find
                self.file_need_find = self.current_file
                if not self.check_included_files(self.current_file):
                    self.current_file = self.file_need_find
                    self.error_at(self.current_file.token_idx, f"gate {name} not defined")
                self.current_file = self.file_need_find
                self.file_need_find = file_need_find_pre
                self.GATE_declare = True
                self.GATE_FOUND = gate_found_pre
                self.gate_name_find = gate_name_find_pre
            
            gate_name_pre = self.GATE_name 
            self.GATE_name = name
            self.get_next_token()
            if self.check_operator_str(self.current_file.token_idx, "("):
                self.get_next_token()
                if self.check_operator_str(self.current_file.token_idx, ")"):
                    self.expect(")")
                    # Check whether the arguments are missing or wrong type is used
                    if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                        if self.check_operator_str(self.current_file.token_idx, ";"):
                            self.error_at(self.current_file.token_idx, "The arguments of the gate are missing")
                        else:
                            self.error_at(self.current_file.token_idx, "The arguments cannot be this type")
                    args = self.idlist_qubit()
                    self.expect(";")
                    node_uop = Parser.create_node(ND_NOEXP_type, args)
                    # Add the gate name to the node for later circuit generation
                    node_uop.add_str(name)
                    # Flip the GATE_declare flag to change the current state back to normal
                    # self.GATE_declare = False
                    # self.OPAQUE_declare = False
                    self.GATE_declare = Gate_declare_pre
                    self.OPAQUE_declare = Opaque_declare_pre
                    self.GATE_name = gate_name_pre
                    self.MULTI_CONTROL_QUBITS.clear()
                    return node_uop
                else:
                    explist = self.explist()
                    self.expect(")")
                     # Check whether the arguments are missing or wrong type is used
                    if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
                        if self.check_operator_str(self.current_file.token_idx, ";"):
                            self.error_at(self.current_file.token_idx, "The arguments of the gate are missing")
                        else:
                            self.error_at(self.current_file.token_idx, "The arguments cannot be this type")
                    args = self.idlist_qubit()
                    self.expect(";")
                    node_uop = Parser.create_node(ND_EXP_type, explist, args)
                    # Add the gate name to the node for later circuit generation
                    node_uop.add_str(name)
                    # Flip the GATE_declare flag to change the current state back to normal
                    # self.GATE_declare = False
                    # self.OPAQUE_declare = False
                    self.GATE_declare = Gate_declare_pre
                    self.OPAQUE_declare = Opaque_declare_pre
                    self.GATE_name = gate_name_pre
                    self.MULTI_CONTROL_QUBITS.clear()
                    return node_uop
            elif self.check_TK_kind(self.current_file.token_idx) == token.TK_IDENT:
                args = self.idlist_qubit()
                self.expect(";")
                node_uop = Parser.create_node(ND_NOEXP_type, args)
                node_uop.add_str(name)
                # Flip the GATE_declare flag to change the current state back to normal
                # self.GATE_declare = False
                # self.OPAQUE_declare = False
                self.GATE_declare = Gate_declare_pre
                self.OPAQUE_declare = Opaque_declare_pre
                self.GATE_name = gate_name_pre
                self.MULTI_CONTROL_QUBITS.clear()
                return node_uop
            # Check for some errors
            else:
                if self.check_operator_str(self.current_file.token_idx, ","):
                    self.error_at(self.current_file.token_idx, "The gate name cannot be empty")
                else:
                    self.error_at(self.current_file.token_idx, "The arguments cannot be this type")
        # Check for some errors
        else:
            if self.check_operator_str(self.current_file.token_idx, ";"):
                self.error_at(self.current_file.token_idx, "The gate operation cannot be empty")
            else:
                self.error_at(self.current_file.token_idx, "The gate operation cannot be this type")
    
    # Recursive descent parsing for 'idlist := id | id [nninteger], idlist'
    def id_check_qubit(self, qreglist):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            self.error_at(self.current_file.token_idx, "The type should be identifier")
        # Check whether the argument is already declared for the gate definition
        if self.GATE_define:
            if not self.current_file.token[self.current_file.token_idx][self.str_idx] in self.gates[self.GATE_DEF_name].args:
                self.error_at(self.current_file.token_idx, "The argument "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" is not declared in gate "+self.GATE_DEF_name)
        # Check whether the qreg is already defined
        if (not self.GATE_define) and (self.GATE_declare or self.OPAQUE_declare) and (not self.current_file.token[self.current_file.token_idx][self.str_idx] in self.qregs):
            self.error_at(self.current_file.token_idx, "qreg "+self.current_file.token[self.current_file.token_idx][self.str_idx]+" not defined")
        name = self.current_file.token[self.current_file.token_idx][self.str_idx]
        self.get_next_token()
        # Check whether the argument is indexed
        if self.check_operator_str(self.current_file.token_idx, "["):
            # Error happens if the argument is indexed in the gate definition
            if self.GATE_define:
                self.error_at(self.current_file.token_idx, "The argument of gate definition cannot be indexed")
            self.get_next_token()
            self.check_num_error("qreg index")
            idx = int(self.current_file.token[self.current_file.token_idx][self.val_idx])
            # Check whether the qreg index exceeds the size
            if idx >= self.qregs[name]:
                self.error_at(self.current_file.token_idx, "The qreg index exceeds the size")
            self.get_next_token()
            self.expect("]")
            qreglist.append((name, idx))
            self.MULTI_CONTROL_QUBITS[name+f"[{idx}]"] = idx
        else:
            qreglist.append((name, -1))
            self.MULTI_CONTROL_QUBITS[name] = -1
        
    def idlist_qubit(self):
        qreglist = []
        self.id_check_qubit(qreglist)
        while self.check_operator_str(self.current_file.token_idx, ","):
            self.expect(",")
            # Check for whether the number of arguments exceeds the gate defined
            if self.GATE_declare:
                if len(qreglist) == len(self.gates[self.GATE_name].args):
                    self.error_at(self.current_file.token_idx, f"The number of arguments exceeds the gate {self.GATE_name} defined")
            if self.OPAQUE_declare:
                if len(qreglist) == len(self.opaques[self.GATE_name].args):
                    self.error_at(self.current_file.token_idx, f"The number of arguments exceeds the opaque gate {self.GATE_name} defined")
            self.id_check_qubit(qreglist)
        # Check for whether the number of arguments is less than the gate defined
        if self.GATE_declare:
            if len(qreglist) < len(self.gates[self.GATE_name].args):
                self.error_at(self.current_file.token_idx, f"The number of arguments is less than the gate {self.GATE_name} defined")
        if self.OPAQUE_declare:
            if len(qreglist) < len(self.opaques[self.GATE_name].args):
                self.error_at(self.current_file.token_idx, f"The number of arguments is less than the opaque gate {self.GATE_name} defined")
        node_idlist = Parser.create_node_qreg(qreglist)
        return node_idlist

    def id_check(self, paramlist):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_IDENT:
            self.error_at(self.current_file.token_idx, "The type should be identifier")
        paramlist.append(self.current_file.token[self.current_file.token_idx][self.str_idx])
        self.get_next_token()
    
    def idlist_param(self):
        paramlist = []
        self.id_check(paramlist)
        while self.check_operator_str(self.current_file.token_idx, ","):
            self.expect(",")
            self.id_check(paramlist)
        return paramlist
    
    '''
    explist     := exp | explist "," exp
    exp         := binaryop
    exp_prim    := ( "+" | "-" )? primary
    primary     := real | nninteger | pi | id | unaryop"("exp")" | "("binaryop")"
    binaryop    := exp_prim "+" exp_prim | exp_prim "-" exp_prim | exp_prim "*" exp_prim 
                   | exp_prim "/" exp_prim | exp_prim "^" exp_prim
    unaryop     := sin | cos | tan | exp | ln | sqrt'''
    
    # For binary operations, operator precedence parsing is applied
    # Recursive descent parsing for exp = ( "+" | "-" )? primary
    def exp(self):
        return self.binaryop()
        
    def exp_prim(self):
        if self.consume_operator_str("+"):
            return self.primary()
        if self.consume_operator_str("-"):
            node_exp = Parser.create_node(ND_SUB, self.create_node_num(0), self.primary())
            return node_exp
        return self.primary()
    
    # Check for unary operators 
    def consume_unaryop(self):
        TK_kind = self.check_TK_kind(self.current_file.token_idx)
        if TK_kind == token.TK_SIN:
            self.get_next_token()
            return ND_SIN
        elif TK_kind == token.TK_COS:
            self.get_next_token()
            return ND_COS
        elif TK_kind == token.TK_TAN:
            self.get_next_token()
            return ND_TAN
        elif TK_kind == token.TK_EXP:
            self.get_next_token()
            return ND_EXP
        elif TK_kind == token.TK_LN:
            self.get_next_token()
            return ND_LN
        elif TK_kind == token.TK_SQRT:
            self.get_next_token()
            return ND_SQRT
        else:
            self.error_at(self.current_file.token_idx, "This unary operator is not supported")
    
    # Recursive descent parsing for primary = real | nninteger | pi | id | unaryop"("exp")" | "("binaryop")"
    def primary(self):
        # Recursive descent parsing for real and nninteger
        if self.check_TK_kind(self.current_file.token_idx) == token.TK_NUM:
            val = self.current_file.token[self.current_file.token_idx][self.val_idx]*(10**self.current_file.token[self.current_file.token_idx][self.exp_idx])
            node_primary = Parser.create_node_num(val)
            self.current_file.token_idx += 1
            return node_primary
        # Recursive descent parsing for pi
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_PI:
            node_primary = Parser.create_node(ND_PI)
            self.get_next_token()
            return node_primary
        # Recursive descent parsing for id
        elif self.check_TK_kind(self.current_file.token_idx) == token.TK_IDENT:
            # Note! Here should be a check for whether the parameter is declared for this gate, this check will be in the code generation part
            node_primary = Parser.create_node(ND_IDENT)
            node_primary.add_str(self.current_file.token[self.current_file.token_idx][self.str_idx])
            # Check if the identifier of the parameter is already defined for gate definition
            if self.GATE_define:
                if self.current_file.token[self.current_file.token_idx][self.str_idx] not in self.gates[self.GATE_DEF_name].params:
                    self.error_at(self.current_file.token_idx, f"The parameter {self.current_file.token[self.current_file.token_idx][self.str_idx]} is not defined for gate {self.GATE_DEF_name}")
            self.get_next_token()
            return node_primary
        # Recursive descent parsing for "("binaryop")"
        elif self.check_operator_str(self.current_file.token_idx, "("):
            self.consume_operator_str("(")
            node_primary = self.binaryop()
            self.expect(")")
            return node_primary
        # Recursive descent parsing for unaryop"("exp")"
        else:
            UnaryOp = self.consume_unaryop()
            self.expect("(")
            node_primary = Parser.create_node(UnaryOp, self.exp())
            self.expect(")")
            return node_primary
    
    # Operator precedence parsing for binaryop = exp "+" exp | exp "-" exp | exp "*" exp | exp "/" exp | exp "^" exp
    
    # In this case, the precedences will be initialized as a dictionary
    # Define the function to get the precedence of the current binary operator
    def get_binaryop_precedence(self):
        # Check whether the current token is an operator
        if self.check_TK_kind(self.current_file.token_idx) != token.TK_OPERATOR:
            self.error_at(self.current_file.token_idx, "This is not an operator")
        # Check whether the current operator is supported
        if not self.current_file.token[self.current_file.token_idx][self.str_idx] in binop_precedence:
            self.error_at(self.current_file.token_idx, "This operator is not supported")
        precedence = binop_precedence[self.current_file.token[self.current_file.token_idx][self.str_idx]]
        return precedence
    
    # Define the function to get the node kind of the current binary operator
    def get_binaryop(self):
        # Since this function will only be used after the precedence check, the current token must be an operator supported, so no need to check error
        if self.current_file.token[self.current_file.token_idx][self.str_idx] == "+":
            self.current_file.token_idx += 1
            return ND_ADD
        elif self.current_file.token[self.current_file.token_idx][self.str_idx] == "-":
            self.get_next_token()
            return ND_SUB
        elif self.current_file.token[self.current_file.token_idx][self.str_idx] == "*":
            self.get_next_token()
            return ND_MUL
        elif self.current_file.token[self.current_file.token_idx][self.str_idx] == "/":
            self.get_next_token()
            return ND_DIV
        else:
            self.get_next_token()
            return ND_POW
    
    # Define the function needed for recursively parsing the binaryop
    def ParseBinaryopRHS(self, expr_prec, lhs):
        # If this is a binary operator, find its precedence
        while True:
            # Get the precedence of the operator
            prec = self.get_binaryop_precedence()
            # If this is a binary operator that binds at least as tightly as the current binary operator, consume it, otherwise we are done
            if prec < expr_prec:
                return lhs
            # Now this is a binary operator
            binaryop = self.get_binaryop()
            # Parse the expression after the binary operator
            rhs = self.exp_prim()
            if rhs is None:
                self.error_at(self.current_file.token_idx, "The expression after the binary operator cannot be empty")
            # If this is a binary operator that binds less tightly with RHS than the operator after RHS, let the pending operator take RHS as its LHS
            next_prec = self.get_binaryop_precedence()
            if prec < next_prec:
                rhs = self.ParseBinaryopRHS(prec+1, rhs)
            # Merge lhs/RHS
            lhs = Parser.create_node(binaryop, lhs, rhs)
    
    # Recursive descent parsing for binaryop
    def binaryop(self):
        # First parse the left hand side
        lhs = self.exp_prim()
        if lhs is None:
            self.error_at(self.current_file.token_idx, "The expression before the binary operator cannot be empty")
        # Then parse the right hand side, the precedence of the first binary operator is 0
        return self.ParseBinaryopRHS(0, lhs)
    
    # Recursive descent parsing for explist = exp | explist "," exp
    def explist(self):
        exp_list = []
        exp_list.append(self.exp())
        while self.check_operator_str(self.current_file.token_idx, ","):
            self.expect(",")
            # Check whether the number of parameters exceeds the number of parameters required for the gate
            if self.GATE_declare:
                if len(exp_list) == len(self.gates[self.GATE_name].params):
                    self.error_at(self.current_file.token_idx, f"The number of parameters exceeds the number of parameters required for gate {self.GATE_name}")
            elif self.OPAQUE_declare:
                if len(exp_list) == len(self.opaques[self.GATE_name].params):
                    
                    self.error_at(self.current_file.token_idx, f"The number of parameters exceeds the number of parameters required for opaque {self.GATE_name}")
            else:
                if len(exp_list) == quantumcircuit.Param_Num_Table[self.GATE_name_support]:
                    self.error_at(self.current_file.token_idx, f"The number of parameters exceeds the number of parameters required for gate {self.GATE_name}")
                
            exp_list.append(self.exp())
        # Check whether the number of parameters is less than the number of parameters required for the gate
        if self.GATE_declare:
            if len(exp_list) < len(self.gates[self.GATE_name].params):
                self.error_at(self.current_file.token_idx, f"The number of parameters is less than the number of parameters required for gate {self.GATE_name}")
        elif self.OPAQUE_declare:
             if len(exp_list) < len(self.opaques[self.GATE_name].params):
                self.error_at(self.current_file.token_idx, f"The number of parameters is less than the number of parameters required for opaque {self.GATE_name}")
        else:
            if len(exp_list) < quantumcircuit.Param_Num_Table[self.GATE_name_support]:
                self.error_at(self.current_file.token_idx, f"The number of parameters is less than the number of parameters required for gate {self.GATE_name}")
        node_explist = Parser.create_node_explist(exp_list)
        return node_explist
    
    # Define the Recursive descent parsing function
    def Recursive_Descent_Parsing(self):
        self.program()
    
    #================================================================================================
    # End of Recursive descent parsing
    #================================================================================================
    
    #================================================================================================
    # Circuit generation
    #================================================================================================
    
    # Define the recursive function to generate the code for the node
    def code_gen(self, node, quantumcircuit):
        if node is None:
            return
        # return the val of the node if it is a number
        if node.kind == ND_NUM:
            return node.val
        # return the corresponding parameter value if it is an identifier
        elif node.kind == ND_IDENT:
            parameter_name = node.str
            parameter_val = self.gates[self.GATE_DEF_name].params[parameter_name]
            return parameter_val
        # return the pi if it is a pi node
        elif node.kind == ND_PI:
            return math.pi
        # qubits added to circuit if ND_QREG_DEC is encountered
        elif node.kind == ND_QREG_DEC:
            qubit_name = node.str
            size = self.qregs[qubit_name]
            quantumcircuit.add_qubit(qubit_name, size)
            quantumcircuit.add_qubit_max_time_slice(qubit_name, 0, size)
            return
        # classical bits added to circuit if ND_CREG_DEC is encountered
        elif node.kind == ND_CREG_DEC:
            cbit_name = node.str
            size = self.cregs[cbit_name]
            quantumcircuit.add_creg(cbit_name, size)
            return
        # the control and target qubits will be returned for both argument and idlist
        elif node.kind == ND_QREG:
            if node.controlled_with_parameter:
                control_qreg = node.qregs
                if self.GATE_define:
                    for i in range(len(control_qreg)):
                        control_qreg[i] = self.gates[self.GATE_DEF_name].args[control_qreg[i][0]]
                target_qreg = self.code_gen(node.left, quantumcircuit)
                return control_qreg, target_qreg
            else:
                qregs = []
                if self.GATE_define:
                    for i in range(len(node.qregs)):
                        qregs.append(self.gates[self.GATE_DEF_name].args[node.qregs[i][0]])
                    return qregs
                else:
                    return node.qregs
        # creg node
        elif node.kind == ND_CREG:
            return node.cregs
        # if the node is a gate declare node, skip it
        elif node.kind == ND_GATE_DEC:
            return
        # if the node is a opaque declare node, skip it
        elif node.kind == ND_OPAQUE:
            return
        #### the following code is for the single qubit gates without parameters ####
        # X gate
        elif node.kind == ND_X:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("x", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # Y gate
        elif node.kind == ND_Y:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("y", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # Z gate
        elif node.kind == ND_Z:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("z", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # S gate
        elif node.kind == ND_S:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("s", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # T gate
        elif node.kind == ND_T:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("t", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # H gate
        elif node.kind == ND_H:
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_no_parameter("h", qubit_name, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        
        ### The following code is for the single qubit gates with parameters ###
        # Generate the parameters based on explist of Explist node
        elif node.kind == ND_EXP_LIST:
            params = []
            for i in range(len(node.exps)):
                params.append(self.code_gen(node.exps[i], quantumcircuit))
            return params
            
        # RX gate
        elif node.kind == ND_RX:
            parameter = self.code_gen(node.left, quantumcircuit)
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("rx", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # RY gate
        elif node.kind == ND_RY:
            parameter = self.code_gen(node.left, quantumcircuit)
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("ry", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # RZ gate
        elif node.kind == ND_RZ:
            parameter = self.code_gen(node.left, quantumcircuit)
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("rz", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # RTHETA gate
        elif node.kind == ND_RTHETA:
            parameter = self.code_gen(node.left, quantumcircuit)
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("rtheta", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # U gate
        elif node.kind == ND_U:
            parameter = self.code_gen(node.left, quantumcircuit)
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("u", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        # U1 gate
        elif node.kind == ND_U1:
            parameter = [0, 0]
            parameter.extend(self.code_gen(node.left, quantumcircuit))
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("u", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        
        # U2 gate
        elif node.kind == ND_U2:
            parameter = [math.pi/2]
            parameter.extend(self.code_gen(node.left, quantumcircuit))
            qubit = self.code_gen(node.right, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("u", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        
        # Sdg gate
        elif node.kind == ND_SDG:
            parameter = [0, 0, -math.pi/2]
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("u", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        
        # Tdg gate
        elif node.kind == ND_TDG:
            parameter = [0, 0, -math.pi/4]
            qubit = self.code_gen(node.left, quantumcircuit)
            qubit_name = qubit[0][0]
            qubit_idx = qubit[0][1]
            quantumcircuit.add_single_qubit_gate_with_parameter("u", qubit_name, parameter, qubit_idx, self.IF_creg, self.IF_num, self.IF)
        
        # The following code is for the controlled gates without parameters
        # CX gate
        elif node.kind == ND_CX:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("cx", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        
        # CCX gate
        elif node.kind == ND_CCX:
            qubits = self.code_gen(node.left, quantumcircuit)
            control_qubit = qubits[0:2]
            target_name = qubits[2][0]
            target_idx = qubits[2][1]
            quantumcircuit.add_controlled_gate_no_parameter("cx", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CY gate
        elif node.kind == ND_CY:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("cy", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CZ gate
        elif node.kind == ND_CZ:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("cz", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CS gate
        elif node.kind == ND_CS:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("cs", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CT gate
        elif node.kind == ND_CT:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("ct", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CH gate
        elif node.kind == ND_CH:
            control_qubit = self.code_gen(node.left, quantumcircuit)
            target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_no_parameter("ch", control_qubit, target_name, target_idx, self.IF_creg, self.IF_num, self.IF)
        
        ## The following code is for the controlled gates with parameters
        # CRX gate
        elif node.kind == ND_CRX:
            parameter = self.code_gen(node.left, quantumcircuit)
            control_qubit, target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_with_parameter("crx", control_qubit, target_name, parameter, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CRY gate
        elif node.kind == ND_CRY:
            parameter = self.code_gen(node.left, quantumcircuit)
            control_qubit, target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_with_parameter("cry", control_qubit, target_name, parameter, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CRZ gate
        elif node.kind == ND_CRZ:
            parameter = self.code_gen(node.left, quantumcircuit)
            control_qubit, target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_with_parameter("crz", control_qubit, target_name, parameter, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CRTHETA gate
        elif node.kind == ND_CRTHETA:
            parameter = self.code_gen(node.left, quantumcircuit)
            control_qubit, target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_with_parameter("crtheta", control_qubit, target_name, parameter, target_idx, self.IF_creg, self.IF_num, self.IF)
        # CU gate
        elif node.kind == ND_CU:
            parameter = self.code_gen(node.left, quantumcircuit)
            control_qubit, target_qubit = self.code_gen(node.right, quantumcircuit)
            target_name = target_qubit[0][0]
            target_idx = target_qubit[0][1]
            quantumcircuit.add_controlled_gate_with_parameter("cu", control_qubit, target_name, parameter, target_idx, self.IF_creg, self.IF_num, self.IF)
        
        ## The following code is for the gate definition
        # Gate definition without parameters
        elif node.kind == ND_GATE_NOEXP:
            gate_name = node.str
            arguments = self.code_gen(node.left, quantumcircuit)
            # Update the values of the arguments of this gate to the corresponding keys
            i = 0
            for arg in self.gates[gate_name].args:
                self.gates[gate_name].args[arg] = arguments[i]
                i += 1
            # Generate the circuit for the contents of the gate declared
            Gate_def_name_original = self.GATE_DEF_name
            Gate_def_flag_original = self.GATE_define
            self.GATE_define = True
            self.GATE_DEF_name = gate_name
            for i in range(len(self.gates[gate_name].contents)):
                self.code_gen(self.gates[gate_name].contents[i], quantumcircuit)
            self.GATE_define = Gate_def_flag_original
            self.GATE_DEF_name = Gate_def_name_original
            return
        
        # Gate definition with parameters
        elif node.kind == ND_GATE_EXP:
            gate_name = node.str
            explist = self.code_gen(node.left, quantumcircuit)
            arguments = self.code_gen(node.right, quantumcircuit)
            # Update the values of the arguments of this gate to the corresponding keys
            i = 0
            for param in self.gates[gate_name].params:
                self.gates[gate_name].params[param] = explist[i]
                i += 1
            i = 0
            for arg in self.gates[gate_name].args:
                self.gates[gate_name].args[arg] = arguments[i]
                i += 1
            # Generate the circuit for the contents of the gate declared
            Gate_def_name_original = self.GATE_DEF_name
            Gate_def_flag_original = self.GATE_define
            self.GATE_define = True
            self.GATE_DEF_name = gate_name
            for i in range(len(self.gates[gate_name].contents)):
                self.code_gen(self.gates[gate_name].contents[i], quantumcircuit)
            self.GATE_define = Gate_def_flag_original
            self.GATE_DEF_name = Gate_def_name_original
            return
        
        ## The following code is for the opaque definition
        # Gate definition without parameters
        elif node.kind == ND_OPAQUE_NOEXP:
            opaque_name = node.str
            arguments = self.code_gen(node.left, quantumcircuit)
            # call the function to add the opaque gate to the quantum circuit\
            quantumcircuit.add_opaque(opaque_name, arguments, [], self.IF_creg, self.IF_num, self.IF)
            return
        
        # Gate definition with parameters
        elif node.kind == ND_OPAQUE_EXP:
            opaque_name = node.str
            explist = self.code_gen(node.left, quantumcircuit)
            arguments = self.code_gen(node.right, quantumcircuit)
            # call the function to add the opaque gate to the quantum circuit
            quantumcircuit.add_opaque(opaque_name, arguments, explist, self.IF_creg, self.IF_num, self.IF)
            return
        
        ## The following code is for the measurement
        elif node.kind == ND_MEASURE:
            qregs = self.code_gen(node.left, quantumcircuit)
            cregs = self.code_gen(node.right, quantumcircuit)
            # Check whether the all the indexes of the qregs are mapped to the cregs
            if qregs[0][1] == -1 and cregs[0][1] == -1:
                if self.qregs[qregs[0][0]] != 1:
                    # Locally store the name of the qreg and creg
                    qreg_name = qregs[0][0]
                    creg_name = cregs[0][0]
                    # Remove the current element of qregs and cregs list
                    qregs.pop()
                    cregs.pop()
                    # loop through all the qubits 
                    for i in range(self.qregs[qreg_name]):
                        qregs.append((qreg_name, i))
                        cregs.append((creg_name, i))
            # Add the measurement to the quantum circuit
            quantumcircuit.add_measurement(qregs, cregs, self.IF_creg, self.IF_num, self.IF)
            return
        
        ## The following code is for the reset 
        elif node.kind == ND_RESET:
            qregs = self.code_gen(node.left, quantumcircuit)
            # Check whether the qreg is not indexed and the size of the qreg is not 1, if so, reset all the qubits
            if qregs[0][1] == -1 and self.qregs[qregs[0][0]] != 1:
                # Locally store the name of the qreg
                qreg_name = qregs[0][0]
                # Remove the current element of qregs list
                qregs.pop()
                # loop through all the qubits 
                for i in range(self.qregs[qreg_name]):
                    qregs.append((qreg_name, i))
            # Add the reset to the quantum circuit
            quantumcircuit.add_reset(qregs, self.IF_creg, self.IF_num, self.IF)
            return
        ## The following code is for the barrier
        elif node.kind == ND_BARRIER:
            qregs = self.code_gen(node.left, quantumcircuit)
            # Check whether the qreg is not indexed and the size of the qreg is not 1, if so, reset all the qubits
            length = len(qregs)
            for i in range(length):
                if qregs[i][1] == -1 and self.qregs[qregs[i][0]] != 1:
                    qreg_name = qregs[i][0]
                    qregs[i] = (qreg_name, 0)
                    # loop through all the qubits 
                    for j in range(1, self.qregs[qreg_name]):
                        qregs.append((qreg_name, j))
            # Add the barrier to the quantum circuit
            quantumcircuit.add_barrier(qregs)
            return
        
        ## The following code is for the if
        elif node.kind == ND_IF:
            self.IF = True
            condition_creg, condition_num = self.code_gen(node.left, quantumcircuit)
            self.IF_creg = condition_creg[0]
            self.IF_num = condition_num
            self.code_gen(node.right, quantumcircuit)
            self.IF = False
            return
        
        ## The following part is for Unary operations
        # sin
        elif node.kind == ND_SIN:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.sin(exp)
        
        # cos
        elif node.kind == ND_COS:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.cos(exp)
        
        # tan
        elif node.kind == ND_TAN:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.tan(exp)
        
        # exp
        elif node.kind == ND_EXP:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.exp(exp)
        
        # ln
        elif node.kind == ND_LN:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.log(exp)
        
        # sqrt
        elif node.kind == ND_SQRT:
            exp = self.code_gen(node.left, quantumcircuit)
            return math.sqrt(exp)
        
        ## The following part is for binary operations
        else:
            # first get the value of the left hand side
            lhs = self.code_gen(node.left, quantumcircuit)
            # then get the value of the right hand side
            rhs = self.code_gen(node.right, quantumcircuit)
            # add
            if node.kind == ND_ADD:
                return lhs + rhs
        
            # sub
            if node.kind == ND_SUB:
                return lhs - rhs
        
            # mul
            if node.kind == ND_MUL:
                return lhs * rhs
        
            # div
            if node.kind == ND_DIV:
                return lhs / rhs
        
            # pow
            if node.kind == ND_POW:
                return lhs ** rhs
            
            # ==
            if node.kind == ND_EQUAL:
                return lhs, rhs
        
        
    ### Define the function to generate the quantum circuit
    def circuit_gen(self):
        quantumcircuit = Quantum_circuit()
        for i in range(len(self.code)):
            self.code_gen(self.code[i], quantumcircuit)
        return quantumcircuit
    
    #================================================================================================
    # Compilation
    #================================================================================================
    @staticmethod
    def compile(filepath):
        filename, file_str, TK, include_dic = Token.Tokenize(filepath)
        file_node = Filesystem(filename, file_str, TK)
        file_node.set_include_dict(include_dic)
        parser = Parser(file_node)
        parser.Recursive_Descent_Parsing()
        QC = parser.circuit_gen()
        return QC
    
filepath = "qsofinstr/check2.qasm"
QC = Parser.compile(filepath)
QC.test_draw()    