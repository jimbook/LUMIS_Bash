import os
import time
from multiprocessing.connection import Connection
import h5py
import numpy as np
import pandas as pd
import dataLayer
from dataLayer.baseCore import *
from dataLayer.calculationTools import *
from dataLayer.calculateForPoca import pocaAnalizy
class sliceData(object):
    def __init__(self,data):
        self.data = data
        self.triggerID = np.arange(0, data.shape[0])
        self.rng = np.random.default_rng()

    def getRandomEvents(self,size: int):
        index = self.rng.integers(self.triggerID.shape[0] - size,size=1)
        return self.data[index[0]:index[0]+size, :]

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm
from tqdm import tqdm
def gaussian(x,amp,average,std):
    return amp*norm.pdf(x,average,std)

def randomPocaCount(data):
    slc = sliceData(data)
    loopNum = 1000
    pocaLength = np.empty((loopNum,), dtype=int)
    for i in range(loopNum):
        poca = PocaPosition(slc.getRandomEvents(130))
        pocaLength[i] = poca.shape[0]
    # fit as gaussian
    myBins = np.arange(40, 81)
    y, x = np.histogram(pocaLength, bins=myBins)
    a0 = np.sum(y)
    a1 = np.average(pocaLength)
    a2 = np.std(pocaLength)
    print("0-amp:{}\taverage:{}\tstd:{}".format(a0, a1, a2))
    vals, covar = curve_fit(gaussian, xdata=x[:-1], ydata=y, p0=[a0, a1, a2])
    print("1-amp:{}\taverage:{}\tstd:{}".format(*vals))
    y1 = gaussian(x[:-1], *vals)
    plt.figure()
    plt.hist(pocaLength, bins=100)
    plt.plot(x[:-1], y1, "r--")
    plt.show()

def angelAnalyse(data):
    PoCA_angel = data
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 2] < 800) & (PoCA_angel[:, 2] > 650)]
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 0] > 270) & (PoCA_angel[:, 0] < 370)]
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 1] > 270) & (PoCA_angel[:, 1] < 370)]
    PoCA_voxels = PoCA_angel[:, 0] // 20 + PoCA_angel[:, 1] // 20 * 100 + PoCA_angel[:, 2] // 20 * 100 * 100
    PoCA_angel_weight = PoCA_angel[:, -1] < 0.3
    PoCA_angel_weight = PoCA_angel_weight * 0.1
    PoCA_angel_weight[PoCA_angel_weight == 0] = 1
    PoCA = pd.DataFrame({"theta":np.power(PoCA_angel[:, -1],2) / 20 * PoCA_angel_weight, "voxels":PoCA_voxels.astype(np.int)}).sort_values("voxels")
    PoCA_max = PoCA.groupby("voxels").mean()
    if PoCA_max.shape[0] > 0:
        return np.max(PoCA_max["theta"].values)
    else:
        return 0

def SDE(data,loopSize: int, timeIndex: int = 1):
    slc = sliceData(data)
    result = np.empty((loopSize,))
    for i in tqdm(range(loopSize)):
        result[i] = angelAnalyse(slc.getRandomEvents(65*timeIndex))
    return result

def ROC(SDE_Ture,SDE_False,step = 0.1):

    result = np.empty((int(15/step),4))
    for i in tqdm(range(int(15/step))):
        result[i,0] = np.sum(SDE_Ture > i*step)/SDE_Ture.shape[0]
        result[i,1] = np.sum(SDE_False> i*step)/SDE_False.shape[0]
        result[i,2] = np.sum(SDE_Ture < i*step)/SDE_Ture.shape[0]
        result[i,3] = np.sum(SDE_False< i*step)/SDE_False.shape[0]
    return result

