package main

import (
	"bufio"
	"fmt"
	"os"
)

var writer = bufio.NewWriter(os.Stdout)
var print_counter = 0

func Add(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	return append(s[:len(s)-2], a.(int)+b.(int))
}

func Sub(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	return append(s[:len(s)-2], a.(int)-b.(int))
}

func Mul(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	return append(s[:len(s)-2], a.(int)*b.(int))
}

func Div(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	return append(s[:len(s)-2], a.(int)/b.(int))
}

func Print(s []interface{}) []interface{} {
	a := s[len(s)-1]
	fmt.Fprintf(writer, "%v\n", a)
	print_counter += 1
	if print_counter > 100000 {
		writer.Flush()
		print_counter = 0
	}
	return s[:len(s)-1]
}

func Cons(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	return append(s[:len(s)-2], append([]interface{}{b}, a.([]interface{})...))
}

func Eval(s []interface{}) []interface{} {
	a := s[len(s)-1]
	s = a.(func([]interface{}) []interface{})(s[:len(s)-1])
	return s
}

func Dup(s []interface{}) []interface{} {
	a := s[len(s)-1]
	s = s[:len(s)-1]
	s = append(s, a, a)
	return s
}

func If(s []interface{}) []interface{} {
	c := s[len(s)-1]
	b := s[len(s)-2]
	a := s[len(s)-3]
	s = s[:len(s)-3]
	if a.(bool) {
		s = append(s, b)
	} else {
		s = append(s, c)
	}
	s = Eval(s)
	return s
}

func While(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	for {
		s = append(s, a)
		s = Eval(s)
		c := s[len(s)-1]
		s = s[:len(s)-1]
		if !c.(bool) {
			break
		}
		s = append(s, b)
		s = Eval(s)
	}
	return s
}

func Lt(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	s = append(s, a.(int) < b.(int))
	return s
}

func Gt(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	s = append(s, a.(int) > b.(int))
	return s
}

func Lte(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	s = append(s, a.(int) <= b.(int))
	return s
}

func Gte(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	s = append(s, a.(int) >= b.(int))
	return s
}

func Eq(s []interface{}) []interface{} {
	b := s[len(s)-1]
	a := s[len(s)-2]
	s = s[:len(s)-2]
	s = append(s, a.(int) == b.(int))
	return s
}

func Not(s []interface{}) []interface{} {
	a := s[len(s)-1]
	s = s[:len(s)-1]
	s = append(s, !a.(bool))
	return s
}
