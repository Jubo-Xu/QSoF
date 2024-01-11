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
    
    ''' BNF of modified OpenQASM
    mainprogram := OPENQASM real; program
    program := statement | program statement
    statement := decl 
    | gatedecl goplist }
    '''
    
    
        