if __name__ == '__main__':

    data_null = h5Data("testData/h5Data/2020_11_28/tempData_17_53_55.h5", 'r').getData(-2)
    data_Pb = h5Data("testData/h5Data/2020_11_28/tempData_22_00_33.h5", 'r').getData(-2)
    pb = PocaPosition(data_Pb)[:, :4]
    bg = PocaPosition(data_null)[:, :4]
    np.savetxt(os.path.join('./res/2020-12-1/','bg.txt'),bg,delimiter=',')
    np.savetxt(os.path.join('./res/2020-12-1/', 'pb.txt'), pb, delimiter=',')
    # for timeIndex in range(1,21,1):
    timeIndex = 2
    r_Pb = SDE(pb, 10000, timeIndex)
    r_null = SDE(bg,10000, timeIndex)

    roc = ROC(r_Pb,r_null,)
    fp1 = roc[roc[:,1] <= 0.1]
    # v = np.power(0 - roc[:,1], 2) + np.power(1 - roc[:, 0], 2)
    # v_fp1 = np.power(0 - fp1[:,1], 2) + np.power(1 - fp1[:, 0], 2)
    i = fp1.shape[0]
    print(i*0.1)
    print(np.sum(r_Pb >= i*0.1)/r_Pb.shape[0])
    print(np.sum(r_null >= i * 0.1) / r_null.shape[0])

    # v2 = np.power(0 - roc[:,2], 2) + np.power(1 - roc[:, 3], 2)
    # i2 = np.argmin(v2)
    # print(i2*0.1)
    # print(np.sum(r_Pb > i2*0.1)/r_Pb.shape[0])

    plt.figure()
    plt.hist(x=r_null, bins=180, color=(0, 1, 0, 0.3),label="null",
             density=True)
    plt.hist(x=r_Pb, bins=180, color=(1, 0, 0, 0.3), label="Pb",
             density=True)
    plt.legend()
    # plt.savefig(os.path.join('./res/2020-12-1/','ScatteringDensity_%d_min.png'%timeIndex), dpi=600)
    # plt.show()
    # plt.close()

    # plt.figure(dpi = 600)
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.suptitle('threshold: %.4f, confidence:%.4f'%(i*0.1, np.sum(r_Pb > i*0.1)/r_Pb.shape[0]))
    ax.plot(roc[:,1],roc[:,0],'b--',marker="x", label="TP-FP")
    ax.plot(roc[:, 3], roc[:, 2], 'r--', marker="x", label="TN-FN")
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 1)
    ax.legend()
    # fig.savefig(os.path.join('./res/2020-12-1/','ROC_time_%d_min.png'%timeIndex), dpi=600)
    plt.show()
    print()
    # plt.close()
    # pos_Pb = PocaPosition(data=data_Pb)
    # pos_null = PocaPosition(data_null)
    #
    # angle_Pb = pos_Pb[(pos_Pb[:, 0] > 100) & (pos_Pb[:, 0] < (650 - 100)) &
    #                                  (pos_Pb[:, 1] > 100) & (pos_Pb[:, 1] < (650 - 100)) &
    #                                  (pos_Pb[:, 2] < 900) & (pos_Pb[:, 2] > 600),3]
    # angle_null = pos_null[(pos_null[:, 0] > 100) & (pos_null[:, 0] < (650 - 100)) &
    #                                  (pos_null[:, 1] > 100) & (pos_null[:, 1] < (650 - 100)) &
    #                                  (pos_null[:, 2] < 900) & (pos_null[:, 2] > 600),3]
    # def func0(angle:np.array,cutLine:float):
    #     idx = angle < cutLine
    #     a0 = np.sum(idx)
    #     a1 = np.sum(~idx)
    #     return a1/a0
    # result_Pb = np.empty((180,))
    # result_null = np.empty((180,))
    # for i in tqdm(range(180)):
    #     result_Pb[i] = func0(angle_Pb,i/2)
    #     result_null[i] = func0(angle_null, i / 2)
    #
    #
    # plt.figure()
    # plt.hist(x=result_null[result_null>1e-10 & result_null<1], bins=180, color=(0, 1, 0, 0.3),label="null",
    #          density=True)
    # plt.hist(x=result_Pb[result_Pb>1e-10 & result_Pb<1], bins=180, color=(1, 0, 0, 0.3), label="Pb",
    #          density=True)
    # plt.legend()
    # plt.show()
    # plt.close()


    # def calculateTheta(data:pd.DataFrame):
    #     a0 = pocaAnalizy(data)
    #     pos = a0.HitPositions
    #     def getTheta(event:np.array):
    #         '''
    #
    #         :param hit: (4,3)
    #         :return:
    #         '''
    #         inVector = (event[1] - event[0])
    #         outVector = (event[3] - event[2])
    #         midVector = (event[2] - event[1])
    #         longSide = event[2] - event[0]
    #
    #         projection = np.array([0, 2])
    #         normal_x = np.array([1, 0, 0])# (x,z)
    #         normal_y = np.array([0, 1, 0])
    #         normal_z = np.array([0, 0, 1])
    #
    #
    #
    #         in_long = np.dot(longSide[projection], inVector[projection])
    #         out_long = np.dot(longSide[projection], outVector[projection])
    #         in_out = np.dot(inVector[projection], outVector[projection])
    #         in_mid = np.dot(inVector[projection],midVector[projection])
    #         mid_out = np.dot(midVector[projection],outVector[projection])
    #         in_in = np.dot(inVector[projection], inVector[projection])
    #         out_out = np.dot(outVector[projection], outVector[projection])
    #         mid_mid = np.dot(midVector[projection],midVector[projection])
    #
    #
    #         # 计算夹角
    #         # 单位：°
    #         # theta = np.arccos(np.sqrt((in_out * in_out) / (in_in * out_out))) * 180 / np.pi
    #         # theta_0 = np.arccos(np.sqrt((in_mid * in_mid) / (in_in * mid_mid))) * 180 / np.pi
    #         # theta_1 = np.arccos(np.sqrt((mid_out * mid_out) / (mid_mid * out_out))) * 180 / np.pi
    #
    #         #
    #         theta_0 = np.arccos((np.dot(normal_x[projection],inVector[projection]) / np.sqrt(in_in)))
    #         theta_1 = np.arccos((np.dot(normal_x[projection],midVector[projection]) / np.sqrt(mid_mid)))
    #         theta_2 = np.arccos((np.dot(normal_x[projection],outVector[projection]))/ np.sqrt(out_out))
    #
    #         # idx = np.array([[0,1]])
    #         # theta_x_0 = np.arccos(np.sqrt([0,]))
    #
    #         # 计算poca点
    #         if in_in < 1e-4:
    #             t1 = in_long / in_in
    #             t2 = - out_long / out_out
    #         else:
    #             t1 = (in_out * out_long - out_out * in_long) / (in_out ** 2 - in_in * out_out)
    #             t2 = in_in / in_out * t1 - (in_long / in_out)
    #         return *((event[0] + t1 * inVector) + (event[2] + t2 * outVector)) / 2, theta_0,theta_1,theta_2
    #
    #
    #     result = np.empty((pos.shape[0],6))
    #     for i in tqdm(range(pos.shape[0])):
    #         result[i,:] = np.array(getTheta(pos[i]))
    #
    #     return result
    #

    # theta_Pb = calculateTheta(data_Pb)
    # theta_Pb = theta_Pb[(theta_Pb[:, 0] > 100) & (theta_Pb[:, 0] < (650 - 100)) &
    #                         (theta_Pb[:, 1] > 100) & (theta_Pb[:, 1] < (650 - 100)) &
    #                         (theta_Pb[:, 2] < 900) & (theta_Pb[:, 2] > 600)]
    # theta_null = calculateTheta(data_null)
    # theta_null = theta_null[(theta_null[:, 0] > 100) & (theta_null[:, 0] < (650 - 100)) &
    #                   (theta_null[:, 1] > 100) & (theta_null[:, 1] < (650 - 100)) &
    #                   (theta_null[:, 2] < 900) & (theta_null[:, 2] > 600)]
    # idx = np.array([[1,0],[2,1]])
    # for i in idx:
    #     plt.figure()
    #     plt.hist(x=theta_null[:,3+i[0]] - theta_null[:,3+i[1]],bins=180,color=(1,0,0,0.3),label="theta_null_{}-{}".format(*i),density=True)
    #     plt.hist(x=theta_Pb[:,3+i[0]] - theta_Pb[:,3+i[1]],bins=180,color=(0,1,0,0.3),label="theta_Pb_{}-{}".format(*i),density=True)
    #     plt.legend()
    #     plt.show()
    #     plt.close()
    # plt.figure()
    # plt.hist(x=theta_Pb[:, 3 + idx[0,0]] - theta_Pb[:, 3 + idx[0,1]], bins=180, color=(1, 0, 0, 0.3),
    #          label="theta_Pb_{}-{}".format(*idx[0]), density=True)
    # plt.hist(x=theta_Pb[:, 3 + idx[1,0]] - theta_Pb[:, 3 + idx[1,1]], bins=180, color=(0, 1, 0, 0.3),
    #          label="theta_Pb_{}-{}".format(*idx[1]), density=True)
    # plt.legend()
    # plt.show()
    # plt.close()

