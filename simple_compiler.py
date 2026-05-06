import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str
    position: int
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', pos={self.position})"


class Lexer:
    """Converts source code into tokens"""
    
    TOKEN_PATTERNS = [
        ('NUMBER',     r'\d+\.?\d*'),      
        ('IDENTIFIER', r'[a-zA-Z_]\w*'),   
        ('ASSIGN',     r'='),               
        ('PLUS',       r'\+'),             
        ('MINUS',      r'-'),              
        ('MULTIPLY',   r'\*'),              
        ('DIVIDE',     r'/'),               
        ('LPAREN',     r'\('),              
        ('RPAREN',     r'\)'),              
        ('WHITESPACE', r'\s+'),             
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        
    def tokenize(self) -> List[Token]:
        """Perform lexical analysis"""
        tokens = []
        
        while self.pos < len(self.text):
            matched = False
            
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.text, self.pos)
                
                if match:
                    value = match.group(0)
                    if token_type != 'WHITESPACE':  
                        tokens.append(Token(token_type, value, self.pos))
                    self.pos = match.end()
                    matched = True
                    break
            
            if not matched:
                raise SyntaxError(f"Illegal character '{self.text[self.pos]}' at position {self.pos}")
        
        return tokens


@dataclass
class ASTNode:
    """Base class for Abstract Syntax Tree nodes"""
    pass

@dataclass
class NumberNode(ASTNode):
    value: float

@dataclass
class VariableNode(ASTNode):
    name: str

