from parsing import parse_expr, Tree, TreeType
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
    code += f"    {stack} = append({stack}, {tree.nodes[0]})\n"
    return code
  if tree.type == TreeType.PushBool:
    val = "true" if tree.nodes[0] == "True" else "false"
    code += f"    {stack} = append({stack}, {val})\n"
    return code
  if tree.type == TreeType.PushChar:
    code += f"    {stack} = append({stack}, '{tree.nodes[0]}')\n"
    return code
  if tree.type == TreeType.PushList:
    a = new_list()
    code += f"    {a} := []interface{{}}{{}}\n"
    code = compile(code, tree.nodes[0], a)
    code += f"    {stack} = append({stack}, {a})\n"
  if tree.type == TreeType.PushQuote:
    a = new_quote()
    code += f"    {a} := func({stack} []interface{{}}) []interface{{}} {{\n"
    code = compile(code, tree.nodes[0], stack)
    code += f"    return {stack}\n"
    code += "    }\n"
    code += f"    {stack} = append({stack}, ({a}))\n"
    return code
  if tree.type == TreeType.PrintType:
    return code
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      code = compile(code, node, stack)
    return code
  if tree.type == TreeType.Noop:
    return code
  name = tree.type.name
  code += f"    {stack} = {name}({stack})\n"
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
  code += "    stack := []interface{}{}\n"
  code = compile(code, tree)
  code += "    writer.Flush()\n"
  code += "}\n"
  return code

with open("main.stk") as f:
  text = f.read()

with open("main.go", "w") as f:
  f.write(compile_source_code("main.stk", text))
