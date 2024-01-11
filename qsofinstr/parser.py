from token import Token

ND_NUM = 0


class Node:
    def __init__(self, kind):
        self.kind = kind
        self.val = 0
        self.left = None
        self.right = None
    
    def add_left(self, node):
        self.left = node
    
    def add_right(self, node):
        self.right = node

class Parser(Token):
    def __init__(self, TK):
        super().__init__()
        self.token = TK
    
    def create_node(self, kind, leftnode=None, rightnode=None):
        node = Node(kind)
        node.add_left(leftnode)
        node.add_right(rightnode)
        return node
    
    def create_node_num(self, val):
        node = Node(ND_NUM)
        node.val = val
        return node
    
    ### Recursive descent parsing ###
    ''' BNF of modified OpenQASM
    mainprogram := OPENQASM real; program
    program     := statement | program statement
    statement   := decl 
                   | gatedecl goplist }
                   | gatedecl }
                   | opaque id idlist ;
                   | opaque id () idlist ; | opaque id (idlist) idlist ;
                   | qop
                   | if (id == nninteger) qop

    decl        := qreg id [nninteger] ; | creg id [nninteger] ;
    gatedecl    := gate id idlist {
                   | gate id () idlist {
                   | gate id (idlist) idlist {
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
