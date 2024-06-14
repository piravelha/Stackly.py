#ifndef LIB_H
#define LIB_H

#include <stddef.h>

#define STACK_CAPACITY 100

typedef struct Stack Stack;

typedef enum {
  TYPE_INT,
  TYPE_BOOL,
  TYPE_CHAR,
  TYPE_LIST,
  TYPE_QUOTE
} DataType;


typedef struct {
  DataType type;
  union {
    int int_value;
    int bool_value;
    char char_value;
    Stack *list_value;
    void (*quote_value)(Stack *);
  };
} Data;

struct Stack {
  int top;
  Data *elements;
};

void init_stack(Stack *stack);
void push(Stack *stack, Data elem);
Data pop(Stack *stack);
void free_stack(Stack *stack);
void push_int(Stack *stack, int elem);
void push_bool(Stack *stack, int elem);
void push_char(Stack *stack, char elem);
void push_list(Stack *stack, Stack *elem);
void push_quote(Stack *stack, void (*elem)(Stack *));
void add_operation(Stack *stack);
void cons_operation(Stack *stack);
void print_operation(Stack *stack);
void eval_operation(Stack *stack);

#endif // LIB_H
