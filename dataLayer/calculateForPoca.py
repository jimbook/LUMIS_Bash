import math
import dataLayer
import numpy as np
import pandas as pd
from dataLayer.auxiliaryFunction import *
from dataLayer.parameterStorage import *
#将数据处理成可以加速处理的数据格式-更快
# @timeCount
def pretreatment(rawData: pd.DataFrame,replaceInfo:np.array):
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

# 从数据中获取基线和阈值
# @timeCount
def getParameter(rawData):
    baseline = np.empty((8,36))
    threshold = np.empty((8, 36))
    for i in range(8):
        board = rawData.loc[rawData[dataLayer._Index[-1]] == i]
        for j in range(36):
            hist,_ = np.histogram(board.iloc[:,j].values,bins=np.arange(300,1000))
            tmp = np.argmax(hist)
            baseline[i,j] = tmp + 300
            threshold[i,j] = np.argmin(hist[tmp:tmp + 30])+baseline[i,j]
    return baseline,threshold

# 用平均值法均一化、卡阈值、减去基线（同时低于基线的置零）-可加速
# @timeCount
def meanScale(event: np.array,mean_scale: np.array,threshold: np.array,baseline: np.array):
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
    first = event # * mean_scale
    np.place(first,first < threshold,0) #*mean_scale
    second = first - baseline #*mean_scale
    np.place(second,second < 0,0)
    return second

# 检查事件是否符合条件（1~2个bar触发，两个bar触发时必须相邻）并将数据转换成指定格式-可加速
# @timeCount
def checkTriggerAvailable(event: np.array):
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
# @timeCount
def fastCalculateTriggerPositions(event: np.array,geometry: np.array, detectorSize: np.array):
    '''
    快速计算触发点位置（没有迭代,默认位2个相邻bar触发，兼容单bar触发,没有倾斜修正）
    计算公式：最大值触发bar索引（注意索引从0开始） * 一半的闪烁体长度（因为是交错叠放的）...
    :param event: (None,8,4)-[max,min,maxIndex,minIndex]
    :param geometry: (8,7)-[vertexVector_x,vertexVector_y,vertexVector_z,normalVector_x,normalVector_y,normalVector_z,sitMode]
    :param detectorSize:(4,)-[length,width,barInterval,barHeight]
    :return:(None,8,2)[x or y,z]
    '''
    output = np.full((event.shape[0], 8, 3), np.nan)
    xMode = geometry[:, 6] == 0
    yMode = geometry[:, 6] == 1
    barSite = event[:, :, 2] - event[:, :, 3]
    EnergeRate = event[:, :, 0] / (event[:, :, 0] + event[:, :, 1]) * detectorSize[2] / 2
    # 计算x取向的数据
    output[:, xMode, 0] = event[:, xMode, 2] * detectorSize[2] / 2 + EnergeRate[:, xMode] * (barSite[:, xMode]) + \
                          detectorSize[2] * (-barSite[:, xMode] + 1) / 2 + geometry[xMode, 0]
    # 计算y取向的数据
    output[:, yMode, 1] = event[:, yMode, 2] * detectorSize[2] / 2 + EnergeRate[:, yMode] * (barSite[:, yMode]) + \
                          detectorSize[2] * (-barSite[:, yMode] + 1) / 2 + geometry[yMode, 1]
    # 计算z方向上的数据
    output[:, :, 2] = event[:, :, 2] % 2 * detectorSize[3] + (-1) ** event[:, :, 2] * EnergeRate + geometry[:, 2]
    return output

# 快速反演粒子径迹（仅用于xy正交放置时）
# @timeCount
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
        wanted_z = geometry[::2,2] + detectorSize[-1] # shape(4,)
    output = np.empty((event.shape[0],4,3))
    # 注意这里以z轴为X，x轴/y轴为Y进行拟合，以兼容垂直入射的情况
    slop_x,intercept_x = getLineFrom2Pos(event[:,xBoard[::2],2],event[:,xBoard[::2],0],
                                         event[:,xBoard[1::2],2],event[:,xBoard[1::2],0]) # shape(None,2)
    slop_y,intercept_y = getLineFrom2Pos(event[:,yBoard[::2],2],event[:,yBoard[::2],1],
                                         event[:,yBoard[1::2],2],event[:,yBoard[1::2],1])
    for i in range(wanted_z.shape[0]):
        output[:, i, 0] = wanted_z[i]*slop_x[:,int(i/2)] + intercept_x[:,int(i/2)]
        output[:, i, 1] = wanted_z[i]*slop_y[:,int(i/2)] + intercept_y[:,int(i/2)]
        output[:, i, 2] = wanted_z[i]
    return output

