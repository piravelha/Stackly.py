package main
func main() {
    stack := Stack{[]interface{}{}}
    stack.Push(1)
    quote_0 := func(stack *Stack) {
    stack.Dup()
    stack.Push(1000000)
    stack.Lt()
    }
    stack.Push(quote_0)
    quote_1 := func(stack *Stack) {
    stack.Dup()
    stack.Print()
    stack.Push(1)
    stack.Add()
    }
    stack.Push(quote_1)
    stack.While()
    stack.Print()
}
