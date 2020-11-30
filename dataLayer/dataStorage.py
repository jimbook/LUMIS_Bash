'''
用于GUI进程存放数据
'''
import numpy as np
import pandas as pd
import os,time
from dataLayer import calculationTools
from dataLayer import _Index
from dataLayer.baseCore import h5Data
'''
*****************DATA STRUCTURE*****************
==============INPUT DATA STRUCTURE==============
----------------DATA STRUCTURE---------------
type:       DataFrame
dtype:      int64
shape:      (None, 38)

COL_INDEX   MEAN
0~35        channel 0~35
36          triggerID
37          boardID
----------------EnergySpectrumData-----------------
type:       np.array
dtype:      int64
shape:(8, 36, 4095)

AXIS0:boardID           AXIS1:channel           AXIS2:energy spectrum data
0~7                     0~35                    0~4094
--------------------statusInfo---------------------
type: dict

        -KEY-       -value-
type     int         tuple
content  0~8   (TrigDAC,bias,TrigMode)

-------------------baseline------------------------

==============OUTPUT DATA STRUCTURE==============
'''
#==============辅助参数===============
# 获取到数据的数目/索引(用于寻找新增数据)
_dataIndex = 0

# h5文件路径
_path = ''

# playBack文件
_playBackData: h5Data = None

#=============固定数据============
# 能谱数据
_EnergySpectrumData = np.zeros((8, 36, 4095)).astype('int64')

# 基线数据
_baseline = np.zeros((8, 36)).astype('int64')

# poca点数据
_pocaPos = np.empty((500,4))
_pocaCount = 0

# 检测高Z物体报警索引
_alarmIndex = 0
_alarmTime = time.time()

#***************内部函数*****************

# 新增数据:计算各道能谱，并merge能谱数据
def mergeEnergySpectrum(newData: pd.DataFrame):
    global _EnergySpectrumData
    newSpectrum = calculationTools.ToEnergySpectrumData(newData)
    _EnergySpectrumData[:newSpectrum.shape[0]] += newSpectrum

# 新增数据：计算poca点
def calculatePocaPosition(newData:pd.DataFrame):
    global _pocaPos,_pocaCount
    newPoca = calculationTools.PocaPosition(newData)
    while _pocaCount+newPoca.shape[0] >= _pocaPos.shape[0]:
        _pocaPos = np.append(_pocaPos, np.empty((500, 4))).reshape((-1, 4))
    _pocaPos[_pocaCount:_pocaCount+newPoca.shape[0]] = newPoca[:,:4]
    _pocaCount += newPoca.shape[0]

#*******************外部函数********************

#----------------input--------------
# 设置h5文件路径和信息
def setH5Path(h5Path: str):
    global _dataIndex, _path
    if os.path.exists(h5Path):
        if os.path.splitext(h5Path)[-1] == '.h5':
            _path = h5Path
            _dataIndex = 0
        else:
            raise Exception('File with extension .{} is not support.'.format(os.path.splitext(h5Path)[0]))
    else:
        raise FileNotFoundError('{} can not found.'.format(h5Path))

# 更新一次数据（当前只更新能谱数据、poca点数据）
def update():
    global _dataIndex, _path
    h5 = h5Data(_path,'r')
    newData = h5.getData(-2, _dataIndex)
    mergeEnergySpectrum(newData)
    calculatePocaPosition(newData)
    _dataIndex += newData.shape[0]
    print(getEnergySpetrumData(0,16),h5.getFileName(),h5.index[:])

#------------playBack--------------
# 初始化数据回放
def initPlayBackModule():
    global _path, _playBackData
    _path = './playBack.h5'
    _dataIndex = 0
    _playBackData = h5Data(_path,'w')

# 向h5中添加数据
def playBackAddData(data: np.array, newset: bool = False):
    global _playBackData
    _playBackData.addToDataSet(data)
    _playBackData.flush()
    update()

