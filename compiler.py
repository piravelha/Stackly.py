from parser import parse_expr, Tree, TreeType
from lexer import lex
from typechecker import typecheck

var_counter = 0
def new_quote():
  global var_counter
  result = var_counter
  var_counter += 1
  return f"quote_{result}"

def compile(code, tree: Tree):
  if tree.type == TreeType.PushInt:
    code += f"    push_int(stack, {tree.nodes[0]});\n"
    return code
  if tree.type == TreeType.PushBool:
    val = 1 if tree.nodes[0] == "True" else 0
    code += f"    push_bool(stack, {val});\n"
    return code
  if tree.type == TreeType.PushChar:
    code += f"    push_char(stack, '{tree.nodes[0]}');\n"
    return code
  if tree.type == TreeType.PushQuote:
    code = code.split("// start\n")
    a = new_quote()
    func = "// start\n"
    func += f"void {a}(Stack *stack) {{\n"
    func = compile(func, tree.nodes[0])
    func += "}\n"
    code.insert(1, func)
    code = "".join(code)
    code += f"push_quote(stack, &{a});\n"
    return code
  if tree.type == TreeType.Add:
    code += "    add_operation(stack);\n"
    return code
  if tree.type == TreeType.Print:
    code += "    print_operation(stack);\n"
    return code
  if tree.type == TreeType.Eval:
    code += "    eval_operation(stack);\n"
    return code
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      code = compile(code, node)
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
  code = "#include \"lib.h\"\n"
  code += "// start\n\n"
  code += "int main() {\n"
  code += "    Stack _stack;\n"
  code += "    Stack *stack = &_stack;\n"
  code += "    init_stack(stack);\n"
  code = compile(code, tree)
  code += "    return 0;\n"
  code += "}\n"
  return code

with open("main.stk") as f:
  text = f.read()

with open("out.c", "w") as f:
  f.write(compile_source_code("main.stk", text))
