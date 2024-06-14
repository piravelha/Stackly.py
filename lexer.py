from dataclasses import dataclass
from enum import Enum, auto
import re

class TokenType(Enum):
  Int = auto()
  Char = auto()
  Word = auto()
  OpenQuote = auto()
  CloseQuote = auto()
  OpenBracket = auto()
  CloseBracket = auto()

@dataclass
class Location:
  file: str
  line: int
  col: int
  def __repr__(self):
    return f"{self.file}:{self.line}:{self.col}:"

@dataclass
class Token:
  type: TokenType
  value: str
  location: Location
  def __repr__(self):
    return f"[{self.type.name}:'{self.value}']"

def lex(file: str, code: str) -> list[Token]:
  tokens = []
  int_p = r"^(\d+)"
  line = 1
  col = 1
  while code:
    if ws := re.findall(r"^([ \t]+)", code):
      col += len(ws[0])
      code = code[len(ws[0]):]
      continue
    if re.findall(r"^(\n)", code):
      col = 1
      line += 1
      code = code[1:]
      continue
    loc = Location(file, line, col)
    if n := re.findall(int_p, code):
      col += len(n[0])
      code = code[len(n[0]):]
      tokens.append(Token(TokenType.Int, n[0], loc))
      continue
    if c := re.findall(r"^'([^'])'", code):
      col += len(c[0]) + 2
      code = code[len(c[0])+2:]
      tokens.append(Token(TokenType.Char, c[0], loc))
      continue
    if w := re.findall(r"^([^\s\d{}\[\]]+)", code):
      col += len(w[0])
      code = code[len(w[0]):]
      tokens.append(Token(TokenType.Word, w[0], loc))
      continue
    if re.findall(r"^(\{)", code):
      col += 1
      code = code[1:]
      tokens.append(Token(TokenType.OpenQuote, "{", loc))
      continue
    if re.findall(r"^(\})", code):
      col += 1
      code = code[1:]
      tokens.append(Token(TokenType.CloseQuote, "}", loc))
      continue
    if re.findall(r"^(\[)", code):
      col += 1
      code = code[1:]
      tokens.append(Token(TokenType.OpenBracket, "[", loc))
      continue
    if re.findall(r"^(\])", code):
      col += 1
      code = code[1:]
      tokens.append(Token(TokenType.CloseBracket, "]", loc))
      continue
  
  return tokens

