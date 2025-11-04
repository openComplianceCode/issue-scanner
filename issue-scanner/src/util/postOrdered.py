import logging
import re
import sys
from util.stack import Stack

operator = {
    'or': 3,
    'and': 3,
    'with': ValueError ,
    '(': ValueError,
    ')':ValueError,
}
priority = {}
x=2147483647
for i in list(operator):
    x-=1
    priority[i]=x

def infixToPostfix(infixexpr):
    operation_stack = Stack()
    postfix_list = []
    token_list = []

    try:
        license_set = re.split(r'\(|\)|\s+\,|\s+[Aa][Nn][Dd]\s+|\s+-?[Oo][Rr]-?\s+|\s+/\s+|\s+[Ww][Ii][Tt][Hh]\s+', infixexpr)
        posfix_set = re.findall(r'\(|\)|\s+\,|\s+[Aa][Nn][Dd]\s+|\s+-?[Oo][Rr]-?\s+|\s+/\s+|\s+[Ww][Ii][Tt][Hh]\s+', infixexpr)

        if len(posfix_set) == 0:
            for i in range(len(license_set)):
                license_set[i] = license_set[i].strip()
            return license_set

        for i,var in enumerate(posfix_set):
            token_list.append(license_set[i])
            token_list.append(posfix_set[i])
        
        token_list.append(license_set[len(license_set) - 1])

        for index in range(len(token_list)): 
            if ' -or' in token_list[index].lower() or 'or- ' in token_list[index].lower():
                token_list[index] = 'or'
            token_list[index] = token_list[index].strip()

        token_list = list(filter(None, token_list))
    
        for token in token_list:
            
            # Push left bracket onto stack
            if token == '(':
                operation_stack.push(token)
            # If the marker is a closing parenthesis, repeatedly remove elements from the operation_stack stack,
            # until the corresponding left bracket is removed
            elif token == ')':
                top_token = operation_stack.pop()
                while top_token != '(':
                    # Each operator taken from the stack is added to the end of the result list
                    postfix_list.append(top_token)
                    top_token = operation_stack.pop()
            # Operands are added to the end of the list
            elif token.lower() in ['and', 'or', 'with']:
                while (not operation_stack.is_empty()) and (priority[operation_stack.peek().lower()] >= priority[token.lower()]):
                    postfix_list.append(operation_stack.pop())
                operation_stack.push(token)
            else:
                postfix_list.append(token)
    
        while not operation_stack.is_empty():
            postfix_list.append(operation_stack.pop())
    except Exception as e:      
        logger = logging.getLogger(__name__)
        logger.exception("licenses to Postfix is error: %s", str(e))
        postfix_list = []
        postfix_list.append(infixexpr)
 
    return postfix_list

    