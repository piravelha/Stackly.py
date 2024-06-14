from enum import Enum, auto
from dataclasses import dataclass
from typing import Union
from parser import parse_expr, Tree, TreeType
from lexer import lex, Token, TokenType, Location

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

def unify_effects(
    a: Effect,
    b: Effect,
    env = {},
    ) -> Union[Effect, None]:
  pops = []
  a_pops = a.pops
  for i, b_ in enumerate(b.pops):
    if b_.type == Kind.Multi:
      b_len = len(b.pops) - 1
      env[b_.effect] = a_pops[:len(a_pops)-b_len]
      pops.extend(a_pops[:len(a_pops)-b_len])
      a_pops = a_pops[len(env[b_.effect]):]
      continue
    if not a_pops:
      return None, env
    a_ = a_pops[0]
    c, env = unify(a_, b_, env)
    if not c:
      return None, env
    pops.append(c)
    a_pops = a_pops[1:]
  pushes = []
  a_pushes = a.pushes
  for i, b_ in enumerate(b.pushes):
    if b_.type == Kind.Multi:
      b_len = len(b.pushes) - 1
      env[b_.effect] = a_pushes[:len(a_pushes)-b_len]
      pushes.extend(a_pushes[:len(a_pushes)-b_len])
      a_pushes = a_pushes[len(env[b_.effect]):]
      continue
    if not a_pushes:
      return None, env
    a_ = a_pushes[0]
    c, env = unify(a_, b_, env)
    if not c:
      return None, env
    pushes.append(c)
    a_pushes = a_pushes[1:]
  return Effect(pops, pushes), env


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
    
def sequence_effects(
    es: list[Effect],
    ) -> Effect:
  A = []
  B = []
  env = {}
  for i, e in enumerate(es):
    if i > 0:
      prev = es[i-1].pushes
      _, env = unify_effects(Effect(prev, []), Effect(e.pops, []), env)
    for pop in e.pops:
      if B:
        c, env = unify(B[-1], pop, env)
        if c:
          B.pop()
          continue
      app = apply_env(pop, env)
      if isinstance(app, list):
        for a in app:
          if B:
            c, env = unify(B[-1], a, env)
            if c:
              B.pop()
              continue
          A.append(a)
      else:
        A.append(app)
    for push in e.pushes:
      app = apply_env(push, env)
      if isinstance(app, list):
        B.extend(app)
      else:
        B.append(app)
  return Effect(A, B)

def assert_enough_args(tree, expected, got):
  if got < expected:
    print(f"{tree.location} TYPE ERROR: Not enough arguments on the stack for the '{tree.type.name}' operator, expected at least {expected}, got {got}")
    exit(1)

def assert_type(tree, pos, expected, got):
  if not unify(got, expected)[0]:
    print(f"{tree.location} TYPE ERROR: Invalid type for the {pos} argument of the '{tree}' operator, expected '{expected}', got '{got}'")
    exit(1)

def effect_of(tree, pops=[], pushes=[]):
  if tree.type == TreeType.Noop:
    return Effect(pops, pushes)
  if tree.type == TreeType.TypeCast:
    return effect_of(tree.nodes[1])
  if tree.type == TreeType.PushInt:
    effect = Effect(
      [],
      [int_type(tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.PushBool:
    effect = Effect(
      [],
      [bool_type(tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.PushChar:
    effect = Effect(
      [],
      [char_type(tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.PushList:
    elem = new_var(tree.location)
    lstack = typecheck(tree.nodes[0])
    for t in lstack:
      c, _ = unify(t, elem)
      if not c:
        print(f"{t.location} TYPE ERROR: Attempting to create a list of different types")
        exit(1)
      elem = c
    effect = Effect(
      [],
      [list_type(elem, tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type in [TreeType.Add, TreeType.Sub]:
    effect = Effect(
      [int_type(tree.location), int_type(tree.location)],
      [int_type(tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Cons:
    a = new_var(tree.location)
    effect = Effect(
      [a, list_type(a, tree.location)],
      [list_type(a, tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Eq:
    a = new_var(tree.location)
    effect = Effect(
      [a, a],
      [bool_type(tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Print:
    a = new_var(tree.location)
    effect = Effect(
      [a],
      [],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.PushQuote:
    effect = Effect(
      [],
      [quote_type(effect_of(tree.nodes[0]), tree.location)],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Eval:
    a = new_multi(tree.location)
    b = new_multi(tree.location)
    effect = Effect(
      [
        a,
        quote_type(Effect(
          [a],
          [b],
        ), tree.location),
      ],
      [b],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.If:
    a = new_multi(tree.location)
    b = new_multi(tree.location)
    q = quote_type(Effect([a], [b]), tree.location)
    effect = Effect(
      [a, bool_type(tree.location), q, q],
      [b],
    )
    print(pops, pushes)
    print(effect)
    print(sequence_effects([Effect(pops, pushes), effect]))
    print("-"*55)
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      effect = effect_of(node, pops, pushes)
      pops = effect.pops
      pushes = effect.pushes
    return Effect(pops, pushes)
  assert False

def eval_quote(stack, quote):
  env = {}
  u, env = unify_effects(Effect(stack, []), Effect(quote.effect.pops, []))
  print(quote)
  print(env)
  print("-"*50)

  if not u:
    print(f"{quote.location} TYPE ERROR: Unification of types failed during evaluation of quote, expected stack to be '{quote.effect.pops}', but was '{stack}'")
    exit(1)
  u = [apply_env(v, env) for v in u.pops]
  for i, pop in enumerate(u):
    s = stack.pop()
    c, env = unify(pop, s, env)
    if not c:
      print(f"{s.location} TYPE ERROR: Unification of types failed during evaluation of quote, expected argument #{i} of the stack to be '{pop}', but was '{s}'")
      exit(1)
  for push in quote.effect.pushes:
    app = apply_env(push, env)
    if isinstance(app, list):
      stack.extend(app)
    else:
      stack.append(app)
  return stack
  
def compare_quotes(tree, stack, quotes, offset=0, self=False):
  if self:
    quote = quotes
    new = typecheck(quote.effect, stack.copy())
    [new.pop() for _ in range(offset)]
    for a, b in zip(stack, new):
      u, env = unify(a, b)
      if not u:
        print(f"{b.location} TYPE ERROR: Invalid type when evaluating quotes: expected '{a}', got '{b}'")
        exit(1)
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
      exit(1)
    for a, b in zip(first, result):
      u, env = unify(a, b)
      if not u:
        print(f"{b.location} TYPE ERROR: Invalid type when evaluating quotes: expected '{a}', got '{b}'")
        exit(1)

def typecheck(tree, stack=[]):
  if tree.type == TreeType.Noop:
    return stack
    c, _ = unify(tree)
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
        exit(1)
      elem = c
    stack.append(list_type(elem, tree.location))
    return stack
  if tree.type in [TreeType.Add, TreeType.Sub]:
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
  if tree.type == TreeType.Lt:
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
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      stack = typecheck(node, stack)
    return stack
  print(tree)
  assert False

