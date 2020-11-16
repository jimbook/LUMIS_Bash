#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 2020
poca algorithm
@author: niqk
将 Ratio 实例化 并传入cpa list
返回得到 RatioList
每一项为 x y z Angle Ratio
具体用法可看 show_2D（）
"""

import datetime
import math
import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm
from tqdm import tqdm
import random
# This import registers the 3D projection, but is otherwise unused.
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import numpy as np
from matplotlib import cm


def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept


class Ratio(object):
    """using Ratio Algorithm after get initial poca points
        input data: a dataframe poca_Data
        for each row:
        poca_x, poca_y, poca_z, theta ( angle), p1_x, p1_y, p1_z, p2_x, p2_y, p2_z
    """

    def __init__(self, poca_data :np.array, **kwargs):
        '''

        :param poca_data: shape(None,10)[poca_x, poca_y, poca_z, theta ( angle), p1_x, p1_y, p1_z, p2_x, p2_y, p2_z]
        :param kwargs:
        '''
        self.theta_cut = 0.9 # 大于这个的就扔掉
        self.amplification = 30000 # 循环次数
        self.cube_size = 5 # 探测区域的大小
        self.start_num = 0 # 开始点
        self.slice_point = 1 # 切分系数（切成几分）
        random.seed(time.time()) #
        self.data = poca_data
        self.RatioList = [] # 保存返回ratio点的仓库

        ## set a save path
        filename = sys.argv[0]
        dirname = os.path.dirname(filename)
        _temp = os.path.abspath(dirname) + '/res/'
        print(_temp)
        if not os.path.exists(_temp):
            os.mkdir(_temp)
        _today = datetime.date.today()
        self.res_path = _temp + '/' + str(_today)
        if not os.path.exists(self.res_path):
            os.mkdir(self.res_path)
        _hr = datetime.datetime.now().hour
        _minute = datetime.datetime.now().minute
        # print(_today)
        self.res_path = self.res_path + '/' + str(_hr) + '_' + str(_minute)
        if not os.path.exists(self.res_path):
            os.mkdir(self.res_path)
        self.plt_path = self.res_path + '/plts/'
        if not os.path.exists(self.plt_path):
            os.mkdir(self.plt_path)

    def generate_ratio_points(self, **kwargs):
        if kwargs.get('slice'):
            self.slice_point = kwargs.get('slice')

        if kwargs.get('start_num'):
            self.start_num = kwargs.get('start_num')

        if kwargs.get('cube_size'):
            self.cube_size = kwargs.get('cube_size')

        if kwargs.get('amplification'):
            self.amplification = kwargs.get('amplification')

        if kwargs.get('theta_cut'):
            self.theta_cut = kwargs.get('theta_cut')

        for _i in trange(int(self.amplification)):
            P_x = random.uniform(0, 49.5)  # x range
            P_y = random.uniform(0, 49.5)  # y range
            P_z = random.uniform(40, 90)  # z range for the detection area
            P_rand = np.array([P_x, P_y, P_z])
            # print(P_rand)
            self.poca_enhance(P_rand)

    def poca_enhance(self, P_rand):
        N_all = 0 # 分母（总共的事件数据）
        Cut_N = 0 #
        Angle_sigma = 0 # 散射角的平方
        endpoints = self.start_num + int(self.data.shape[0] / self.slice_point) # 结束点位置
        _temp = self.cube_size / 2
        for _i in range(self.start_num, endpoints):
            cpa = np.array([self.data[_i, 0], self.data[_i, 1], self.data[_i, 2]])  # the poca point
            Angle = self.data[_i, 3]  # the scattering angle of POCA point
            p0 = np.array([self.data[_i, 4], self.data[_i, 5], self.data[_i, 6]])  # the incoming point
            q0 = np.array([self.data[_i, 7], self.data[_i, 8], self.data[_i, 9]])  # the outgoing point
            # if Angle > 20:
            #     continue
            diff = cpa - P_rand # poca到生成点的矢量
            if abs(diff[0]) < _temp and abs(diff[1]) < _temp and abs(diff[2]) < _temp: # 生成点的探测区域内是否包含poca
                N_all += 1 #
                Angle = Angle * abs(1. - np.linalg.norm(diff) * 2. / self.cube_size / math.sqrt(3)) # 平滑处理
                Angle_sigma += Angle ** 2 # 角度平方的累加
                if Angle <= self.theta_cut:
                    Cut_N += 1
            else:
                if diff[2] < 0: # poca在探测区域上
                    line_u = cpa - p0 # 连线矢量
                    x_top = line_u[0] / line_u[2] * (P_rand[2] + self.cube_size / 2 - cpa[2]) + cpa[0] - P_rand[0]
                    x_low = line_u[0] / line_u[2] * (P_rand[2] - self.cube_size / 2 - cpa[2]) + cpa[0] - P_rand[0]
                    y_top = line_u[1] / line_u[2] * (P_rand[2] + self.cube_size / 2 - cpa[2]) + cpa[1] - P_rand[1]
                    y_low = line_u[1] / line_u[2] * (P_rand[2] - self.cube_size / 2 - cpa[2]) + cpa[1] - P_rand[1]
                    if x_top < _temp and x_low < _temp and y_top < _temp and y_low < _temp: # 连线是否过探测区
                        N_all += 1
                        Cut_N += 1
                else:# poca在探测区域下
                    line_d = q0 - cpa
                    x_top = line_d[0] / line_d[2] * (P_rand[2] + self.cube_size / 2 - cpa[2]) + cpa[0] - P_rand[0]
                    x_low = line_d[0] / line_d[2] * (P_rand[2] - self.cube_size / 2 - cpa[2]) + cpa[0] - P_rand[0]
                    y_top = line_d[1] / line_d[2] * (P_rand[2] + self.cube_size / 2 - cpa[2]) + cpa[1] - P_rand[1]
                    y_low = line_d[1] / line_d[2] * (P_rand[2] - self.cube_size / 2 - cpa[2]) + cpa[1] - P_rand[1]
                    if x_top < _temp and x_low < _temp and y_top < _temp and y_low < _temp: # 连线是否过探测区
                        N_all += 1
                        Cut_N += 1
        if N_all > int(100 * self.cube_size ** 2 * 0.01 / self.slice_point):  # check statistical validation
            self.RatioList.append(
                np.array([P_rand[0], P_rand[1], P_rand[2], math.sqrt(Angle_sigma / N_all), Cut_N / N_all]))
            """upload data: MSR_x, MSR_y, MSR_z, MSC, ratio"""

    def show_3D(self):
        pass

    def show_2D(self):

        MC_data = np.concatenate(self.RatioList, axis=0).reshape([len(self.RatioList), 5])
        MC_data = MC_data[MC_data[:, 4] < 0.95, :]
        X = MC_data[:, 0]
        Y = MC_data[:, 1]
        Z = MC_data[:, 2]
        PoCA = MC_data[:, 3]
        Ratio = MC_data[:, 4]
        sca_P = np.sqrt((PoCA - np.min(PoCA)) / (np.max(PoCA) - np.min(PoCA))) * 40.
        sca_R = np.sqrt((np.max(Ratio) - Ratio) / (np.max(Ratio) - np.min(Ratio))) * 40.
        fig, ax = plt.subplots(2, 3, figsize=(12, 8))
        fig.suptitle('Lanzhou University Muon Imaging System, upper: MSR/PoCA, lower: Ratio')
        cbar1 = ax[0, 0].scatter(X, Y, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar1, ax=ax[0, 0])
        ax[0, 0].grid(True)
        ax[0, 0].set_xlim(0, 50)
        ax[0, 0].set_ylim(0, 50)
        ax[0, 0].set_xlabel('x (cm)')
        ax[0, 0].set_ylabel('y (cm)')
        cbar2 = ax[0, 1].scatter(X, Z, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar2, ax=ax[0, 1])
        ax[0, 1].grid(True)
        ax[0, 1].set_xlim(0, 50)
        ax[0, 1].set_ylim(40, 90)
        ax[0, 1].set_xlabel('x (cm)')
        ax[0, 1].set_ylabel('z (cm)')
        cbar3 = ax[0, 2].scatter(Y, Z, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar3, ax=ax[0, 2])
        ax[0, 2].grid(True)
        ax[0, 2].set_xlim(0, 50)
        ax[0, 2].set_ylim(40, 90)
        ax[0, 2].set_xlabel('x (cm)')
        ax[0, 2].set_ylabel('z (cm)')
        ################# ratio below
        cbar4 = ax[1, 0].scatter(X, Y, s=sca_R, c=Ratio, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar4, ax=ax[1, 0])
        ax[1, 0].grid(True)
        ax[1, 0].set_xlim(0, 50)
        ax[1, 0].set_ylim(0, 50)
        ax[1, 0].set_xlabel('x (cm)')
        ax[1, 0].set_ylabel('y (cm)')
        cbar5 = ax[1, 1].scatter(X, Z, s=sca_R, c=Ratio, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar5, ax=ax[1, 1])
        ax[1, 1].grid(True)
        ax[1, 1].set_xlim(0, 50)
        ax[1, 1].set_ylim(40, 90)
        ax[1, 1].set_xlabel('x (cm)')
        ax[1, 1].set_ylabel('z (cm)')
        cbar6 = ax[1, 2].scatter(Y, Z, s=sca_R, c=Ratio, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # colorbar and other settings
        fig.colorbar(cbar6, ax=ax[1, 2])
        ax[1, 2].grid(True)
        ax[1, 2].set_xlim(0, 50)
        ax[1, 2].set_ylim(40, 90)
        ax[1, 2].set_xlabel('x (cm)')
        ax[1, 2].set_ylabel('z (cm)')

        fig.savefig(os.path.join(self.path, 'poca_plt.png'), dpi=600)


from tqdm import trange

if __name__ == '__main__':
    from poca import POCA_Analysis
    analysis = POCA_Analysis()
    data = pd.read_csv('tmpStorage/poca_data2.csv', index_col=0)
    for i in trange(data.shape[0]):
        _df = data.iloc[i, :].to_numpy()
        analysis.run_poca(_df)
    data = np.concatenate(analysis.CPA_List, axis=0).reshape([len(analysis.CPA_List), 10])
    np.savetxt(os.path.join(analysis.res_path, 'poca.csv'), data, delimiter=",")
    ratio_test = Ratio(data)
    ratio_test.generate_ratio_points(start_num=1000, slice=2, amplification=10000)
    print()
    ratio_test.show_2D()