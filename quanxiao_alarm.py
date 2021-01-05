"""
这里要作的事情：
1.将有铅砖的PoCA数据按照时间切片，切割成30s，60s，90s，120s的不同小段
for item in each slice:
    1).分别沿着三个维度进行投影、分割、并通过std计算theta的sigma，确定要选择的体素区间
    2)根据选择的体素空间，计算出theta的sigma^2，得到散射密度的一个数据点
2.使用无铅砖的PoCA数据，重复上面的操作，同样得到四组散射密度数据曲线
3.步进提高阈值（将整个横坐标分成20/50段），按照阈值以上的数据点比例，确定True-Positive和False-Positive
4.我们首先是希望有较高的True-Positive，其次是保证足够低的False-Positive，所以要在不同的切片数据曲线上来回跳动，
在条件允许的情况下得到想要的结果。
"""
import os

import h5py
import numpy as np
import matplotlib.pyplot as plt
import time
from tqdm import trange
import random

fname1 = os.path.join('./res/2020-12-1/','bg.txt')
measure_time1 = 14701.
fname2 = os.path.join('./res/2020-12-1/','pb.txt')
measure_time2 = 46620.
#
# datab = np.loadtxt(fname1, delimiter=",", skiprows=1, usecols=(4))
# # 首先确认出一个合适的本底角度分布归一化曲线
# background_data_num = np.sum((datab > 2.5) & (datab < 10))/ datab.shape[0]
# print(background_data_num)
# # 其次，从本底数据或者从有铅砖的数据里，取一段时间的数据，确定出2.5~10度的中间数据量差异。
# # 执行多次这样的操作，得到直方图。然后不断提高阈值，得到ROC曲线。
# def segment_data_and_caculate_diff(fname, measure_time, slicetime:int = 60, num:int = 200):
#     PoCA_Data = np.loadtxt(fname, dtype=float, usecols=(4), delimiter=",", skiprows=1)
#     slice_cell = int(PoCA_Data.shape[0] / measure_time * slicetime)
#     data = []
#     for i in trange(num):
#         slice_index = random.randint(0, PoCA_Data.shape[0] - slice_cell)
#         data.append(PoCA_Data[slice_index:slice_index + slice_cell])
#     data = np.asarray(data).reshape(num, slice_cell)  # shape(num,slice_cell)
#     # 下面对已经实现了时间切片的数据进行了voxel的空间切分
#     return np.sum((data > 2.5) & (data < 10), axis=1) / slice_cell - background_data_num
#
# data1_diff = segment_data_and_caculate_diff(fname1, measure_time1, slicetime=1200, num=10000)
# data2_diff = segment_data_and_caculate_diff(fname2, measure_time2, slicetime=1200, num=10000)
#
# plt.figure()
# plt.hist(data1_diff, bins=30, histtype='step', label="no_pb")
# plt.hist(data2_diff, bins=30, histtype='step', label="pb_bricks")
# plt.legend()
# plt.show()

def alarm(fname, measure_time, timeslice:int = 60, num:int = 100):
    PoCA_Data = np.loadtxt(fname, dtype=float, delimiter=",")
    # print(PoCA_Data.shape)
    # 接下来对数据进行切片，构建出合乎处理方式的array形式
    slice_cell = int(PoCA_Data.shape[0] / measure_time * timeslice)
    data = []
    for i in range(num):
        slice_index = random.randint(0, PoCA_Data.shape[0] - slice_cell)
        data.append(PoCA_Data[slice_index:slice_index + slice_cell, :])
    data = np.asarray(data).reshape(num, slice_cell, 4)  # shape(num,slice_cell, 4)
    # data = PoCA_Data[:slice_cell * num, :].reshape(num, slice_cell, 4)  # shape(num,slice_cell,4)
    final_data = []
    for slice_data in data:  # shape(num,slice_cell,4) ----> shape(slice_cell,4)
        condition = ((slice_data[:, 0] > 325-50) & (slice_data[:, 0] < 325+50) &
                     (slice_data[:, 1] > 325-50) & (slice_data[:, 1] < 325+50) &
                     (slice_data[:, 2] > 650) & (slice_data[:, 2] < 800))
        slice_data = slice_data[condition]
        sigma_theta = np.average(np.power(slice_data[:, 3], 2))/100
        final_data.append(sigma_theta)
    final_data = np.asarray(final_data)
    # 进行ROC的曲线绘制
    n, bins = np.histogram(final_data, bins=120, range=(0, 10))
    bins = (bins[1:] + bins[:-1]) / 2
    return final_data, n ,bins

def diff_time(time, num):
    final_data1, n1, bins1 = alarm(fname1, measure_time=measure_time1, timeslice=time, num=num)
    final_data2, n2, bins2 = alarm(fname2, measure_time=measure_time2, timeslice=time, num=num)
    # plt.figure()
    # plt.hist(final_data1, bins=120, range=(0,10), histtype='step', label=fname1)
    # plt.hist(final_data2, bins=120, range=(0,10), histtype='step', label=fname2)
    # plt.legend()
    TP = []
    FP = []
    Threshold = []
    for i in range(len(n1)):
        FP.append(np.sum(n1[i:]) / np.sum(n1))
        TP.append(np.sum(n2[i:]) / np.sum(n2))
        Threshold.append(bins1[i])
    return np.asarray(FP), np.asarray(TP), np.asarray(Threshold)
#
# FP1, TP1, TH1 = diff_time(60, 1000)
# FP2, TP2, TH2 = diff_time(120, 1000)
# FP3, TP3, TH3 = diff_time(240, 1000)
# FP4, TP4, TH4 = diff_time(600, 1000)
#
# plt.figure()
# plt.plot(FP1, TP1, 'b--',marker="x", label="60s")
# plt.plot(FP2, TP2, 'r--',marker="x", label="120s")
# plt.plot(FP3, TP3, 'g--',marker="x", label="240s")
# plt.plot(FP4, TP4, 'y--',marker="x", label="480s")
# plt.xlabel("Flase-Positive")
# plt.ylabel("True-Positive")
# plt.legend()
# plt.title("Receiver Operating Characteristic Curve")
# plt.show()




tr = []
tp = []
fp = []
for i in trange(10):
    FP2, TP2, TH2 = diff_time(600, 1000)
    FP2_sliced = FP2[FP2>0.05].shape[0] - 0
    tr.append(TH2[FP2_sliced])
    tp.append(TP2[FP2_sliced])
    fp.append(FP2[FP2_sliced])
    # print('120 s threshold: ',TH2[FP2_sliced])
    # print('120 s TP: ',TP2[FP2_sliced])
    # print('120 s FP: ',FP2[FP2_sliced])
plt.figure()
plt.hist(tr, bins=100, label="tr")
plt.legend()

plt.figure()
plt.hist(tp, bins=100, label="tp")
plt.legend()

plt.figure()
plt.hist(fp, bins=100, label="fp")
plt.legend()

plt.show()