import numba
import numpy as np
import pandas as pd
import tqdm
import dataLayer
from dataLayer.baseCore import *
import os
import time
import datetime
import scipy.stats
auxiliaryPath = "./tmpStorage"
baseline = pd.read_csv(os.path.join(auxiliaryPath, "bl.csv"), index_col=0, header=0)
threshold = pd.read_csv(os.path.join(auxiliaryPath, "tr.csv"), index_col=0, header=0)
meanScaleInfo = pd.read_csv(os.path.join(auxiliaryPath, "mean_scale.csv"), index_col=0, header=0)
channelReplace = pd.read_csv(os.path.join(auxiliaryPath, "channelReplace.csv"), index_col=0, header=0)
'''
加速程序预处理约定-处理成如下结构：
np.array -shape
(
None    triggerID
,8      boardID
,32     chn_0~chn_31
)
'''
# 辅助函数：打印loop
class idxCount(object):
    def __init__(self,allCount: int):
        self.allCount = allCount
        self.nowCount = 0

    def printNowCount(self):
        if self.nowCount == 0:
            self.start = time.time()
            usedTime = 0
            progress = self.nowCount / self.allCount
            print("\r{}/{}--{:.2%}--used time:{}--estimate using time:{}".format(
                self.nowCount, self.allCount, progress, datetime.timedelta(seconds=usedTime),
                "??:??:??"), end=''
            )
        else:
            usedTime = time.time() - self.start
            progress = self.nowCount/self.allCount
            print("\r{}/{}--{:.2%}--used time:{}--estimate using time:{}".format(
                self.nowCount,self.allCount,progress,datetime.timedelta(seconds=usedTime),
                datetime.timedelta(seconds=usedTime/progress)),end=''
                )
        self.nowCount += 1

    def __del__(self):
        print('')

# 辅助函数：打印函数运行时间
def timeCount(function):
   def wrapper(*args, **kwargs):
        time_start = time.time()
        res = function(*args, **kwargs)
        cost_time = time.time() - time_start
        print("function:{},running time:{}".format(function.__name__,datetime.timedelta(seconds=cost_time)))
        return res
   return wrapper

#将数据处理成可以加速处理的数据格式
@timeCount
def pretreatment(rawData: pd.DataFrame,replaceInfo:np.array = channelReplace.values):
    '''
    将数据处理成可以加速处理的数据格式
    1.筛选数据-留下只有八层的数据
    2.替换坏道
    3.将数据转换成(None,8,32)[chn_00~chn_31]
    :param rawData:
    :return:(None,8,32)[chn_00~chn_31]
    '''
    firstData = rawData.set_index(dataLayer._Index[-2])
    result = []
    triggerID = np.unique(firstData.index.values)

    ic = idxCount(triggerID.shape[0])
    for i in triggerID:
        ic.printNowCount()
        event = firstData.loc[i]
        # 留下只有八层的数据
        if event.shape[0] == 8:
            replacedEvent = replaceBadChannel_forNUmba(event.values,replaceInfo=replaceInfo)
            result.append(replacedEvent[:,:32])
    return np.array(result)

# 预处理函数：替换坏道-可加速
@numba.njit()
def replaceBadChannel_forNUmba(rawData: np.array, replaceInfo: np.array):
    '''
    替换坏道-可加速
    将数据转换成numpy数组可以使用numba加速
    仅在巨量数据时使用：数据超过GB级别时，否则会降低速度，也可在用于加速程序中调用。
    :param rawData:(None,39)-column = _Index
    :param replaceInfo:
    :return:(None,39)-column = _Index
    '''
    board = rawData[:,-1]
    for boardID,oldChn,newChn in replaceInfo:
        boardChoose = board == boardID
        rawData[boardChoose,oldChn] = rawData[boardChoose,newChn]
    return rawData


#将数据处理成可以加速处理的数据格式-更快
@timeCount
def pretreatment_forNumba(rawData: pd.DataFrame,replaceInfo:np.array = channelReplace.values):
    '''
    将数据处理成可以加速处理的数据格式-更快
    1.筛选数据-留下只有八层的数据
    2.替换坏道
    3.将数据转换成(None,8,32)[chn_00~chn_31]
    :param rawData:
    :return:(None,8,32)[chn_00~chn_31]
    '''
    # 筛选数据-留下只有八层的数据
    boardCount = rawData.loc[:,dataLayer._Index[-2:]].groupby(dataLayer._Index[-2]).count()
    boardCount_filer = boardCount.index.values[boardCount.iloc[:,0].values == 8]
    first = rawData.set_index(dataLayer._Index[-2]).loc[boardCount_filer,dataLayer._Index[:36]].values
    first = first.reshape((int(first.shape[0]/8),8,-1))
    # first 为筛选后的数据，np.array - shape(None,8,36) column:chn_00~chn_35
    # 替换坏道
    for boardID,oldChn,newChn in replaceInfo:
        first[:,boardID,oldChn] = first[:,boardID,newChn]
    # 将数据转换成(None,8,32)[chn_00~chn_31]
    return first[:,:,:32]

