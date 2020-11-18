import numba
from numba import cuda
from numba.cuda import random
import numpy as np
import pandas as pd
import math
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

#将数据处理成可以加速处理的数据格式 unused
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

# 预处理函数：替换坏道-可加速 unused
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

@timeCount
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
    first = event# * mean_scale
    t = threshold*mean_scale
    np.place(first,first < threshold*mean_scale,0)
    b= baseline*mean_scale
    second = first - baseline*mean_scale
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
    :return:(None,8,2)[x or y,z]
    '''
    layer_distance_np = np.array([0, 25.36 + 10.64, 405, 405 + 25.36 + 10.64,
                                  1010, 1010 + 25.36 + 10.64, 1415, 1415 + 25.36 + 10.64]).T
    output = np.full((event.shape[0], 8, 3), np.nan)
    xMode = geometry[:, 6] == 0
    yMode = geometry[:, 6] == 1
    barSite = event[:, :, 2] - event[:, :, 3]
    EnergeRate = event[:, :, 0] / (event[:, :, 0] + event[:, :, 1]) * detectorSize[2] / 2

    #
    set_bar =  event[:, xMode, 2] * detectorSize[2] / 2
    en_offset = EnergeRate[:, xMode] * (barSite[:, xMode])
    odd_offset = detectorSize[2] * (-barSite[:, xMode] + 1) / 2
    geo_offset = geometry[xMode, 0]
    all = set_bar + en_offset + odd_offset + geo_offset
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
@timeCount
def fastCalculateParticleTrack(event: np.array,geometry: np.array, detectorSize: np.array,wanted_z: np.array = None):
    '''
    快速反演粒子径迹（仅用于xy正交放置时）
    :param event: (None,8,3)[x,y,z],x和y没有时为nan
    :param geometry: (8,7)-[vertexVector_x,vertexVector_y,vertexVector_z,normalVector_x,normalVector_y,normalVector_z,sitMode]
    :param detectorSize:(4,)-[length,width,barInterval,barHeight]
    :param wanted_z:(4,)
    :return:(None,4,2)[x or y,z]
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
        poca,theta = calculateOnePocaPosition(event[i])
        output[i, :3] = poca
        output[i, 3] = theta
        output[i, 4:7] = event[i, 1]
        output[i, 7:] = event[i, 2]
    return output

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


# 比率算法算法
def ratio_main(event:np.array,detectPlace: np.array,amplification: int = 32*1024,**kwargs):
    '''
    通过比率算法扩展poca点
    :param event: 原始数据(None,10)[poca_x,poca_y,poca_z,theta,p1_x, p1_y, p1_z, p2_x, p2_y, p2_z]
    :param detectPlace: (3,2)[x,y,z]-[min,max)
    :param amplification: 扩展次数
    :param kwargs:theta_cut-角度阈值;device_GPU-是否使用GPU计算;cube_size-探测区域的大小
    :return:(None,6)[MSR_x, MSR_y, MSR_z, MSC, ratio,available]
    '''
    theta_cut = kwargs.get("theta_cut",0.9)
    device_GPU = kwargs.get("device_GPU",True)# todo: 检测GUP是否就绪，未就绪则改为CPU计算
    cube_size = kwargs.get("cube_size",5)
    #============GPU处理部分==========
    # 预处理,分配显存空间
    '''
    input
    1.poca point,Angle:pocaPoints(None,4)-[x,y,z,angle]
    2.poca point-incoming point Vector:poca_inVector(None,4)-[x,y,z]
    3.outgoing point-poca point Vector:out_pocaVector(None,4)-[x,y,z]
    output
    (amplification,6)[MSR_x, MSR_y, MSR_z, MSC, ratio,available]
    '''
    toDevice = np.empty(event.shape).astype(np.float32)
    toDevice[:,:4] = event[:,:4]
    toDevice[:,4:7] = event[:,:3] - event[:, 4:7]
    toDevice[:,7:] = event[:,7:] - event[:,:3]
    toDevice = cuda.to_device(toDevice)
    output = cuda.device_array((amplification,6))
    # 初始化网格参数和随机数生成器
    threads_num = 32
    blocks = math.ceil(amplification / threads_num)
    rng_states = random.create_xoroshiro128p_states(amplification,seed=1)
    # 初始化探测空间
    detectPlace[:,1] = detectPlace[:,1] - detectPlace[:,0]
    detectPlace = detectPlace.reshape((-1,))
    cuda.synchronize()
    _ratioForGPU[blocks,threads_num](rng_states,toDevice,output,*detectPlace,cube_size/2,theta_cut)
    cuda.synchronize()
    result = output.copy_to_host()
    return result[result[:,5] > 0.8]

