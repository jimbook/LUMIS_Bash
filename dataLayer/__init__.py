'''
包含一些通用的参数
'''
# -----------数据索引-----------
_Index = []
for i in range(36):
    _Index.append('chn_{:2>d}'.format(i))
_Index.append('temperature')
_Index.append('triggerID')
_Index.append('boardID')

# -----------指示数据大小的枚举-------
from enum import Enum
class sizeUnit_binary(Enum):
    B = 1
    KB = 1024
    MB = 1024 * 1024

# ---------共享数据地址---------
_address = ("127.0.0.1", 50000)
_authkey = b'jimbook'
