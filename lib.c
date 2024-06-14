#include <stdio.h>
#include <stdlib.h>
#include "lib.h"

void init_stack(Stack *stack) {
  stack->top = 0;
  stack->elements = malloc(STACK_CAPACITY * sizeof(Data));
}

void push(Stack *stack, Data elem) {
  if (stack->top >= STACK_CAPACITY) {
    printf("Stack overflow\n");
    exit(1);
  }
  stack->elements[stack->top++] = elem;
}

Data pop(Stack *stack) {
  if (stack->top <= 0) {
    printf("Stack underflow\n");
    exit(1);
  }
  return stack->elements[--stack->top];
}

void push_int(Stack *stack, int value) {
  Data data;
  data.type = TYPE_INT;
  data.int_value = value;
  push(stack, data);
}

void push_bool(Stack *stack, int value) {
  Data data;
  data.type = TYPE_BOOL;
  data.bool_value = value;
  push(stack, data);
}

void push_char(Stack *stack, char value) {
  Data data;
  data.type = TYPE_CHAR;
  data.char_value = value;
  push(stack, data);
}

void push_quote(Stack *stack, void (*value)(Stack *)) {
  Data data;
  data.type = TYPE_QUOTE;
  data.quote_value = value;
  push(stack, data);
}

void add_operation(Stack *stack) {
  Data b = pop(stack);
  Data a = pop(stack);
  push_int(stack, a.int_value + b.int_value);
}

void print_operation(Stack *stack) {
  Data a = pop(stack);
  if (a.type == TYPE_INT) {
    printf("%d\n", a.int_value);
  } else if (a.type == TYPE_BOOL) {
    if (a.bool_value) {
      printf("True\n");
    } else {
      printf("False\n");
    }
  } else if (a.type == TYPE_CHAR) {
    printf("%c\n", a.char_value);
  }
}

void eval_operation(Stack *stack) {
  Data a = pop(stack);
  a.quote_value(stack);
}
