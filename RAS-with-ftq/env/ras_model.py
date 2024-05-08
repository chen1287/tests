from mlvp.utils import PLRU, TwoBitsCounter
from mlvp import *
from .ftb import *

# 模拟stack
class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        else:
            raise IndexError("pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        else:
            raise IndexError("peek from empty stack")

    def size(self):
        return len(self.items)


class RASWay:
    def __init__(self):
        self.retAddr = 0x00000000   # 返回地址
        self.ctr = 0    # 函数调用嵌套层数
        
        # self.spec_push_valid = 0    # 进行push操作时的valid
        # self.spec_pop_valid = 0     # 进行pop操作时的valid
        # self.spec_push_addr = 0x00000000    # 进行push操作时的地址
        # self.spec_pop_addr = 0x00000000     # 进行pop操作时的地址
