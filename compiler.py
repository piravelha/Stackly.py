from parser import parse_expr, Tree, TreeType
from lexer import lex
from typechecker import typecheck

var_counter = 0
def new_quote():
  global var_counter
  result = var_counter
  var_counter += 1
  return f"quote_{result}"
def new_list():
  global var_counter
  result = var_counter
  var_counter += 1
  return f"list_{result}"

def compile(code, tree: Tree, stack="stack"):
  if tree.type == TreeType.PushInt:
    code += f"    {stack}.Push({tree.nodes[0]})\n"
    return code
  if tree.type == TreeType.PushBool:
    val = "true" if tree.nodes[0] == "True" else "false"
    code += f"    {stack}.Push({val})\n"
    return code
  if tree.type == TreeType.PushChar:
    code += f"    {stack}.Push('{tree.nodes[0]}')\n"
    return code
  if tree.type == TreeType.PushList:
    a = new_list()
    code += f"    {a} := Stack{{[]interface{{}}{{}}}}\n"
    code = compile(code, tree.nodes[0], a)
    code += f"    {stack}.Push({a})\n"
  if tree.type == TreeType.PushQuote:
    a = new_quote()
    code += f"    {a} := func(stack *Stack) {{\n"
    code = compile(code, tree.nodes[0], stack)
    code += "    }\n"
    code += f"    {stack}.Push({a})\n"
    return code
  if tree.type == TreeType.Add:
    code += f"    {stack}.Add()\n"
    return code
  if tree.type == TreeType.Sub:
    code += f"    {stack}.Sub()\n"
    return code
  if tree.type == TreeType.Eq:
    code += f"    {stack}.Eq()\n"
    return code
  if tree.type == TreeType.Cons:
    code += f"    {stack}.Cons()\n"
    return code
  if tree.type == TreeType.Print:
    code += f"    {stack}.Print()\n"
    return code
  if tree.type == TreeType.If:
    code += f"    {stack}.If()\n"
  if tree.type == TreeType.Eval:
    code += f"    {stack}.Eval()\n"
    return code
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      code = compile(code, node, stack)
    return code
  return code

def compile_source_code(file, source_code: str):
  tokens = lex(file, source_code)
  tree, _ = parse_expr(tokens)
  stack = typecheck(tree)
  if stack:
    top = stack.pop()
    print(f"{top.location} TYPE ERROR: Program finished with unhandled data on the stack")
    exit(1)
  code = "package main\n"
  code += "func main() {\n"
  code += "    stack := Stack{[]interface{}{}}\n"
  code = compile(code, tree)
  code += "}\n"
  return code

with open("main.stk") as f:
  text = f.read()

with open("main.go", "w") as f:
  f.write(compile_source_code("main.stk", text))
