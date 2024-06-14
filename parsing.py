from lexer import lex, Token, TokenType, Location
from dataclasses import dataclass
from enum import Enum, auto

class TreeType(Enum):
  PushInt = auto()
  PushBool = auto()
  PushChar = auto()
  PushList = auto()
  Add = auto()
  Sub = auto()
  Mul = auto()
  Div = auto()
  Cons = auto()
  Lt = auto()
  Gt = auto()
  Lte = auto()
  Gte = auto()
  Eq = auto()
  Not = auto()
  PushQuote = auto()
  Eval = auto()
  Print = auto()
  Expr = auto()
  TypeCast = auto()
  Dup = auto()
  If = auto()
  While = auto()
  Noop = auto()

tree_to_name = {
  "Add": "+",
  "Sub": "-",
  "Eq": "=",
  "Eval": "~",
  "Print": "print",
}

@dataclass
class Tree:
  type: TreeType
  nodes: list
  location: Location
  def __repr__(self):
    if self.type == TreeType.Expr:
      return "{" + " ".join([str(n) for n in self.nodes]) + "}"
    if not self.nodes:
      if tree_to_name.get(self.type.name):
        return tree_to_name[self.type.name]
      return self.type.name
    if self.type == TreeType.PushInt:
      return str(self.nodes[0])
    if self.type.name.startswith("Push"):
      return str(self.nodes)[1:-1]
    return f"{self.type.name}{{{self.nodes}}}"

macro_env = {}

def parse_atom(tokens):
  first = tokens[0]
  if first.type == TokenType.Int:
    return Tree(TreeType.PushInt, [first.value], first.location), tokens[1:]
  if first.type == TokenType.Char:
    return Tree(TreeType.PushChar, [first.value], first.location), tokens[1:]
  if first.type == TokenType.Word:
    if first.value == "True" or first.value == "False":
      return Tree(TreeType.PushBool, [first.value], first.location), tokens[1:]
    if first.value == "+":
      return Tree(TreeType.Add, [], first.location), tokens[1:]
    if first.value == "-":
      return Tree(TreeType.Sub, [], first.location), tokens[1:]
    if first.value == "*":
      return Tree(TreeType.Mul, [], first.location), tokens[1:]
    if first.value == "/":
      return Tree(TreeType.Div, [], first.location), tokens[1:]
    if first.value == "<:":
      return Tree(TreeType.Cons, [], first.location), tokens[1:]
    if first.value == "<":
      return Tree(TreeType.Lt, [], first.location), tokens[1:]
    if first.value == ">":
      return Tree(TreeType.Gt, [], first.location), tokens[1:]
    if first.value == "<=":
      return Tree(TreeType.Lte, [], first.location), tokens[1:]
    if first.value == ">=":
      return Tree(TreeType.Gte, [], first.location), tokens[1:]
    if first.value == "=":
      return Tree(TreeType.Eq, [], first.location), tokens[1:]
    if first.value == "not":
      return Tree(TreeType.Not, [], first.location), tokens[1:]
    if first.value == "~":
      return Tree(TreeType.Eval, [], first.location), tokens[1:]
    if first.value == "print":
      return Tree(TreeType.Print, [], first.location), tokens[1:]
    if first.value == "if":
      return Tree(TreeType.If, [], first.location), tokens[1:]
    if first.value == "while":
      return Tree(TreeType.While, [], first.location), tokens[1:]
    if first.value == ".":
      return Tree(TreeType.Dup, [], first.location), tokens[1:]
    if first.value == "define":
      name = tokens[1]
      body, tokens = parse_expr(tokens[2:])
      end = tokens[0]
      if end.value != "end":
        print(end.value)
        print(f"{first.location} PARSE ERROR: Unterminated macro declaration")
        exit(1)
      macro_env[name.value] = body
      return Tree(TreeType.Noop, [], first.location), tokens[1:]
    if macro_env.get(first.value):
      return macro_env[first.value], tokens[1:]
  if first.type == TokenType.OpenQuote:
    body, tokens = parse_expr(tokens[1:])
    if tokens[0].type != TokenType.CloseQuote:
      print(f"{first.location} PARSE ERROR: Unterminated quote definition")
      exit(1)
    return Tree(TreeType.PushQuote, [body], first.location), tokens[1:]
  if first.type == TokenType.OpenBracket:
    body, tokens = parse_expr(tokens[1:])
    if tokens[0].type != TokenType.CloseBracket:
      print(f"{first.location} PARSE ERROR: Unterminated list definition")
      exit(1)
    return Tree(TreeType.PushList, [body], first.location), tokens[1:]
  return None, tokens

def parse_expr(tokens):
  if not tokens:
    return Tree(TreeType.Expr, [], Location("", 0, 0)), tokens
  first = tokens[0]
  nodes = []
  while tokens:
    node, new_tokens = parse_atom(tokens)
    if node == None:
      break
    tokens = new_tokens
    nodes.append(node)
  return Tree(TreeType.Expr, nodes, first.location), tokens

