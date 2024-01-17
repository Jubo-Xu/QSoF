from token import Token
import token

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

class Node:
    def __init__(self, kind):
        self.kind = kind
        self.val = 0
        self.str = ""
        self.qregs = []
        self.cregs = []
        self.left = None
        self.right = None
        self.controlled = False
    
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
            self.params.extend(arg)
        else:
            self.params.append(arg)

class Gate:
    def __init__(self, name):
        self.name = name
        self.params = []
        self.args = []
        self.contents = []
    
    def add_params(self, param):
        if isinstance(param, list):
            self.params.extend(param)
        else:
            self.params.append(param)
    
    def add_args(self, arg):
        if isinstance(arg, list):
            self.args.extend(arg)
        else:
            self.params.append(arg)
    
    def add_contents(self, content_node):
        self.contents.append(content_node)

# The expressions would be represented as a list, where each element is a binary operation node
class Explist(Node):
    def __init__(self, kind):
        super().__init__(kind)
        self.exps = []
    
    def add_exps(self, exp):
        self.exps.append(exp)


class Parser(Token):
    def __init__(self, TK, file_str):
        super().__init__()
        self.token = TK
        self.node = None
        self.token_idx = 0
        self.input_str = file_str
        # Set up the Hash table for opaques, qregs, and cregs
        # For opaques, the key is the name of the opaque, and the element is a tuple of 
        self.opaques = {}
        self.qregs = {}
        self.cregs = {}
        self.gates = {}
        
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
    
    def expect(self, op):
        if self.token[self.token_idx][self.kind_idx] != token.TK_OPERATOR or self.token[self.token_idx][self.str_idx] != op:
            Token.annotate_error(self.input_str, self.token[self.token_idx][self.idx_idx], "missing operator: " + op, self.token[self.token_idx][self.line_idx], self.token[self.token_idx][self.err_line_idx])
        self.token_idx += 1
    
    def check_TK_kind(self, idx):
        return self.token[idx][self.kind_idx]

    def check_operator_str(self, idx, str):
        return self.token[idx][self.kind_idx] == token.TK_OPERATOR and self.token[idx][self.str_idx] == str
    
    def error_at(self, idx, message):
        Token.annotate_error(self.input_str, self.token[idx][self.idx_idx], message, self.token[idx][self.line_idx], self.token[idx][self.err_line_idx])
    
    def check_num_error(self, name):
        # Check whether the qreg or creg size is missing or wrong type is used
        if self.check_TK_kind(self.token_idx) != token.TK_NUM:
            if self.check_operator_str(self.token_idx, "]"):
                self.error_at(self.token_idx, "There has to be a number for the "+name)
            else:
                self.error_at(self.token_idx, "The "+name+" should be a number")
        # Check whether the qreg or creg size is an integer
        if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
            self.error_at(self.token_idx, "The "+name+" should be an integer")
    
    ### Recursive descent parsing ###
    ''' BNF of modified OpenQASM
    mainprogram := OPENQASM real; program
    program     := statement | program statement
    statement   := decl 
                   | gatedecl 
                   | opaque id idlist ;
                   | opaque id () idlist ; | opaque id (idlist) idlist ;
                   | qop
                   | if (condition) qop
    condition   := id == nninteger

    decl        := qreg id [nninteger] ; | creg id [nninteger] ;
    gatedecl    := gate id idlist {goplist}
                   | gate id () idlist {goplist}
                   | gate id (idlist) idlist {goplist}
    goplist     := uop 
                   | goplist uop 
    qop         := uop 
                   | measure argument -> argument_c ;
                   | reset argument ;
    uop         := U (explist) argument ;
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
                   | id (explist) idlist ;
    idlist     := id | id [nninteger], idlist
    argument_c  := id | id [nninteger]
    argument    := id | id [nninteger]
    explist     := exp | explist , exp
    exp         := real | nninteger | pi | id
                   | exp + exp | exp - exp | exp * exp 
                   | exp / exp | - exp | exp ^ exp
                   | (exp) | unaryop (exp)
    unaryop     := sin | cos | tan | exp | ln | sqrt
    
    id          := [a-z][A-Za-z0-9_]*
    real        := ([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)([eE][-+]?[0-9]+)?
    nninteger   := [1-9]+[0-9]*|0
                   
    '''
    # First starting with the statement
    def statement(self):
        if self.check_TK_kind(self.token_idx) == token.TK_QREG or self.check_TK_kind(self.token_idx) == token.TK_CREG:
            return self.decl()
        elif self.check_TK_kind(self.token_idx) == token.TK_GATE:
            return self.gatedecl()
        elif self.check_TK_kind(self.token_idx) == token.TK_OPAQUE:
            # Check whether the opaque is already defined
            if self.token[self.token_idx+1][self.str_idx] in self.opaques:
                Token.annotate_error(self.input_str, self.token[self.token_idx+1][self.idx_idx], "opaque "+self.token[self.token_idx+1][self.str_idx]\
                                      +" already defined", self.token[self.token_idx+1][self.line_idx], self.token[self.token_idx+1][self.err_line_idx])
            if self.check_operator_str(self.token_idx+2, "("):
                # Recursive descent parsing for 'opaque id (idlist) idlist ;'
                if self.check_TK_kind(self.token_idx+3) == token.TK_IDENT:
                    name = self.token[self.token_idx+1][self.str_idx]
                    self.token_idx += 3
                    opaque_instance = Opaque(name)
                    params = self.idlist()
                    opaque_instance.add_params(params)
                    self.expect(")")
                    args = self.idlist()
                    opaque_instance.add_args(args)
                    self.expect(";")
                    self.opaques[name] = opaque_instance
                    node_stmt = Parser.create_node(ND_OPAQUE)
                    node_stmt.add_str(name)
                    return node_stmt
                # Recursive descent parsing for 'opaque id () idlist ;'
                elif self.check_operator_str(self.token_idx+3, ")"):
                    name = self.token[self.token_idx+1][self.str_idx]
                    self.token_idx += 4
                    opaque_instance = Opaque(name)
                    args = self.idlist()
                    opaque_instance.add_args(args)
                    self.expect(";")
                    self.opaques[name] = opaque_instance
                    node_stmt = Parser.create_node(ND_OPAQUE)
                    node_stmt.add_str(name)
                    return node_stmt
                else:
                    self.error_at(self.token_idx+3, "The parameters could only be identifiers or empty")
            # Recursive descent parsing for 'opaque id idlist ;'
            elif self.check_TK_kind(self.token_idx+2) == token.TK_IDENT:
                name = self.token[self.token_idx+1][self.str_idx]
                self.token_idx += 3
                opaque_instance = Opaque(name)
                args = self.idlist()
                opaque_instance.add_args(args)
                self.expect(";")
                self.opaques[name] = opaque_instance
                node_stmt = Parser.create_node(ND_OPAQUE)
                node_stmt.add_str(name)
                return node_stmt
            # Check for some errors
            else:
                if self.check_operator_str(self.token_idx+2, ";"):
                    self.error_at(self.token_idx+2, "The arguments cannot be empty")
                elif self.check_operator_str(self.token_idx+2, ","):
                    self.error_at(self.token_idx+2, "The opaque name cannot be empty")
                else:
                    self.error_at(self.token_idx+2, "The arguments or parameters cannot be this type")
        # Recursive descent parsing for 'if (condition) qop'
        elif self.check_TK_kind(self.token_idx) == token.TK_IF:
            self.token_idx += 1
            self.expect("(")
            condition = self.condition()
            self.expect(")")
            if self.check_operator_str(self.token_idx, ";"):
                self.error_at(self.token_idx, "The statement of if cannot be empty")
            qop = self.qop()
            node_stmt = Parser.create_node(ND_IF, condition, qop)
        # Recursive descent parsing for 'qop'
        else:
            return self.qop()
    
    # Recursive descent parsing for 'condition := id == nninteger'
    def condition(self):
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.token_idx, ")"):
                self.error_at(self.token_idx, "The condition cannot be empty")
            else:
                self.error_at(self.token_idx, "The condition cannot be this type")
        condition_lhs = self.create_node_creg((self.token[self.token_idx][self.str_idx], -1))
        self.expect("==")
        condition_rhs = self.create_node_num(self.token[self.token_idx][self.val_idx])
        node_condition = Parser.create_node(ND_EQUAL, condition_lhs, condition_rhs)
        return node_condition
    
    # Recursive descent parsing for 'decl := qreg id [nninteger] ; | creg id [nninteger] ;'
    def decl(self):
        # Recursive descent parsing for 'qreg id [nninteger] ;'
        if self.check_TK_kind(self.token_idx) == token.TK_QREG:
            self.token_idx += 1
            # Check whether the qreg name is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.token_idx, "["):
                    self.error_at(self.token_idx, "The qreg name is missing")
                else:
                    self.error_at(self.token_idx, "The qreg name cannot be this type")
            # Check whether the qreg name is already defined
            if self.token[self.token_idx][self.str_idx] in self.qregs:
                self.error_at(self.token_idx, "qreg "+self.token[self.token_idx][self.str_idx]+" already defined")
            name = self.token[self.token_idx][self.str_idx]
            self.token_idx += 1
            self.expect("[")
            # # Check whether the qreg size is missing or wrong type is used
            # if self.check_TK_kind(self.token_idx) != token.TK_NUM:
            #     if self.check_operator_str(self.token_idx, "]"):
            #         self.error_at(self.token_idx, "The qreg size is missing")
            #     else:
            #         self.error_at(self.token_idx, "The qreg size should be a number")
            # # Check whether the qreg size is an integer
            # if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
            #     self.error_at(self.token_idx, "The qreg size should be an integer")
            self.check_num_error("qreg size")
            size = int(self.token[self.token_idx][self.val_idx])
            self.qregs[name] = size
            self.expect("]")
            self.expect(";")
            node_decl = Parser.create_node(ND_QREG_DEC)
            node_decl.add_str(name)
            return node_decl
        # Recursive descent parsing for 'creg id [nninteger] ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CREG:
            self.token_idx += 1
            # Check whether the creg name is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.token_idx, "["):
                    self.error_at(self.token_idx, "The creg name is missing")
                else:
                    self.error_at(self.token_idx, "The creg name cannot be this type")
            # Check whether the creg name is already defined
            if self.token[self.token_idx][self.str_idx] in self.cregs:
                self.error_at(self.token_idx, "creg "+self.token[self.token_idx][self.str_idx]+" already defined")
            name = self.token[self.token_idx][self.str_idx]
            self.token_idx += 1
            self.expect("[")
            # # Check whether the creg size is missing or wrong type is used
            # if self.check_TK_kind(self.token_idx) != token.TK_NUM:
            #     if self.check_operator_str(self.token_idx, "]"):
            #         self.error_at(self.token_idx, "The creg size is missing")
            #     else:
            #         self.error_at(self.token_idx, "The creg size should be a number")
            # # Check whether the creg size is an integer
            # if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
            #     self.error_at(self.token_idx, "The creg size should be an integer")
            self.check_num_error("creg size")
            size = int(self.token[self.token_idx][self.val_idx])
            self.qregs[name] = size
            self.expect("]")
            self.expect(";")
            node_decl = Parser.create_node(ND_CREG_DEC)
            node_decl.add_str(name)
            return node_decl
        # Check for some errors
        else:
            if self.check_operator_str(self.token_idx, ";"):
                self.error_at(self.token_idx, "The declaration cannot be empty")
            elif self.check_operator_str(self.token_idx, "["):
                self.error_at(self.token_idx, "The qreg name cannot be empty")
            else:
                self.error_at(self.token_idx, "The declaration cannot be this type")
    
    # Recursive descent parsing for 'gatedecl := gate id idlist {goplist}|gate id () idlist {goplist}|gate id (idlist) idlist {goplist}'
    def gatedecl(self):
        # Check whether the gate keyword is missing
        if self.check_TK_kind(self.token_idx) != token.TK_GATE:
            self.error_at(self.token_idx, "The gate keyword is missing")
        self.token_idx += 1
        # Check whether the gate name is missing or wrong type is used 
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.token_idx, "("):
                self.error_at(self.token_idx, "The gate name is missing")
            elif self.check_operator_str(self.token_idx, "{") or self.check_operator_str(self.token_idx, ";"):
                self.error_at(self.token_idx, "The gate name and the arguments are missing")
            else:
                self.error_at(self.token_idx, "The gate name cannot be this type")
        if self.check_TK_kind(self.token_idx) == token.TK_IDENT and self.check_operator_str(self.token_idx+1, ","):
            self.error_at(self.token_idx, "The gate name is missing")
        # Check whether the gate is already defined 
        if self.token[self.token_idx][self.str_idx] in self.gates:
            self.error_at(self.token_idx, "gate "+self.token[self.token_idx][self.str_idx]+" already defined")
        name = self.token[self.token_idx][self.str_idx]
        self.token_idx += 1
        if self.check_operator_str(self.token_idx, "("):
            self.token_idx += 1
            params = []
            # Check for empty parameters
            if self.check_operator_str(self.token_idx, ")"):
                self.token_idx += 1
            # Check for nonempty parameters
            if self.check_TK_kind(self.token_idx) == token.TK_IDENT:
                params.extend(self.idlist())
            # Check for some errors 
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT and not self.check_operator_str(self.token_idx, ")"):
                self.error_at(self.token_idx, "The parameters should be identifiers")
            self.expect(")")
        # Check whether the arguments are missing or wrong type is used
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            if self.check_operator_str(self.token_idx, "{"):
                self.error_at(self.token_idx, "The arguments are missing")
            elif self.check_operator_str(self.token_idx, ";"):
                self.error_at(self.token_idx, "The arguments and the contents are missing")
            else:
                self.error_at(self.token_idx, "The arguments cannot be this type")
        args = self.idlist()
        self.expect("{")
        gate_val = Gate(name)
        while not self.check_operator_str(self.token_idx, "}"):
            gate_val.add_contents(self.uop())
        self.expect("}")
        gate_val.add_params(params)
        gate_val.add_args(args)
        self.gates[name] = gate_val
        node_gatedecl = Parser.create_node(ND_GATE_DEC)
        node_gatedecl.add_str(name)
        return node_gatedecl
                
    # Recursive descent parsing for 'qop := uop | measure argument -> argument ; | reset argument ;'
    def qop(self):
        # Recursive descent parsing for 'measure argument -> argument ;'
        if self.check_TK_kind(self.token_idx) == token.TK_MEASURE:
            self.token_idx += 1
            # Check whether the argument is missing or wrong type is used 
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.token_idx, "->"):
                    self.error_at(self.token_idx, "The qreg argument is missing")
                elif self.check_operator_str(self.token_idx, ";"):
                    self.error_at(self.token_idx, "The qreg argument and the destination are missing")
                else:
                    self.error_at(self.token_idx, "The qreg argument cannot be this type")
            node_lhs = self.argument()
            self.expect("->")
            # Check whether the destination is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.token_idx, ";"):
                    self.error_at(self.token_idx, "The creg destination is missing")
                else:
                    self.error_at(self.token_idx, "The creg destination cannot be this type")
            node_rhs = self.argument_c()
            self.expect(";")
            node_qof = Parser.create_node(ND_MEASURE, node_lhs, node_rhs)
            return node_qof
        elif self.check_TK_kind(self.token_idx) == token.TK_RESET:
            self.token_idx += 1
            # Check whether the argument is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                if self.check_operator_str(self.token_idx, ";"):
                    self.error_at(self.token_idx, "The qreg argument is missing")
                else:
                    self.error_at(self.token_idx, "The qreg argument cannot be this type")
            node_lhs = self.argument()
            node_qof = Parser.create_node(ND_RESET, node_lhs)
            return node_qof
        else:
            return self.uop()
    
    # Recursive descent parsing for 'argument := id | id [nninteger]'
    def argument(self):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            self.error_at(self.token_idx, "The qreg argument should be an identifier")
        # Check whether the argument is already defined 
        if not self.token[self.token_idx][self.str_idx] in self.qregs:
            self.error_at(self.token_idx, "qreg "+self.token[self.token_idx][self.str_idx]+" not defined")
        name = self.token[self.token_idx][self.str_idx]
        self.token_idx += 1
        # Check whether the argument is indexed
        if self.check_operator_str(self.token_idx, "["):
            # Check whether the qreg size is missing or wrong type is used
            self.token_idx += 1
            # if self.check_TK_kind(self.token_idx) != token.TK_NUM:
            #     if self.check_operator_str(self.token_idx, "]"):
            #         self.error_at(self.token_idx, "There has to be a number for the qreg index")
            #     else:
            #         self.error_at(self.token_idx, "The qreg index should be a number")
            # # Check whether the qreg size is an integer
            # if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
            #     self.error_at(self.token_idx, "The qreg size should be an integer")
            self.check_num_error("qreg index")
            index = int(self.token[self.token_idx][self.val_idx])
            node_argument = Parser.create_node_qreg((name, index))
            self.expect("]")
            return node_argument
        else:
            node_argument = Parser.create_node_qreg((name, -1))
            return node_argument
    
    # Recursive descent parsing for 'argument_c := id | id [nninteger]'
    def argument_c(self):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            self.error_at(self.token_idx, "The creg argument should be an identifier")
        # Check whether the argument is already defined 
        if not self.token[self.token_idx][self.str_idx] in self.cregs:
            self.error_at(self.token_idx, "creg "+self.token[self.token_idx][self.str_idx]+" not defined")
        name = self.token[self.token_idx][self.str_idx]
        self.token_idx += 1
        # Check whether the argument is indexed
        if self.check_operator_str(self.token_idx, "["):
            # Check whether the creg size is missing or wrong type is used
            self.token_idx += 1
            # if self.check_TK_kind(self.token_idx) != token.TK_NUM:
            #     if self.check_operator_str(self.token_idx, "]"):
            #         self.error_at(self.token_idx, "There has to be a number for the creg index")
            #     else:
            #         self.error_at(self.token_idx, "The creg index should be a number")
            # # Check whether the creg size is an integer
            # if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
            #     self.error_at(self.token_idx, "The creg size should be an integer")
            self.check_num_error("creg index")
            index = int(self.token[self.token_idx][self.val_idx])
            node_argument = Parser.create_node_creg((name, index))
            self.expect("]")
            return node_argument
        else:
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
        self.token_idx += 1
        self.expect("(")
        # Check whether the explist is missing
        if self.check_operator_str(self.token_idx, ")"):
            self.error_at(self.token_idx, "The explist of "+name+" is missing")
        explist = self.explist()
        self.expect(")")
        # Check whether the argument is missing
        if self.check_operator_str(self.token_idx, ";"):
            self.error_at(self.token_idx, "The argument of "+name+" is missing")
        argument = self.argument()
        self.expect(";")
        node_uop = Parser.create_node(kind, explist, argument)
        return node_uop
    
    def uop_without_explist_single(self, kind, name):
        self.token_idx += 1
        # Check whether the argument is missing
        if self.check_operator_str(self.token_idx, ";"):
            self.error_at(self.token_idx, "The argument of"+name+"is missing")
        argument = self.argument()
        self.expect(";")
        node_uop = Parser.create_node(kind, argument)
        return node_uop
    
    def uop_without_explist_controlled(self, kind, name):
        self.token_idx += 1
        # Check whether the first argument is missing
        if self.check_operator_str(self.token_idx, ","):
            self.error_at(self.token_idx, "The first argument of "+name+" is missing")
        argument_lhs = self.argument()
        argument_lhs.controlled = True
        self.expect(",")
        # Check whether the second argument is missing
        if self.check_operator_str(self.token_idx, ";"):
            self.error_at(self.token_idx, "The second argument of "+name+" is missing")
        argument_rhs = self.argument()
        self.expect(";")
        node_uop = Parser.create_node(kind, argument_lhs, argument_rhs)
        return node_uop
    
    def uop_with_explist_controlled(self, kind, name):
        self.token_idx += 1
        self.expect("(")
        # Check whether the explist is missing
        if self.check_operator_str(self.token_idx, ")"):
            self.error_at(self.token_idx, "The explist of "+name+" is missing")
        explist = self.explist()
        self.expect(")")
        # Check whether the first argument is missing
        if self.check_operator_str(self.token_idx, ","):
            self.error_at(self.token_idx, "The first argument of "+name+" is missing")
        argument_control = self.argument()
        argument_control.controlled = True
        self.expect(",")
        # Check whether the second argument is missing
        if self.check_operator_str(self.token_idx, ";"):
            self.error_at(self.token_idx, "The second argument of "+name+" is missing")
        argument_target = self.argument()
        self.expect(";")
        argument_control.add_left(argument_target)
        node_uop = Parser.create_node(kind, explist, argument_control)
        return node_uop
    
    def uop(self):
        # Recursive descent parsing for 'U (explist) argument ;'
        if self.check_TK_kind(self.token_idx) == token.TK_U:
            node_uop = self.uop_with_explist_single(ND_U, "U")
            return node_uop
        # Recursive descent parsing for 'CX argument , argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CX:
            node_uop = self.uop_without_explist_controlled(ND_CX, "CX")
            return node_uop
        # Recursive descent parsing for 'X argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_X:
            node_uop = self.uop_without_explist_single(ND_X, "X")
            return node_uop
        # Recursive descent parsing for 'Y argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_Y:
            node_uop = self.uop_without_explist_single(ND_Y, "Y")
            return node_uop
        # Recursive descent parsing for 'Z argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_Z:
            node_uop = self.uop_without_explist_single(ND_Z, "Z")
            return node_uop
        # Recursive descent parsing for 'S argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_S:
            node_uop = self.uop_without_explist_single(ND_S, "S")   
            return node_uop
        # Recursive descent parsing for 'T argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_T:
            node_uop = self.uop_without_explist_single(ND_T, "T")
            return node_uop
        # Recursive descent parsing for 'RTHETA (explist) argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_RTHETA:
            node_uop = self.uop_with_explist_single(ND_RTHETA, "RTHETA")
            return node_uop
        # Recursive descent parsing for 'RX (explist) argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_RX:
            node_uop = self.uop_with_explist_single(ND_RX, "RX")
            return node_uop
        # Recursive descent parsing for 'RY (explist) argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_RY:
            node_uop = self.uop_with_explist_single(ND_RY, "RY")
            return node_uop
        # Recursive descent parsing for 'RZ (explist) argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_RZ:
            node_uop = self.uop_with_explist_single(ND_RZ, "RZ")
            return node_uop
        # Recursive descent parsing for 'H argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_H:
            node_uop = self.uop_without_explist_single(ND_H, "H")
            return node_uop
        # Recursive descent parsing for 'CY argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CY:
            node_uop = self.uop_without_explist_controlled(ND_CY, "CY")
            return node_uop
        # Recursive descent parsing for 'CZ argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CZ:
            node_uop = self.uop_without_explist_controlled(ND_CZ, "CZ")
            return node_uop
        # Recursive descent parsing for 'CU (explist) argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CU:
            node_uop = self.uop_with_explist_controlled(ND_CU, "CU")
            return node_uop
        # Recursive descent parsing for 'CS argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CS:
            node_uop = self.uop_without_explist_controlled(ND_CS, "CS")
            return node_uop
        # Recursive descent parsing for 'CT argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CT:
            node_uop = self.uop_without_explist_controlled(ND_CT, "CT")
            return node_uop
        # Recursive descent parsing for 'CRTHETA (explist) argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CRTHETA:
            node_uop = self.uop_with_explist_controlled(ND_CRTHETA, "CRTHETA")
            return node_uop
        # Recursive descent parsing for 'CRX (explist) argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CRX:
            node_uop = self.uop_with_explist_controlled(ND_CRX, "CRX")
            return node_uop
        # Recursive descent parsing for 'CRY (explist) argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CRY:
            node_uop = self.uop_with_explist_controlled(ND_CRY, "CRY")
            return node_uop
        # Recursive descent parsing for 'CRZ (explist) argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CRZ:
            node_uop = self.uop_with_explist_controlled(ND_CRZ, "CRZ")
            return node_uop
        # Recursive descent parsing for 'CH argument, argument ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_CH:
            node_uop = self.uop_without_explist_controlled(ND_CH, "CH")
            return node_uop
        # Recursive descent parsing for 'id idlist ; | id () idlist ; | id (explist) idlist ;'
        elif self.check_TK_kind(self.token_idx) == token.TK_IDENT:
            # Check whether the gate is already defined 
            if not self.token[self.token_idx][self.str_idx] in self.gates:
                self.error_at(self.token_idx, "gate "+self.token[self.token_idx][self.str_idx]+" not defined")
            self.token_idx += 1
            if self.check_operator_str(self.token_ix, "("):
                self.token_idx += 1
                if self.check_operator_str(self.token_idx, ")"):
                    self.expect(")")
                    # Check whether the arguments are missing or wrong type is used
                    if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                        if self.check_operator_str(self.token_idx, ";"):
                            self.error_at(self.token_idx, "The arguments of the gate are missing")
                        else:
                            self.error_at(self.token_idx, "The arguments cannot be this type")
                    args = self.idlist()
                    self.expect(";")
                    node_uop = Parser.create_node(ND_GATE_NOEXP, args)
                    return node_uop
                else:
                    explist = self.explist()
                    self.expect(")")
                     # Check whether the arguments are missing or wrong type is used
                    if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
                        if self.check_operator_str(self.token_idx, ";"):
                            self.error_at(self.token_idx, "The arguments of the gate are missing")
                        else:
                            self.error_at(self.token_idx, "The arguments cannot be this type")
                    args = self.idlist()
                    self.expect(";")
                    node_uop = Parser.create_node(ND_GATE_EXP, explist, args)
                    return node_uop
            elif self.check_TK_kind(self.token_idx) == token.TK_IDENT:
                args = self.idlist()
                self.expect(";")
                node_uop = Parser.create_node(ND_GATE_NOEXP, args)
                return node_uop
            # Check for some errors
            else:
                if self.check_operator_str(self.token_idx, ","):
                    self.error_at(self.token_idx, "The gate name cannot be empty")
                else:
                    self.error_at(self.token_idx, "The arguments cannot be this type")
        # Check for some errors
        else:
            if self.check_operator_str(self.token_idx, ";"):
                self.error_at(self.token_idx, "The gate operation cannot be empty")
            else:
                self.error_at(self.token_idx, "The gate operation cannot be this type")
    
    # Recursive descent parsing for 'idlist := id | id [nninteger], idlist'
    def id_check(self, qreglist):
        # Check whether the argument is identifier
        if self.check_TK_kind(self.token_idx) != token.TK_IDENT:
            self.error_at(self.token_idx, "The type should be identifier")
        # Check whether the qreg is already defined
        if not self.token[self.token_idx][self.str_idx] in self.qregs:
            self.error_at(self.token_idx, "qreg "+self.token[self.token_idx][self.str_idx]+" not defined")
        name = self.token[self.token_idx][self.str_idx]
        self.token_idx += 1
        # Check whether the argument is indexed
        if self.check_operator_str(self.token_idx, "["):
            self.token_idx += 1
            self.check_num_error("qreg index")
            idx = int(self.token[self.token_idx][self.val_idx])
            self.expect("]")
            qreglist.append((name, idx))
        else:
            qreglist.append((name, -1))
        
    def idlist(self):
        qreglist = []
        self.id_check(qreglist)
        while not self.check_operator_str(self.token_idx, ";"):
            self.expect(",")
            self.id_check(qreglist)
        node_idlist = Parser.create_node_qreg(qreglist)
        return node_idlist