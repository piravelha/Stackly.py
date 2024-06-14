from enum import Enum, auto
from dataclasses import dataclass
from typing import Union
from parsing import TreeType
from lexer import Location

SHOULD_EXIT = True

@dataclass
class Effect:
  pops: 'list[Type]'
  pushes: 'list[Type]'
  def __repr__(self):
    return f"{str(self.pops)} => {str(self.pushes)}"

class Kind(Enum):
  Int = auto()
  Bool = auto()
  Char = auto()
  Quote = auto()
  List = auto()
  Var = auto()
  Multi = auto()

def pretty_var(var):
  return "abcdefghijklmnopqrstuvwxyz"[int(var[1:])] if int(var[1:]) < 26 else var

@dataclass
class Type:
  type: Kind
  effect: Union[
    Effect,
    str,
    None,
  ]
  location: Location
  def __repr__(self):
    if self.type == Kind.List:
      return f"{self.effect} {self.type.name}"
    if self.type == Kind.Quote:
      return f"{{{self.effect}}}"
    if self.type == Kind.Var:
      return pretty_var(self.effect)
    if self.type == Kind.Multi:
      return f"..{pretty_var(self.effect)}"
    return self.type.name

def int_type(loc) -> Type:
  return Type(
    Kind.Int,
    None,
    loc,
  )

def bool_type(loc) -> Type:
  return Type(
    Kind.Bool,
    None,
    loc,
  )

def char_type(loc) -> Type:
  return Type(
    Kind.Char,
    None,
    loc,
  )

def list_type(elem, loc) -> Type:
  return Type(
    Kind.List,
    elem,
    loc,
  )

def quote_type(tree, loc) -> Type:
  return Type(
    Kind.Quote,
    tree,
    loc,
  )

var_count = -1

def new_var(loc) -> Type:
  global var_count
  var_count += 1
  return Type(
    Kind.Var,
    f"v{var_count}",
    loc,
  )

def new_multi(loc) -> Type:
  global var_count
  var_count += 1
  return Type(
    Kind.Multi,
    f"m{var_count}",
    loc,
  )

def unify(
    a: Type,
    b: Type,
    env = {},
    ) -> Union[Type, None]:
  if b.type == Kind.Var:
    env[b.effect] = a
    return a, env
  if a.type != b.type:
    return None, env
  if a.type == Kind.List:
    a_elem = a.effect
    b_elem = b.effect
    c, env = unify(a_elem, b_elem, env)
    if not c:
      return None, env
    return Type(Kind.List, c, a.location), env
  if a.type == Kind.Quote:
    return a, env
  return a, env

def apply_env(type, env):
  global SHOULD_EXIT
  if type.type == Kind.Quote:
    pops = []
    for p in type.effect.pops:
      app = apply_env(p, env)
      if isinstance(app, list):
        pops.extend(app)
      else:
        pops.append(app)
    pushes = []
    for p in type.effect.pushes:
      app = apply_env(p, env)
      if isinstance(app, list):
        pushes.extend(app)
      else:
        pushes.append(app)
    return Type(Kind.Quote, Effect(pops, pushes), type.location)
  if type.type == Kind.Var:
    if env.get(type.effect) != None:
      return env[type.effect]
  if type.type == Kind.Multi:
    if env.get(type.effect) != None:
      return env[type.effect]
  return type

def assert_enough_args(tree, expected, got):
  global SHOULD_EXIT
  if got < expected:
    print(f"{tree.location} TYPE ERROR: Not enough arguments on the stack for the '{tree.type.name}' operator, expected at least {expected}, got {got}")
    if SHOULD_EXIT: exit(1)
    else: raise TypeError()

def assert_type(tree, pos, expected, got):
  global SHOULD_EXIT
  if not unify(got, expected)[0]:
    print(f"{tree.location} TYPE ERROR: Invalid type for the {pos} argument of the '{tree}' operator, expected '{expected}', got '{got}'")
    if SHOULD_EXIT: exit(1)
    else: raise TypeError()
  