# 用平均值法均一化、卡阈值、减去基线（同时低于基线的置零）-可加速
@timeCount
def meanScale_forNumba(event: np.array,mean_scale: np.array,threshold: np.array,baseline: np.array):
    '''
    用平均值法均一化、卡阈值、减去基线（同时低于基线的置零）-可加速
    将数据转换成numpy数组可以使用numba加速
    仅在巨量数据时使用，否则会降低速度，也可在用于加速程序中调用。
    :param event: (None,8,32)
    :param mean_scale: (8,32) chn_00~chn_31
    :param threshold: (8,32)
    :param baseline: (8,32)
    :return:(None,8,32)
    '''
    first = event * mean_scale
    np.place(first,first < threshold,0)
    second = first - baseline
    np.place(second,second < 0,0)
    return second

# 检查事件是否符合条件（1~2个bar触发，两个bar触发时必须相邻）并将数据转换成指定格式-可加速
@timeCount
def checkTriggerAvailable_forNumba(event: np.array):
    '''
    检查事件是否符合条件（1~2个bar触发，两个bar触发时必须相邻）并将数据转换成指定格式
    :param event: np.array-shape(None,8,32)
    :return:(None,8,4)-[max,min,maxIndex,minIndex]
    '''
    checkNotZero = event != 0 # (None,8,32)
    triggerBarNum = np.sum(checkNotZero,axis=2) #(None,8)
    del checkNotZero
    triggerCheck = (triggerBarNum == 2) | (triggerBarNum == 1)
    triggerCheck = np.sum(triggerCheck, axis=1) # (None,)
    triggerCheck = triggerCheck == 8
    del triggerBarNum
    # 筛选1~2个bar触发的数据
    first = event[triggerCheck]
    np.place(first, first < 0.1, np.nan)
    del triggerCheck
    output = np.empty((first.shape[0], 8, 4))
    np.nanmax(first, out=output[:, :, 0],axis=2)
    np.nanmin(first, out=output[:, :, 1],axis=2)
    output[:, :, 2] = np.nanargmax(first,axis=2)
    output[:, :, 3] = np.nanargmin(first,axis=2)
    # 筛选bar触发时相邻
    triggerCheck = np.sum(np.abs(output[:, :, 2] - output[:, :, 3]),axis=1) <= 8
    return output[triggerCheck]

# 快速计算触发点位置（没有迭代）
@timeCount
def fastCalculateTriggerPositions_forNumba(event: np.array,geometry: np.array, detectorSize: np.array):
    '''
    快速计算触发点位置（没有迭代,默认位2个相邻bar触发，兼容单bar触发,没有倾斜修正）
    计算公式：最大值触发bar索引（注意索引从0开始） * 一半的闪烁体长度（因为是交错叠放的）...
    :param event: (None,8,4)-[max,min,maxIndex,minIndex]
    :param geometry: (8,7)-[vertexVector_x,vertexVector_y,vertexVector_z,normalVector_x,normalVector_y,normalVector_z,sitMode]
    :param detectorSize:(4,)-[length,width,barInterval,barHeight]
    :return:(None,8,3)[x,y,z]
    '''
    output = np.full((event.shape[0], 8, 3),np.nan)
    xMode = geometry[:, 6] == 0
    yMode = geometry[:, 6] == 1
    barSite = event[:, :, 2] - event[:, :, 3]
    EnergeRate = event[:, :, 0]/(event[:, :, 0] + event[:, :, 1]) * detectorSize[2]/2
    # 计算x取向的数据
    output[:, xMode, 0] = event[:, xMode, 2] * detectorSize[2]/2 + EnergeRate[:, xMode] * (barSite[:, xMode]) + detectorSize[2] * (-barSite[:, xMode] + 1) / 2 + geometry[xMode, 0]
    # 计算y取向的数据
    output[:, yMode, 1] = event[:, yMode, 2] * detectorSize[2]/2 + EnergeRate[:, yMode] * (barSite[:, yMode]) + detectorSize[2] * (-barSite[:, yMode] + 1) / 2 + geometry[yMode, 1]
    # 计算z方向上的数据
    output[:, :, 2] = event[:, :, 2] % 2 * detectorSize[3] + (-1) ** event[:, :, 2] * EnergeRate + geometry[:, 2]
    return output

