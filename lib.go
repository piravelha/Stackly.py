package main

import "fmt"

type Stack struct {
  Elements []interface{}
}

func (s *Stack) Push(elem interface{}) {
  s.Elements = append(s.Elements, elem)
}

func (s *Stack) Pop() interface{} {
  popped := s.Elements[len(s.Elements)-1]
  s.Elements = s.Elements[:len(s.Elements)-1]
  return popped
}

func (s *Stack) Add() {
  b := s.Pop()
  a := s.Pop()
  s.Push(a.(int) + b.(int))
}

func (s *Stack) Sub() {
  b := s.Pop()
  a := s.Pop()
  s.Push(a.(int) - b.(int))
}

func (s *Stack) Print() {
  a := s.Pop()
  fmt.Println(a)
}

func (s *Stack) Cons() {
  b := s.Pop()
  a := s.Pop()
  s.Push(append([]interface{}{a}, b.(Stack).Elements...))
}

func (s *Stack) Eval() {
  a := s.Pop()
  a.(func(*Stack))(s)
}

func (s *Stack) Dup() {
  a := s.Pop()
  s.Push(a)
  s.Push(a)
}

func (s *Stack) If() {
  c := s.Pop()
  b := s.Pop()
  a := s.Pop()
  if a.(bool) {
    s.Push(b)
  } else {
    s.Push(c)
  }
  s.Eval()
}

func (s *Stack) While() {
  b := s.Pop()
  a := s.Pop()
  for {
    s.Push(a)
    s.Eval()
    c := s.Pop()
    if !c.(bool) {
      break
    }
    s.Push(b)
    s.Eval()
  }
}

func (s *Stack) Eq() {
  b := s.Pop()
  a := s.Pop()
  s.Push(a == b)
}

func (s *Stack) Lt() {
  b := s.Pop()
  a := s.Pop()
  s.Push(a.(int) < b.(int))
}
