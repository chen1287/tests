from mlvp.utils import PLRU, TwoBitsCounter
from mlvp import *
from .ftb import *

vAddrBits = 64
rasSize = 16

# 普通栈模拟提交栈
class ComStack:
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

# 链式栈模拟预测栈
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class PreStack:
    def __init__(self):
        self.top = None

    def is_empty(self):
        return self.top is None

    def push(self, data):
        new_node = Node(data)
        new_node.next = self.top
        self.top = new_node

    def pop(self):
        if not self.is_empty():
            data = self.top.data
            self.top = self.top.next
            return data
        else:
            raise IndexError("pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.top.data
        else:
            raise IndexError("peek from empty stack")

    def size(self):
        count = 0
        current = self.top
        while current is not None:
            count += 1
            current = current.next
        return count


class RASModel:
    def __init__(self, rasSize, vAddrBits, spec_new_addr, push_valid, pop_valid, recover_sp, recover_top, recover_valid, recover_push, recover_pop, recover_new_addr):
        # 初始化栈指针寄存器
        self.sp = 0
        
        # 初始化栈顶条目寄存器
        self.top = RASEntry(0, 0)
        
        # 输入信号
        self.spec_new_addr = spec_new_addr
        self.push_valid = push_valid
        self.pop_valid = pop_valid
        self.recover_sp = recover_sp
        self.recover_top = recover_top
        self.recover_valid = recover_valid
        self.recover_push = recover_push
        self.recover_pop = recover_pop
        self.recover_new_addr = recover_new_addr
        
        # 根据 rasSize 初始化栈内存
        self.stack = [RASEntry(0, 0) for _ in range(rasSize)]
        
        # 调试接口初始化
        self.debugIO = DebugIO()


# 辅助类，用于模拟 RASEntry 结构
class RASEntry:
    def __init__(self, retAddr, ctr):
        self.retAddr = retAddr
        self.ctr = ctr

# 辅助类，用于模拟 DebugIO 结构
class DebugIO:
    def __init__(self):
        self.spec_push_entry = RASEntry(0, 0)
        self.spec_alloc_new = False
        self.recover_push_entry = RASEntry(0, 0)
        self.recover_alloc_new = False
        self.sp = 0
        self.topRegister = RASEntry(0, 0)
        self.out_mem = [RASEntry(0, 0) for _ in range(rasSize)]