# 向h5中添加新数据集
def playBackNewSet():
    _playBackData.newSets()

# 结束数据回放
def EndPlayBackModule():
    global _playBackData
    clearAllData()
    _playBackData = None

#---------------clear--------------
# 清空所有数据(暂时只清空索引记录、h5文件指向、能谱数据和基线数据,poca点和poca点索引)
def clearAllData():
    global _dataIndex, _path, _baseline, _EnergySpectrumData,_pocaPos,_pocaCount
    _dataIndex = 0
    _path = ''
    resetBaseline()
    clearEnergySpetrumData()
    clearPocaPostion()

# 清空能谱数据
def clearEnergySpetrumData():
    _EnergySpectrumData = np.zeros((8, 36, 4095)).astype('int64')

# 重置基线设置
def resetBaseline():
    _baseline = np.zeros((8, 36)).astype('int64')

# 清空poca点数据
def clearPocaPostion():
    _pocaPos = np.empty((500, 3))
    _pocaCount = 0
    resetAlarm()

# 重置报警索引
def resetAlarm():
    _alarmIndex = _pocaCount
    _alarmTime = time.time()

#--------------output-------------
# 获取h5数据指向
def getH5Data() -> h5Data:
    global _path
    return h5Data(_path,'r')

# 获取当前读取到的索引位置(行数)
def getDataIndex():
    return _dataIndex

# 对数据进行计算，返回结果
def calculationData(MapFunc, reduceFunc = None, startIndex: int = 0):
    '''
    :param MapFunc: 计算函数，要求接收一个无重复triggerID的标准结构DataFrame参数，对DataFrame进行计算，返回结果R
    :param reduceFunc: 对MapFunc返回的结果进行merge，要求可以输入两个参数,返回两个参数merge后的结果
    :return:(result, index)
    '''
    if not (callable(MapFunc) and (callable(reduceFunc) or reduceFunc is None)):
        raise ValueError('Input parameter should be function.')
    global _path
    h5 = h5Data(_path, 'r')
    if reduceFunc is None:
        _d = h5.getData(-2, startIndex=startIndex)
        return MapFunc(_d), startIndex + _d.shape[0]
    else:
        _d = h5.getData(0, startIndex=startIndex)
        _r = MapFunc(_d)
        for i in range(1, h5.index.shape[0]):
            _d = pd.DataFrame(h5.getData(i), columns=_Index)
            reduceFunc(_r, MapFunc(_d))
        return _r, startIndex + _d.shape[0]

# 获取能谱数据
def getEnergySpetrumData(tier: int,channel: int or str):
    if isinstance(channel,str):
        chnIndex = _Index.index(channel)
    else:
        chnIndex = channel
    rdata = _EnergySpectrumData[tier][chnIndex]
    return rdata

# 获取基线
def getBaseline(tier: int = None, channel: int = None):
    if tier is None and channel is None:
        return _baseline
    else:
        if tier is  None:
            raise ValueError('When a channel is specified, argument(tier) cannot be None.')
        if channel is None:
            return _baseline[tier]
        else:
            return _baseline[tier][channel]

# 获取poca点数据
def getPocaPosition():
    return _pocaPos[:_pocaCount]

# 检测是否报警
def alarm():
    PoCA = _pocaPos[_alarmIndex:_pocaCount]
    t = time.time() - _alarmTime
    threshold = [0.9, 1.7, 2.2, 3.2, 5.2, 7.6]
    confidence= [0.59, 0.78, 0.85, 0.88, 0.891, 0.912]
    if PoCA.shape[0] > 60 and t > 60:
        idx = int(t // 60 - 1)
        if idx > 5:
            idx = 5
        return calculationTools.checkHighZ(PoCA,threshold[idx]),confidence[idx]
    else:
        return None,0

if __name__ == "__main__":
    import pyqtgraph.examples
    pyqtgraph.examples.run()