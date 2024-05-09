from mlvp.utils import PLRU, TwoBitsCounter
from mlvp import *
from .ftb import *
import ctypes as ct # C语言类型 

vAddrBits = 64
RasSize = 16
RasSpecSize = 32

# # 普通栈模拟提交栈
# class ComStack:
#     def __init__(self):
#         self.items = []

#     def is_empty(self):
#         return len(self.items) == 0

#     def push(self, item):
#         self.items.append(item)

#     def pop(self):
#         if not self.is_empty():
#             return self.items.pop()
#         else:
#             raise IndexError("pop from empty stack")

#     def peek(self):
#         if not self.is_empty():
#             return self.items[-1]
#         else:
#             raise IndexError("peek from empty stack")

#     def size(self):
#         return len(self.items)

# # 链式栈模拟预测栈
# class Node:
#     def __init__(self, data):
#         self.data = data
#         self.next = None

# class PreStack:
#     def __init__(self):
#         self.top = None

#     def is_empty(self):
#         return self.top is None

#     def push(self, data):
#         new_node = Node(data)
#         new_node.next = self.top
#         self.top = new_node

#     def pop(self):
#         if not self.is_empty():
#             data = self.top.data
#             self.top = self.top.next
#             return data
#         else:
#             raise IndexError("pop from empty stack")

#     def peek(self):
#         if not self.is_empty():
#             return self.top.data
#         else:
#             raise IndexError("peek from empty stack")

#     def size(self):
#         count = 0
#         current = self.top
#         while current is not None:
#             count += 1
#             current = current.next
#         return count


class RASEntry:
    # 返回地址
    retAddr = ct.c_uint64(0)
    # 函数调用嵌套层数
    ctr = ct.c_uint8(0)
    # !=方法，用来比较两个RASEntry对象是否相等
    def __ne__(self, other):
        return self.retAddr != other.retAddr or self.ctr != other.ctr

# RASPtr循环指针队列,用来管理RAS中的条目
class RASPtr:
    def __init__(self, size, value, flag):
        self.size = size
        self.value = value
        self.flag = flag
    # 翻转标志位 
    def inverse(self):
        return RASPtr(self.size, self.value, not self.flag)
    

# RASMeta类,包含了管理RAS所需的元数据，如栈指针（ssp）、计数器（sctr）和三个不同的指针（TOSW、TOSR、NOS）
class RASMeta:
    def __init__(self, ssp, sctr, TOSW, TOSR, NOS):
        self.ssp = ssp
        self.sctr = sctr
        self.TOSW = TOSW
        self.TOSR = TOSR
        self.NOS = NOS

    def __str__(self):
        return (f"RASMeta(ssp={self.ssp}, sctr={self.sctr}, "
                f"TOSW={self.TOSW}, TOSR={self.TOSR}, NOS={self.NOS})")
    
# RASDebug类用于调试目的，它包含了指向RAS条目和指针的向量。
class RASDebug:
    # spec_queue 是一个向量，包含了 RasSpecSize 个 RASEntry 实例
    spec_queue = [RASEntry() for _ in range(RasSpecSize)]
    # spec_nos 是一个向量，包含了 RasSpecSize 个 RASPtr 实例
    spec_nos = [RASPtr(0, 0, False) for _ in range(RasSpecSize)]
    # commit_stack 是一个向量，包含了 RasSize 个 RASEntry 实例
    commit_stack = [RASEntry() for _ in range(RasSize)]

# 实现重放栈的具体逻辑
class RASStack:
    def __init__(self, 
                 spec_push_valid, spec_pop_valid, spec_push_addr, s2_fire,
                 s3_fire, s3_cancel, s3_meta, s3_missed_pop, s3_missed_push,
                 s3_pushAddr, commit_push_valid, commit_pop_valid,
                 commit_push_addr, commit_meta_TOSW, commit_meta_TOSR,
                 redirect_valid, redirect_isCall, redirect_isRet,
                 redirect_meta_ssp, redirect_meta_sctr, redirect_meta_TOSW,
                 redirect_meta_TOSR, redirect_meta_NOS, redirect_callAddr,
                 spec_pop_addr, ssp, sctr, nsp, TOSR, TOSW, NOS, BOS):
        
        # Assigning input variables to class attributes
        self.spec_push_valid = spec_push_valid  # 进行PUSH操作
        self.spec_pop_valid = spec_pop_valid    # 进行POP操作
        self.spec_push_addr = spec_push_addr    # PUSH的地址
        self.s2_fire = s2_fire  # S2信号有效
        self.s3_fire = s3_fire  # S3信号有效
        self.s3_cancel = s3_cancel  # S3的信号表示需要撤销S2的操作
        self.s3_meta = s3_meta  # S3需要S2时的现场信息
        self.s3_missed_pop = s3_missed_pop  # S3判断需要进行再次POP操作
        self.s3_missed_push = s3_missed_push    # S3判断需要进行再次PUSH操作
        self.s3_pushAddr = s3_pushAddr  # S3需要PUSH的地址
        self.commit_push_valid = commit_push_valid  # PUSH操作正确
        self.commit_pop_valid = commit_pop_valid    # POP操作正确
        self.commit_push_addr = commit_push_addr    # PUSH的正确地址
        self.commit_meta_TOSW = commit_meta_TOSW    # 之前预测时候的现场信息TOSW
        self.commit_meta_TOSR = commit_meta_TOSR    # 之前预测时候的现场信息TOSR
        self.redirect_valid = redirect_valid    # 是否发生了重定向
        self.redirect_isCall = redirect_isCall  # 真实情况是Call
        self.redirect_isRet = redirect_isRet    # 真实情况是Return
        self.redirect_meta_ssp = redirect_meta_ssp  # 之前预测时候的现场信息ssp
        self.redirect_meta_sctr = redirect_meta_sctr    # 之前预测时候的现场信息sctr
        self.redirect_meta_TOSW = redirect_meta_TOSW    # 之前预测时候的现场信息TOSW
        self.redirect_meta_TOSR = redirect_meta_TOSR    # 之前预测时候的现场信息TOSR
        self.redirect_meta_NOS = redirect_meta_NOS  # 之前预测时候的现场信息NOS
        self.redirect_callAddr = redirect_callAddr  # 重定向的地址
        self.spec_pop_addr = spec_pop_addr  # RAS的栈顶数据
        self.ssp = ssp  # commit栈顶指针
        self.sctr = sctr    # commit栈顶重复元素计数器
        self.nsp = nsp  # commit栈顶，会被ssp覆盖
        self.TOSR = TOSR    # spec栈顶指针
        self.TOSW = TOSW    #spec栈数据分配指针
        self.NOS = NOS  
        self.BOS = BOS
        # self.debug = debug
