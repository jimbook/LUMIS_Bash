'''
包含一些通用的参数
'''

# -----------数据索引-----------
_Index = []
for i in range(36):
    _Index.append('chn_{:0>d}'.format(i))
_Index.append('triggerID')
_Index.append('boardID')

# -----------指示数据大小的枚举-------
from enum import Enum
class sizeUnit_binary(Enum):
    B = 1
    KB = 1024
    MB = 1024 * 1024

if __name__ == '__main__':
    print(sizeUnit_binary.B.value)




