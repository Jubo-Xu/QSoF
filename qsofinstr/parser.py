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

class Node:
    def __init__(self, kind):
        self.kind = kind
        self.val = 0
        self.str = ""
        self.qregs = []
        self.cregs = []
        self.left = None
        self.right = None
    
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
                   | measure argument -> argument ;
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
                   | id anylist ; | id () anylist ;
                   | id (explist) anylist ;
    anylist     := idlist | mixedlist
    idlist      := id | idlist , id
    mixedlist   := id [nninteger] | mixedlist , id
                   | mixedlist, id [nninteger]
                   | idlist , id [nninteger]
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
            # Check whether the qreg size is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_NUM:
                if self.check_operator_str(self.token_idx, "]"):
                    self.error_at(self.token_idx, "The qreg size is missing")
                else:
                    self.error_at(self.token_idx, "The qreg size should be a number")
            # Check whether the qreg size is an integer
            if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
                self.error_at(self.token_idx, "The qreg size should be an integer")
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
            # Check whether the creg size is missing or wrong type is used
            if self.check_TK_kind(self.token_idx) != token.TK_NUM:
                if self.check_operator_str(self.token_idx, "]"):
                    self.error_at(self.token_idx, "The creg size is missing")
                else:
                    self.error_at(self.token_idx, "The creg size should be a number")
            # Check whether the creg size is an integer
            if self.token[self.token_idx][self.val_idx] != int(self.token[self.token_idx][self.val_idx]) or self.token[self.token_idx][self.exp_idx] != 0:
                self.error_at(self.token_idx, "The creg size should be an integer")
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
            