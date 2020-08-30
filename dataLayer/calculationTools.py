'''
包含一些用于计算工具函数
'''
import pandas as pd
import numpy as np
from dataLayer.constantParameter import _Index

# 计算添加能谱数据
def ToEnergySpetrumData(data: pd.DataFrame,tier: list = None,channel: list = None) -> list:
    '''
    :param data:
    ------------DATA STRUCTURE------------
                0~35        36          37
    COLUMNS: chn_00~chn_35 triggerID boardID
    SHAPE:  (None,38)
    :return:
    '''
    if tier is None:
        _boardID = np.unique(data[_Index[-1]].values)
        _boardID.sort()
    else:
        _boardID = tier
    if channel is None:
        _channel = range(36)
    else:
        _channel = channel
    ESD = []
    for i in range(len(_boardID)):
        ESD.append([])
    for j in range(len(_boardID)):
        boardIndex = (data[_Index[-1]] == _boardID[j])
        for i in _channel:
            _chn = data[_Index[i]].values
            index = (_chn != 0) & boardIndex
            chn = _chn[index]
            y, x = np.histogram(chn,bins=np.arange(2**12))
            ESD[j].append(y)
    return ESD

# 计算符合能谱
def ToCoincidentEnergySpetrumData(data: pd.DataFrame,tier: int, channel: int, channel_coin: int):
    index = (data[_Index[-1]] == tier) & \
            (data[_Index[channel]] != 0) & \
            (data[_Index[channel_coin]] != 0)
    _d = data[_Index[channel]].values[index]  # 将目标板子和通道已触发的数据筛选出
    y, x = np.histogram(_d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
    return y

if __name__ == '__main__':
    pass