@cuda.jit
def _ratioForGPU(randomCreater,rawData,output,X_start,X_length,Y_start,Y_length,Z_start,Z_length,cube_size,theta_cut):
    # share memory distribution
    random_points = cuda.shared.array(shape=(32, 3),dtype=numba.float32)    #random points
    RotiaParameters = cuda.shared.array(shape=(32, 3),dtype=numba.float32)  #N_all,Cut_N,Angle_sigma
    tmpSorage = cuda.shared.array(shape=(32, 6),dtype=numba.float32)
    # local memory distribution
    poca_randomVector = cuda.local.array((3,),numba.float32)    #poca point-random point Vector,Angle
    # init randomPoint
    idx = cuda.grid(1)
    random_points[cuda.threadIdx.x,0] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3)*X_length+X_start
    random_points[cuda.threadIdx.x,1] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3+1)*Y_length+Y_start
    random_points[cuda.threadIdx.x,2] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3+2)*Z_length+Z_start
    # init CountParameters
    for i in range(3):
        RotiaParameters[cuda.threadIdx.x,i] = 0.
    # start cycle
    for i in range(rawData.shape[0]):
        # get poca_randomVector
        check = True
        for j in range(3):
            poca_randomVector[j] = rawData[i,j] - random_points[cuda.threadIdx.x,j]
            if poca_randomVector[j] >= cube_size:
                check = False
        # poca在探测区域内
        if check:
            RotiaParameters[cuda.threadIdx.x,0] += 1
            norm = 0.
            for j in range(3):
                norm += poca_randomVector[j]**2
            Angle = rawData[i,3] * abs(1. -norm * 2. / (cube_size * math.sqrt(3.)))
            RotiaParameters[cuda.threadIdx.x,2] += Angle**2
            if Angle <= theta_cut:
                RotiaParameters[cuda.threadIdx.x,2] += 1
        # poca在探测区域外
        else:
            # poca在探测区域上方
            if poca_randomVector[2] < 0:
                upDown = 0
            # poca在探测区域下方
            else:
                upDown = 3
            # load data(poca point and poca_incomingVector/outgoing_pocaVector depend on arg:upDown)
            # from rawData(global memory) to share memory
            for j in range(3):
                tmpSorage[cuda.threadIdx.x,j] = rawData[i,j] # poca point
                tmpSorage[cuda.threadIdx.x,j+3] = rawData[i,j+4+upDown] #poca_incomingVector
            check = True
            for j in range(2):
                tmp = tmpSorage[cuda.threadIdx.x,3+j] / tmpSorage[cuda.threadIdx.x,5] * \
                    (random_points[cuda.threadIdx.x,2] + cube_size / 2 - tmpSorage[cuda.threadIdx.x,2]) \
                        + tmpSorage[cuda.threadIdx.x,j] - random_points[cuda.threadIdx.x,j]
                if tmp >= cube_size:
                    check = False
                    break
                tmp = tmpSorage[cuda.threadIdx.x, 3 + j] / tmpSorage[cuda.threadIdx.x, 5] * \
                      (random_points[cuda.threadIdx.x, 2] - cube_size / 2 - tmpSorage[cuda.threadIdx.x, 2]) \
                      + tmpSorage[cuda.threadIdx.x, j] - random_points[cuda.threadIdx.x, j]
                if tmp >= cube_size:
                    check = False
                    break
            if check:
                RotiaParameters[cuda.threadIdx.x, 0] += 1
                RotiaParameters[cuda.threadIdx.x, 1] += 1
    for i in range(3):
        output[idx,i] = random_points[cuda.threadIdx.x,i]
    output[idx,3] = math.sqrt(RotiaParameters[cuda.threadIdx.x,2] / RotiaParameters[cuda.threadIdx.x,0])
    output[idx,4] = RotiaParameters[cuda.threadIdx.x,1] / RotiaParameters[cuda.threadIdx.x,0]
    if RotiaParameters[cuda.threadIdx.x, 0] > math.floor(100 * (cube_size*2) **2 *0.1):
        output[idx,5] = 1
    else:
        output[idx, 5] = -1
