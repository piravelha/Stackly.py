from parsing import Tree, TreeType, parse_expr
from lexer import lex
from typechecker import typecheck
import time
import os

def value_repr(value):
    if isinstance(value, list):
        return "[" + " ".join([str(v) for v in value]) + "]"
    return repr(value)

def print_stack(stack):
  padding = 3
  lpad = "  "
  if stack:
    max_length = max(len(str(v)) for v in stack) + padding
  else:
    max_length = padding
    final = "-" * max_length + "\n"
    final += "| " + " " * (max_length - 4) + " |\n"
    final += "-" * max_length + "\n"
    return print(final)
  reprs = []
  for value in reversed(stack):
    reprs.append(value_repr(value).center(max_length))
  final = ""
  for repr in reprs:
    final += lpad + "-" * (max_length + 4) + "\n"
    final += lpad + "| " + repr + " |\n"
  final += lpad + "-" * (max_length + 4) + "\n"
  print(final)

print_queue = []

def debug(tree, stack):
  global print_queue
  if tree.type == TreeType.PushInt:
    stack.append(int(tree.nodes[0]))
    return stack
  if tree.type == TreeType.PushChar:
    stack.append(tree.nodes[0])
    return stack
  if tree.type == TreeType.PushBool:
    stack.append(tree.nodes[0] == "True")
    return stack
  if tree.type == TreeType.PushList:
    list = debug(tree.nodes[0], [])
    stack.append(list)
    return stack
  if tree.type == TreeType.Add:
    b = stack.pop()
    a = stack.pop()
    stack.append(a + b)
    return stack
  if tree.type == TreeType.Sub:
    b = stack.pop()
    a = stack.pop()
    stack.append(a - b)
    return stack
  if tree.type == TreeType.Mul:
    b = stack.pop()
    a = stack.pop()
    stack.append(a * b)
    return stack
  if tree.type == TreeType.Div:
    b = stack.pop()
    a = stack.pop()
    stack.append(int(a / b))
    return stack
  if tree.type == TreeType.Lt:
    b = stack.pop()
    a = stack.pop()
    stack.append(a < b)
    return stack
  if tree.type == TreeType.Gt:
    b = stack.pop()
    a = stack.pop()
    stack.append(a > b)
    return stack
  if tree.type == TreeType.Lte:
    b = stack.pop()
    a = stack.pop()
    stack.append(a <= b)
    return stack
  if tree.type == TreeType.Gte:
    b = stack.pop()
    a = stack.pop()
    stack.append(a >= b)
    return stack
  if tree.type == TreeType.Eq:
    b = stack.pop()
    a = stack.pop()
    stack.append(a == b)
    return stack
  if tree.type == TreeType.Not:
    a = stack.pop()
    stack.append(not a)
    return stack
  if tree.type == TreeType.Cons:
    b = stack.pop()
    a = stack.pop()
    stack.append([a] + b)
    return stack
  if tree.type == TreeType.PushQuote:
    stack.append(tree.nodes[0])
    return stack
  if tree.type == TreeType.Eval:
    a = stack.pop()
    stack = debug(a, stack)
    return stack
  if tree.type == TreeType.Dup:
    a = stack.pop()
    stack.append(a)
    stack.append(a)
    return stack
  if tree.type == TreeType.If:
    c = stack.pop()
    b = stack.pop()
    a = stack.pop()
    if a:
      stack = debug(b, stack)
    else:
      stack = debug(c, stack)
    return stack
  if tree.type == TreeType.While:
    b = stack.pop()
    a = stack.pop()
    while True:
      stack = debug(a, stack)
      if not stack.pop():
        break
      stack = debug(b, stack)
    return stack
  if tree.type == TreeType.Print:
    a = stack.pop()
    print_queue.append(a)
    return stack
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      stack = debug(node, stack)
    return stack

def debug_program(tree):
  global print_queue
  nodes = tree.nodes
  stack = []
  prev = []
  for node in nodes:
    os.system("clear")
    print_stack(prev)
    for q in print_queue:
      print(q)
    print_queue = []
    print("Executing node:", node, "(ENTER)")
    input("")
    stack = debug(node, stack)
    print_stack(stack)
    prev = stack.copy()
  os.system("clear")
  print_stack(prev)
  for q in print_queue:
    print(q)
  print_queue = []
    
  print("\n\nProgram finished with no abnormalities")

if __name__ == "__main__":
  with open("main.stk") as f:
    text = f.read()

  tokens = lex("main.stk", text)
  tree, _ = parse_expr(tokens)
  stack = typecheck(tree)
  if stack:
    print(f"{stack.pop().location} TYPE ERROR: Progran finished with unhandled data on the stack")
    exit(1)
  debug_program(tree)