# 计算poca点
# @timeCount
def calculatePocaPostions(event: np.array):
    '''
    :param event: (None,4,3)[x,y,z]
    :return:(None,10)[poca_x,poca_y,poca_z,theta,p1_x, p1_y, p1_z, p2_x, p2_y, p2_z]
    '''
    output = np.empty((event.shape[0],10))
    for i in range(event.shape[0]):
        poca,theta = calculateOnePocaPosition(event[i])
        output[i, :3] = poca
        output[i, 3] = theta
        output[i, 4:7] = event[i, 1]
        output[i, 7:] = event[i, 2]
    return output

# 辅助计算函数：计算一个事件中的poca点
def calculateOnePocaPosition(event: np.array):
    """
    计算一个事件中的poca点
    :param event: (4,3)[x,y,z]
    :return:
    """
    # 计算入射，出射基本信息
    inVector = (event[1] - event[0])
    outVector = (event[3] - event[2])
    longSide = event[2] - event[0]
    in_out = np.dot(inVector, outVector)
    in_in = np.dot(inVector, inVector)
    out_out = np.dot(outVector, outVector)
    in_long = np.dot(longSide, inVector)
    out_long = np.dot(longSide, outVector)
    # 计算夹角
    # 单位：°
    theta = math.acos(np.sqrt((in_out * in_out) / (in_in * out_out))) * 180 / np.pi
    # 计算poca点
    if in_in < 1e-4:
        t1 = in_long / in_in
        t2 = - out_long / out_out
    else:
        t1 = (in_out * out_long - out_out * in_long) / (in_out ** 2 - in_in * out_out)
        t2 = in_in / in_out * t1 - (in_long / in_out)
    return ((event[0] + t1 * inVector) + (event[2] + t2 * outVector)) / 2, theta

# 辅助计算函数：通过两个点求直线函数
def getLineFrom2Pos(x1,y1,x2,y2):
    slop = (y1 - y2) / (x1 - x2)
    intercept = (y2*x1 - y1*x2) / (x1 - x2)
    return slop,intercept


# 提供一个快速计算触发点和poca点的类
class pocaAnalizy(object):
    def __init__(self,rawData: pd.DataFrame,**kwargs):
        self.baseline = kwargs.get("baseline",Baseline)
        self.threshold = kwargs.get("threshold",Threshold)
        self.meanScale = kwargs.get("meanScale",MeanScale)
        self.channelReplace = kwargs.get("channelReplace",ChannelReplace)
        self.geometry = kwargs.get("geometry",GeometryCoordinateSystem)
        self.detectorSize = kwargs.get("detectorSize",DetectorSize)
        self.rawData = rawData

    @property
    def HitPositions(self):
        a0 = pretreatment(self.rawData,self.channelReplace.values)
        a0 = meanScale(a0,self.meanScale.values[:,:32],self.threshold.values[:,:32],self.baseline.values[:,:32])
        a0 = checkTriggerAvailable(a0)
        a0 = fastCalculateTriggerPositions(a0,self.geometry.values,self.detectorSize.values[0])
        return fastCalculateParticleTrack(a0,self.geometry.values,self.detectorSize.values[0],np.array([25.36, 430, 1035, 1440]))

    @property
    def pocaPositions(self):
        try:
            return calculatePocaPostions(self.HitPositions)
        except ValueError:
            import traceback
            traceback.print_exc()

    # @property
    # def rawData(self):
    #     return self._rawData
    #
    # @rawData.setter
    # def rawData(self,value: pd.DataFrame):
    #     if isinstance(value,pd.DataFrame):
    #         for i in value.index:
    #             if i in rawData
    #
    #
    # @property
    # def baseline(self):
    #     return self._baseline
    #
    # @property
    # def threshold(self):
    #     return self._threshold


