import time
from lexer import lex
from parsing import parse_expr, Tree, TreeType
from typechecker import typecheck
from debugger import print_stack
import readline
import os
import atexit

HISTORY_FILE = os.path.expanduser("~/.my_repl_history")

if os.path.exists(HISTORY_FILE):
    readline.read_history_file(HISTORY_FILE)

atexit.register(readline.write_history_file, HISTORY_FILE)

def value_repr(value):
    if isinstance(value, list):
        return "[" + " ".join([str(v) for v in value]) + "]"
    return repr(value)

def shell(tree: Tree, stack, info=[0, 0]):
    info_pop, info_push = info
    if tree.type == TreeType.Noop:
        return stack, info
    if tree.type == TreeType.PushInt:
        stack.append(int(tree.nodes[0]))
        return stack, [info_pop, info_push+1]
    if tree.type == TreeType.PushBool:
        stack.append(tree.nodes[0] == "True")
        return stack, [info_pop, info_push+1]
    if tree.type == TreeType.PushChar:
        stack.append(tree.nodes[0])
        return stack, [info_pop, info_push+1]
    if tree.type == TreeType.PushList:
        list, info = shell(tree.nodes[0], [], info)
        info_pop, info_push = info
        stack.append(list)
        return stack, [info_pop, info_push+1]
    if tree.type == TreeType.PushQuote:
        stack.append(tree.nodes[0])
        return stack, [info_pop, info_push+1]
    if tree.type == TreeType.Eval:
        quote = stack.pop()
        stack, info = shell(quote, stack, info)
        return stack, [info[0]+1, info[1]]
    if tree.type == TreeType.Cons:
        b = stack.pop()
        a = stack.pop()
        stack.append([a] + b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Add:
        b = stack.pop()
        a = stack.pop()
        stack.append(a + b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Sub:
        b = stack.pop()
        a = stack.pop()
        stack.append(a - b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Mul:
        b = stack.pop()
        a = stack.pop()
        stack.append(a * b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Div:
        b = stack.pop()
        a = stack.pop()
        stack.append(a / b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Lt:
        b = stack.pop()
        a = stack.pop()
        stack.append(a < b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Gt:
        b = stack.pop()
        a = stack.pop()
        stack.append(a > b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Lte:
        b = stack.pop()
        a = stack.pop()
        stack.append(a <= b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Gte:
        b = stack.pop()
        a = stack.pop()
        stack.append(a >= b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Eq:
        b = stack.pop()
        a = stack.pop()
        stack.append(a == b)
        return stack, [info_pop+2, info_push+1]
    if tree.type == TreeType.Not:
        a = stack.pop()
        stack.append(not a)
        return stack, [info_pop+1, info_push+1]
    if tree.type == TreeType.Dup:
        a = stack.pop()
        stack.append(a)
        stack.append(a)
        return stack, [info_pop+1, info_push+2]
    if tree.type == TreeType.If:
        c = stack.pop()
        b = stack.pop()
        a = stack.pop()
        if a:
            stack, [info_pop, info_push] = shell(b, stack, info)
        else:
            stack, [info_pop, info_push] = shell(c, stack, info)
        return stack, [info_pop+1, info_push+1]
    if tree.type == TreeType.While:
        b = stack.pop()
        a = stack.pop()
        while True:
            stack, [info_pop, info_push] = shell(a, stack, [info_pop, info_push])
            if not stack.pop():
                info_pop += 1
                break
            stack, [info_pop, info_push] = shell(b, stack, [info_pop, info_push])
        return stack, [info_pop+2, info_push]
    if tree.type == TreeType.Print:
        a = stack.pop()
        print(value_repr(a))
        return stack, [info_pop+1, info_push+0]
    if tree.type == TreeType.Expr:
        for node in tree.nodes:
            stack, info = shell(node, stack, info)
        return stack, info
    assert False, f"Not implemented: {tree.type.name}"

def completer(text, state):
    options = [cmd for cmd in commands if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

commands = ["stack", "quit", "help"]

def print_help():
    print("HELP: Commands: `stack`, `quit`, `help`")
    print("    :stack      Prints an ascii representation of the Stack.")
    print("    :quit       Exits the shell.")
    print("    :help       Opens this menu.")

def run(stack, type_stack):
    text = input("hastack> ")
    if text in [":stack", ":s"]:
        print_stack(stack)
        return stack, type_stack
    if text in [":quit", ":q"]:
        print("Quitting hastack shell")
        exit(0)
    if text in [":help", ":h", "help"]:
        print_help()
        return stack, type_stack
    tokens = lex("<shell>", text)
    tree, _ = parse_expr(tokens)
    try:
        type_stack = typecheck(tree, type_stack, should_exit=False)
        stack, info = shell(tree, stack, [0, 0])
        info_pop, info_push = info
        if type_stack:
            print(f"{value_repr(stack[-1])} : {type_stack[-1]}")
        print(f"Popped {info_pop} elements, pushed {info_push}.")
    except TypeError:
        type_stack = []
        stack = []
    return stack, type_stack

stack = []
type_stack = []
while True:
    stack, type_stack = run(stack, type_stack)