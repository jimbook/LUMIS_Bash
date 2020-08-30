'''
用于GUI进程存放数据
'''
import numpy as np
import pandas as pd
import os
from dataLayer import calculationTools
from dataLayer.baseCore import h5Data
from inspect import isfunction
from dataLayer.constantParameter import _Index
'''
*****************DATA STRUCTURE*****************
==============INPUT DATA STRUCTURE==============
type: list[list[int]]
shape:(None,38)
----------------SUBLIST STRUCTURE---------------
INDEX   MEAN
0~35    channel 0~35
36      triggerID
37      boardID
TOTAL LENGTH:38
==============STORAGE DATA STRUCTURE=============
------------------dataInMemory-------------------
type: list[list[int]]
shape:(None,38)

SUBLIST STRUCTURE:
INDEX   MEAN
0~35    channel 0~35
36      triggerID
37      boardID
TOTAL LENGTH:38

---------------------h5Path-----------------------
type: str
mean: path of h5 file

---------------------h5Index----------------------
type: int
mean: how many DataSets in h5 file are available

----------------EnergySpetrumData-----------------
type: list[list[list[int]]]
shape:(0~8,36,4095)
DATA STRUCTURE:
AXIS0:boardID           AXIS1:channel           AXIS2:energy spetrum data
0~7                     0~35                    0~4094

--------------------statusInfo---------------------
type: dict
DATA STRUCTURE:
        -KEY-       -value-
type     int          list
content  0~8   (TrigDAC,bias,TrigMode)

-------------------baseline------------------------

==============OUTPUT DATA STRUCTURE==============
'''
# 标志位
_realtime = False # 当前数据为实时测量数据还是离线分析数据
_reset = False
# 离线数据
_dataOffline = pd.DataFrame()

# 实时测量元数据
_dataInMemory = []
_h5Path = ''
_h5Index = 0


# 能谱数据
_EnergySpetrumData = []

# 状态信息
_statusInfo = {}

# 基线数据
_baseline = {}
#*******************外部函数********************

#----------------input--------------
# 新增数据:
# 1.向内存里添加数据
# 2.计算各道能谱，并向merge能谱数据
# 3.如果reset置为Ture，下一次载入数据时将会清空内存中的数据，同时将h5Index加一
def addDataInMemory(newData: list,reset: bool =False):
    global _h5Index,_reset
    if _reset:
        _dataInMemory.clear()
        _h5Index += 1
        _reset =False
    _dataInMemory.extend(newData)
    _d = pd.DataFrame(newData,columns=_Index)
    _l = calculationTools.ToEnergySpetrumData(_d)
    for i in range(len(_l)):
        tempBoardChannel = _l[i]
        try:
            _EnergySpetrumData[i]
        except IndexError:
            _EnergySpetrumData.append([])
        for j in range(len(tempBoardChannel)):
            try:
                _EnergySpetrumData[i][j] += tempBoardChannel[j]
            except IndexError:
                _EnergySpetrumData[i].append(tempBoardChannel[j])
    if reset:
        _reset = True

# 设置h5文件路径和信息
def setH5Path(h5Path: str,h5Index: int = 0):
    global _h5Path,_h5Index
    if os.path.exists(h5Path):
        if os.path.splitext(h5Path)[0] == '.h5':
            _h5Path = h5Path
            _h5Index = h5Index
        else:
            raise Exception('File with extension .{} is not support.'.format(os.path.splitext(h5Path)[0]))
    else:
        raise FileNotFoundError('{} can not found.'.format(h5Path))

#---------------clear--------------
# 清空所有数据(暂时只清空元数据和能谱数据)
def clearAllData():
    global _h5Index,_h5Path
    _dataInMemory.clear()
    _EnergySpetrumData.clear()
    _h5Index = 0
    _h5Path = ''

# 清空能谱数据
def clearEnergySpetrumData():
    _EnergySpetrumData.clear()

# 重置基线设置
def resetBaseline():
    _baseline.clear()

#--------------output-------------

# 获取内存中的数据
def getDataInMemory(startIndex: int = 0,asDataFrame: bool = True):
    if asDataFrame:
        _d = pd.DataFrame(_dataInMemory[startIndex:],columns=_Index)
        return _d
    else:
        return _dataInMemory

# 获取内存中数据的大小(行数)
def getSizeInMemory():
    return len(_dataInMemory)

# 对所有数据进行计算，返回结果
def calculationAllData(MapFunc,reduceFunc):
    '''
    :param MapFunc: 计算函数，要求接收一个无重复triggerID的标准结构DataFrame参数，对DataFrame进行计算，返回结果R
    :param reduceFunc: 对MapFunc返回的结果进行merge，要求可以输入两个参数,返回两个参数merge后的结果
    :return:
    '''
    if not (isfunction(MapFunc) and isfunction(reduceFunc)):
        raise ValueError('Input parameter should be function.')
    global _h5Path,_h5Index
    _d = pd.DataFrame(_dataInMemory,columns=_Index)
    _r = MapFunc(_d)
    file = h5Data(_h5Path,mode='r')
    for i in range(_h5Index):
        _d = pd.DataFrame(file.getData(i),columns=_Index)
        reduceFunc(_r,MapFunc(_d))
    file.close()
    return _r

# 获取能谱数据
def getEnergySpetrumData(tier: int,channel: int or str):
    if isinstance(channel,str):
        chnIndex = _Index.index(channel)
    else:
        chnIndex = channel
    try:
        rdata = _EnergySpetrumData[tier][chnIndex]
    except IndexError:
        rdata = np.zeros(2**12-1)
    return rdata

# 获取基线
def getBaseline(tier: int, channel: int):
    return _baseline.get(tier,np.zeros(32))[channel]

if __name__ == "__main__":
    import pyqtgraph.examples
    pyqtgraph.examples.run()