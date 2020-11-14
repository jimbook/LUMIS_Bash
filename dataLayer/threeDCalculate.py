import numpy as np
import pandas as pd
import dataLayer
from dataLayer.baseCore import *
import os
import numba
# 处理缪子事件的类
class Moun_(object):
    '''
    缪子事件处理流：
        1.检查是否有八层数据——是：继续；否：丢弃
        替换坏道
        2.用平均值法均一化，卡阈值，减去基线（低于基线的置零）
        3.检查每层的触发情况（要求1~2个bar触发，两个bar触发时必须相邻）--是：继续；否：丢弃
        4.计算各层的触发位置
        5.通过触发位置计算poca点
        6.讲poca点数据输出到tmpStorage中
        7.当数据量足够时，通过比例算法计数
    '''

    def __init__(self,auxiliaryPath: str):
        '''
        导入阈值、基线、均一化数据
        '''
        self.baseline = pd.read_csv(os.path.join(auxiliaryPath, "bl.csv"), index_col=0, header=0)
        self.threshold = pd.read_csv(os.path.join(auxiliaryPath, "tr.csv"), index_col=0, header=0)
        self.meanScaleInfo = pd.read_csv(os.path.join(auxiliaryPath, "mean_scale.csv"), index_col=0, header=0)
        self.channelReplace = pd.read_csv(os.path.join(auxiliaryPath, "channelReplace.csv"), index_col=0, header=0)

    def pretreatment(self,rawData: pd.DataFrame) -> pd.DataFrame:
        '''
        数据预处理：
        1.替换坏道
        2.用平均值法均一化
        3.卡阈值
        :return:
        '''
        pass

    # 替换坏道-全局替换/单事件替换
    def replaceBadChannel(self,rawData: pd.DataFrame):
        board = rawData[dataLayer._Index[-1]].values
        for i in range(self.channelReplace.shape[0]):
            boardChoose = board == self.channelReplace.loc[i, "boardID"]
            oldChannel = dataLayer._Index[self.channelReplace.loc[i, "oldChannelID"]]
            newChannel = dataLayer._Index[self.channelReplace.loc[i, "newChannelID"]]
            rawData.loc[boardChoose, oldChannel] = rawData.loc[boardChoose, newChannel]
        return rawData

    # 用平均值法均一化-单事件
    def meanScale(self,event: pd.DataFrame):
        event.iloc[:,:32].mul(self.meanScaleInfo.iloc[:,:32])
        return event

    # 将小于阈值的置零减去基线-单事件
    def filterBasedOnThreshold(self,event: pd.DataFrame):
        tmp = event.iloc[:,:32]
        check = tmp - self.threshold < 0

    #
    def minusBaseline(self,event: pd.DataFrame):
        pass

# 替换坏道-全局替换/单事件替换
def replaceBadChannel(rawData:pd.DataFrame,replaceInfo: pd.DataFrame):
    board = rawData[dataLayer._Index[-1]].values
    for i in range(replaceInfo.shape[0]):
        boardChoose = board == replaceInfo.loc[i,"boardID"]
        oldChannel = dataLayer._Index[replaceInfo.loc[i,"oldChannelID"]]
        newChannel = dataLayer._Index[replaceInfo.loc[i,"newChannelID"]]
        rawData.loc[boardChoose,oldChannel] = rawData.loc[boardChoose,newChannel]
    return rawData

# 用平均值法均一化-单事件
def meanScale_event(event: pd.DataFrame,mean_scale: pd.DataFrame):
    event.iloc[:,:32].mul(mean_scale.iloc[:,:32])
    return event



if __name__ == '__main__':
    import time
    d = pd.read_csv("../tmpStorage/channelReplace.csv")
    hd = h5Data("../testData/h5Data/tempData_22_59_16.h5","r")
    data = hd.getData(-1)
    start = time.time()
    d[d<10] = 23
    print(d)
    print(time.time() - start)


