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
  Var = auto()
  Multi = auto()

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
    if self.type == Kind.Quote:
      return f"{{{self.effect}}}"
    if self.type == Kind.Var:
      return self.effect
    if self.type == Kind.Multi:
      return f"..{self.effect}"
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

def quote_type(eff: Effect, loc) -> Type:
  return Type(
    Kind.Quote,
    eff,
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
      break
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
      break
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
  if a.type == Kind.Quote:
    a_eff = a.effect
    b_eff = b.effect
    eff, env = unify_effects(
      a_eff,
      b_eff,
      env,
    )
    return Type(a.type, eff, a.location), env
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
  if tree.type == TreeType.Add:
    effect = Effect(
      [int_type(tree.location), int_type(tree.location)],
      [int_type(tree.location)],
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
        quote_type(Effect(
          [a],
          [b],
        ), tree.location),
        a,
      ],
      [b],
    )
    return sequence_effects([Effect(pops, pushes), effect])
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      effect = effect_of(node, pops, pushes)
      pops = effect.pops
      pushes = effect.pushes
    return Effect(pops, pushes)
  assert False

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
  if tree.type == TreeType.Add:
    assert_enough_args(tree, 2, len(stack))
    b = stack.pop()
    a = stack.pop()
    assert_type(tree, "first", int_type(tree.location), a)
    assert_type(tree, "second", int_type(tree.location), b)
    stack.append(int_type(tree.location))
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
  if tree.type == TreeType.PushQuote:
    effect = effect_of(tree.nodes[0])
    stack.append(Type(Kind.Quote, effect, tree.location))
    return stack
  if tree.type == TreeType.Eval:
    assert_enough_args(tree, 1, len(stack))
    quote = stack.pop()
    assert_type(tree, "first", quote, quote_type(Effect([new_multi(tree.location)], [new_multi(tree.location)]), tree.location))
    env = {}
    u, env = unify_effects(Effect(stack, []), Effect(quote.effect.pops, []))
    u = [apply_env(v, env) for v in u.pops]
    for pop in u:
      s = stack.pop()
      c, env = unify(pop, s, env)
      if not c:
        assert False
    for push in quote.effect.pushes:
      app = apply_env(push, env)
      if isinstance(app, list):
        stack.extend(app)
      else:
        stack.append(app)
    return stack
  if tree.type == TreeType.Expr:
    for node in tree.nodes:
      stack = typecheck(node, stack)
    return stack
  assert False
