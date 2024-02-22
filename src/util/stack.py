
class Stack(object):
    def __init__(self, limit=1000):
        self.stack = []  # Store elements
        self.limit = limit  # Stack capacity limit
 
    def push(self, data):
        # Determine whether the stack capacity exceeds the range
        if len(self.stack) >= self.limit:
            raise IndexError('Stack capacity limit exceeded')
        self.stack.append(data)
 
    def pop(self):
        if self.stack:
            return self.stack.pop()
        else:
            # Elements cannot be popped from an empty stack
            raise IndexError('pop from an empty stack')
 
    def peek(self):  # View the top element of the stack
        if self.stack:
            return self.stack[-1]
 
    def is_empty(self):  # Determine whether the stack is empty
        return not bool(self.stack)
 
    def size(self):  # Return stack size
        return len(self.stack)