@dataclass
class BinaryOpNode(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode

@dataclass
class AssignmentNode(ASTNode):
    identifier: str
    expression: ASTNode


class Parser:
    """Converts tokens into an Abstract Syntax Tree (AST)"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> Token:
        """Look at current token without consuming it"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self, expected_type: str) -> Token:
        """Consume and return token if it matches expected type"""
        token = self.peek()
        if token is None or token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} but got {token.type if token else 'EOF'}")
        self.pos += 1
        return token
    
    def parse(self) -> AssignmentNode:
        """Parse assignment: IDENTIFIER = Expression"""
        identifier = self.consume('IDENTIFIER')
        self.consume('ASSIGN')
        expression = self.parse_expression()
        return AssignmentNode(identifier.value, expression)
    
    def parse_expression(self) -> ASTNode:
        """Parse expression: Term ((PLUS | MINUS) Term)*"""
        left = self.parse_term()
        
        while self.peek() and self.peek().type in ('PLUS', 'MINUS'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.parse_term()
            left = BinaryOpNode(op.type, left, right)
        
        return left
    
    def parse_term(self) -> ASTNode:
        """Parse term: Factor ((MULTIPLY | DIVIDE) Factor)*"""
        left = self.parse_factor()
        
        while self.peek() and self.peek().type in ('MULTIPLY', 'DIVIDE'):
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.parse_factor()
            left = BinaryOpNode(op.type, left, right)
        
        return left
    
    def parse_factor(self) -> ASTNode:
        """Parse factor: NUMBER | IDENTIFIER | (Expression)"""
        token = self.peek()
        
        if token.type == 'NUMBER':
            self.pos += 1
            return NumberNode(float(token.value))
        
        elif token.type == 'IDENTIFIER':
            self.pos += 1
            return VariableNode(token.value)
        
        elif token.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_expression()
            self.consume('RPAREN')
            return expr
        
        else:
            raise SyntaxError(f"Unexpected token: {token}")



class Evaluator:
    """Evaluates the AST and computes results"""
    
    def __init__(self, variables: Dict[str, float]):
        self.variables = variables
    
    def evaluate(self, node: ASTNode) -> float:
        """Recursively evaluate AST nodes"""
        
        if isinstance(node, NumberNode):
            return node.value
        
        elif isinstance(node, VariableNode):
            if node.name not in self.variables:
                raise NameError(f"Undefined variable: {node.name}")
            return self.variables[node.name]
        
        elif isinstance(node, BinaryOpNode):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            
            if node.operator == 'PLUS':
                return left + right
            elif node.operator == 'MINUS':
                return left - right
            elif node.operator == 'MULTIPLY':
                return left * right
            elif node.operator == 'DIVIDE':
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            else:
                raise ValueError(f"Unknown operator: {node.operator}")
        
        elif isinstance(node, AssignmentNode):
            value = self.evaluate(node.expression)
            self.variables[node.identifier] = value
            return value
        
        else:
            raise TypeError(f"Unknown node type: {type(node)}")



def print_tree(node: ASTNode, indent: int = 0, prefix: str = ""):
    """Pretty print the parse tree"""
    spacing = "  " * indent
    
    if isinstance(node, AssignmentNode):
        print(f"{spacing}{prefix}Assignment")
        print(f"{spacing}  ├─ Identifier: {node.identifier}")
        print(f"{spacing}  └─ Expression:")
        print_tree(node.expression, indent + 2, "")
    
    elif isinstance(node, BinaryOpNode):
        op_symbol = {
            'PLUS': '+', 'MINUS': '-', 
            'MULTIPLY': '*', 'DIVIDE': '/'
        }[node.operator]
        print(f"{spacing}{prefix}BinaryOp: {op_symbol}")
        print(f"{spacing}  ├─ Left:")
        print_tree(node.left, indent + 2, "")
        print(f"{spacing}  └─ Right:")
        print_tree(node.right, indent + 2, "")
    
    elif isinstance(node, NumberNode):
        print(f"{spacing}{prefix}Number: {node.value}")
    
    elif isinstance(node, VariableNode):
        print(f"{spacing}{prefix}Variable: {node.name}")



def main():
    
    expression = "F=32+1.8*C"
    C_value = 20 
    
    print("=" * 60)
    print("SIMPLE EXPRESSION COMPILER")
    print("=" * 60)
    print(f"\nInput Expression: {expression}")
    print(f"Variable C = {C_value}")
    print()
    
    
    print("=" * 60)
    print("PHASE 1: LEXICAL ANALYSIS (Tokenization)")
    print("=" * 60)
    lexer = Lexer(expression)
    tokens = lexer.tokenize()
    
    for i, token in enumerate(tokens):
        print(f"Token {i+1}: {token}")
    print()
    
   
    print("=" * 60)
    print("PHASE 2: PARSING (Syntax Analysis)")
    print("=" * 60)
    parser = Parser(tokens)
    ast = parser.parse()
    print("Abstract Syntax Tree (AST) generated successfully!")
    print()
    
   
    print("=" * 60)
    print("PHASE 3: PARSE TREE STRUCTURE")
    print("=" * 60)
    print_tree(ast)
    print()
    
   
    print("=" * 60)
    print("PHASE 4: SEMANTIC EVALUATION")
    print("=" * 60)
    variables = {'C': C_value}
    evaluator = Evaluator(variables)
    result = evaluator.evaluate(ast)
    
    print(f"Evaluating with C = {C_value}")
    print(f"\nStep-by-step calculation:")
    print(f"  1.8 * C = 1.8 * {C_value} = {1.8 * C_value}")
    print(f"  32 + {1.8 * C_value} = {32 + 1.8 * C_value}")
    print()
    
    
    print("=" * 60)
    print("PHASE 5: FINAL RESULT")
    print("=" * 60)
    print(f"F = {result}°F")
    print(f"\nConversion: {C_value}°C = {result}°F")
    print("=" * 60)
    
    
    print("\n\nTesting with different Celsius values:")
    print("-" * 40)
    for c in [0, 10, 20, 30, 100]:
        lexer = Lexer(expression)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        evaluator = Evaluator({'C': c})
        f = evaluator.evaluate(ast)
        print(f"{c:3d}°C = {f:6.1f}°F")


if __name__ == "__main__":
    main()