package main
func main() {
    stack := []interface{}{}
    stack = append(stack, 1)
    quote_0 := func(stack []interface{}) []interface{} {
    stack = Dup(stack)
    stack = append(stack, 1000000)
    stack = Lt(stack)
    return stack
    }
    stack = append(stack, (quote_0))
    quote_1 := func(stack []interface{}) []interface{} {
    stack = Dup(stack)
    stack = Print(stack)
    stack = append(stack, 1)
    stack = Add(stack)
    return stack
    }
    stack = append(stack, (quote_1))
    stack = While(stack)
    stack = Print(stack)
    writer.Flush()
}