# 快速反演粒子径迹（仅用于xy正交放置时）
@timeCount
def fastCalculateParticleTrack(event: np.array,geometry: np.array, detectorSize: np.array,wanted_z: np.array = None):
    '''
    快速反演粒子径迹（仅用于xy正交放置时）
    :param event: (None,8,3)[x,y,z],x和y没有时为nan
    :param geometry: (8,7)-[vertexVector_x,vertexVector_y,vertexVector_z,normalVector_x,normalVector_y,normalVector_z,sitMode]
    :param detectorSize:(4,)-[length,width,barInterval,barHeight]
    :param wanted_z:(4,)
    :return:(None,4,3)[x,y,z]
    '''
    xBoard = [0,2,4,6]
    yBoard = [1,3,5,7]
    if wanted_z is None:
        wanted_z = geometry[::2,-1] + detectorSize[-1] # shape(4,)
    output = np.empty((event.shape[0],4,3))
    # 注意这里以z轴为X，x轴/y轴为Y进行拟合，以兼容垂直入射的情况
    slop_x,intercept_x = getLineFrom2Pos(event[:,xBoard[::2],2],event[:,xBoard[::2],0],
                                         event[:,xBoard[1::2],2],event[:,xBoard[1::2],0]) # shape(None,2)
    slop_y,intercept_y = getLineFrom2Pos(event[:,yBoard[::2],2],event[:,yBoard[::2],1],
                                         event[:,yBoard[1::2],2],event[:,yBoard[1::2],1])
    for i in range(wanted_z.shape[0]):
        output[:, i, 0] = wanted_z[i]*slop_x[:,i%2] - intercept_x[:,i%2]
        output[:, i, 1] = wanted_z[i]*slop_y[:,i%2] - intercept_y[:,i%2]
        output[:, i, 2] = wanted_z[i]
    return output

# 辅助计算函数：通过两个点求直线函数
def getLineFrom2Pos(x1,y1,x2,y2):
    slop = (y1 - y2) / (x1 - x2)
    intercept = (y2*x1 - y1*x2) / (x1 - x2)
    return slop,intercept

# 计算poca点
@timeCount
def calculatePocaPostions_forNumba(event: np.array):
    '''
    :param event: (None,4,3)[x,y,z]
    :return:(None,10)[poca_x,poca_y,poca_z,theta,p1_x, p1_y, p1_z, p2_x, p2_y, p2_z]
    '''
    output = np.empty((event.shape[0],10))
    for i in range(event.shape[0]):
        poca,theta = calculateOnePocaPostion(event[i])
        output[i, :3] = poca
        output[i, 3] = theta
        output[i, 4:7] = event[i, 1]
        output[i, 7:] = event[i, 2]
    return output

def calculateOnePocaPostion(event: np.array):
    '''
    计算一个事件中的poca点
    :param event: (4,3)[x,y,z]
    :return:
    '''
    inVector = (event[1] - event[0]) / np.linalg.norm(event[1] - event[0])
    outVector = (event[3] - event[2]) / np.linalg.norm(event[3] - event[2])
    # 计算夹角
    cosTheta = np.dot(inVector,outVector)/(np.linalg.norm(inVector) * np.linalg.norm(outVector))
    if  cosTheta >= 1:# 由于计算机精度问题，cosTheta可能大于1
        sinTheta = 0
    else:
        sinTheta = np.sqrt(1-cosTheta**2)
    theta = np.arcsin(sinTheta) * 180 / np.pi # 单位：°
    # 计算poca点
    longSide = event[0] - event[2]
    in_in = np.dot(inVector,inVector)
    in_out = np.dot(inVector,outVector)
    out_out = np.dot(outVector,outVector)
    in_long = np.dot(inVector,longSide)
    out_long = np.dot(outVector,longSide)
    D = in_in*out_out - in_out**2
    if D < 1e-4:
        sc = 0
        tc = (in_out / out_out) if in_out > out_out else (out_long / out_out)
    else:
        sc = (in_out * out_long - out_out * in_long) / D
        tc = (in_in * out_long - in_out * in_long) / D
    dP = longSide + (inVector * sc) - (outVector * tc)
    poca = event[0] + (inVector * sc) - (dP * sc)
    return poca,theta


if __name__ == '__main__':
    d = pd.read_csv("../tmpStorage/channelReplace.csv")
    hd = h5Data("../testData/h5Data/tempData_22_59_16.h5","r")
    data = hd.getData(0)
    fd = pretreatment_forNumba(data)
    print(fd.shape)
    msData = meanScale_forNumba(fd,meanScaleInfo.values[:,:32],threshold.values[:, :32],baseline.values[:,:32])
    cData = checkTriggerAvailable_forNumba(msData)
    print(cData.shape)