def compare_quotes(tree, stack, quotes, offset=0, self=False):
  global SHOULD_EXIT
  if self:
    quote = quotes
    new = typecheck(quote.effect, stack.copy())
    [new.pop() for _ in range(offset)]
    for a, b in zip(stack, new):
      u, _ = unify(a, b)
      if not u:
        print(f"{b.location} TYPE ERROR: Invalid type when evaluating quotes: expected '{a}', got '{b}'")
        if SHOULD_EXIT: exit(1)
        else: raise TypeError()
    return
  results = []
  for quote in quotes:
    qstack = stack.copy()
    results.append(typecheck(quote.effect, qstack))
  first = results[0]
  for r in results:
    [r.pop() for _ in range(offset)]
  for result in results:
    if len(result) != len(first):
      qs = "".join(["  " + str(q) + "\n" for q in quotes])
      print(f"{tree.location} TYPE ERROR: The quotes passed into '{tree}' are not congruent in shape: [\n{qs}]")
      if SHOULD_EXIT: exit(1)
      else: raise TypeError()
    for a, b in zip(first, result):
      u, _ = unify(a, b)
      if not u:
        print(f"{b.location} TYPE ERROR: Invalid type when evaluating quotes: expected '{a}', got '{b}'")
        if SHOULD_EXIT: exit(1)
        else: raise TypeError()

def typecheck(tree, stack=[], should_exit=True):
  global SHOULD_EXIT
  if not should_exit:
    SHOULD_EXIT = False
  if tree.type == TreeType.Noop:
    return stack
  if tree.type == TreeType.PushInt:
    stack.append(int_type(tree.location))
    return stack
  if tree.type == TreeType.PushBool:
    stack.append(bool_type(tree.location))
    return stack
  if tree.type == TreeType.PushChar:
    stack.append(char_type(tree.location))
    return stack
  if tree.type == TreeType.PushList:
    lstack = typecheck(tree.nodes[0], [])
    elem = new_var(tree.location)
    for t in lstack:
      c, _ = unify(t, elem)
      if not c:
        print(f"{t.location} TYPE ERROR: Attempting to create a list with different types")
        if SHOULD_EXIT: exit(1)
        else: raise TypeError()
      elem = c
    stack.append(list_type(elem, tree.location))
    return stack
  if tree.type in [TreeType.Add, TreeType.Sub, TreeType.Mul, TreeType.Div]:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "first", int_type(tree.location), a)
    assert_type(tree, "second", int_type(tree.location), b)
    stack.append(int_type(tree.location))
    return stack
  if tree.type == TreeType.Cons:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "first", b, list_type(a, tree.location))
    stack.append(b)
    return stack
  if tree.type in [TreeType.Lt, TreeType.Gt, TreeType.Lte, TreeType.Gte]:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "first", int_type(tree.location), a)
    assert_type(tree, "second", int_type(tree.location), b)
    stack.append(bool_type(tree.location))
    return stack
  if tree.type == TreeType.Eq:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "second", a, b)
    stack.append(bool_type(tree.location))
    return stack
  if tree.type == TreeType.Not:
    assert_enough_args(tree, 1, len(stack))
    a = stack.pop()
    assert_type(tree, "first", bool_type(tree.location), a)
    stack.append(bool_type(tree.location))
    return stack
  if tree.type == TreeType.Print:
    assert_enough_args(tree, 1, len(stack))
    stack.pop()
    return stack
  if tree.type == TreeType.Dup:
    a = stack.pop()
    stack.append(a)
    stack.append(a)
    return stack
  if tree.type == TreeType.If:
    assert_enough_args(tree, 3, len(stack))
    c = stack.pop()
    b = stack.pop()
    a = stack.pop()
    e = Effect([new_multi(tree.location)], [new_multi(tree.location)])
    assert_type(tree, "first", bool_type(tree.location), a)
    assert_type(tree, "second", quote_type(e, tree.location), b)
    assert_type(tree, "third", b, c)
    compare_quotes(tree, stack, [b, c])
    stack = typecheck(b.effect, stack)
    return stack
  if tree.type == TreeType.While:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "first", quote_type(None, tree.location), a)
    assert_type(tree, "second", quote_type(None, tree.location), b)
    compare_quotes(tree, stack, b, self=True)
    compare_quotes(tree, stack, a, offset=1, self=True)
    return stack
  if tree.type == TreeType.PushQuote:
    stack.append(Type(Kind.Quote, tree.nodes[0], tree.location))
    return stack
  if tree.type == TreeType.Eval:
    assert_enough_args(tree, 1, len(stack))
    quote = stack.pop()
    assert_type(tree, "first", quote_type(tree, tree.location), quote)
    stack = typecheck(quote.effect, stack)
    return stack
  if tree.type == TreeType.PrintType:
    assert_enough_args(tree, 1, len(stack))
    type = stack.pop()
    print(f"(type?) {tree.location} {type}")
    stack.append(type)
    return stack
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      stack = typecheck(node, stack)
    return stack
  print(tree)
  assert False

