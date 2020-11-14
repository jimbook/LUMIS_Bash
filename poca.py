#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 22 2020

@author: niqk
首先 实例化 MuonEvent 并对每一个event 处理以获的 initial positions
得到一个 MuonEvent.POCA_List()：List
其中每一项为一个 numpy array：
[x0, y0, z0, ........x3, y3, z3] size = 1 * 12
再实例化 POCA_Analysis()
将MuonEvent.POCA_List() 中每一项 传进 POCA_Analysis.run_poca()
全部完成得到一个 CPA list
"""
# import modin.pandas as pd
# import seaborn as sns
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

from dataLayer.baseCore import h5Data

# __all__ = ['h5Data','shareStorage']
# -----------数据索引-----------
_Index = []
basicpath = 'tmpStorage'#r'/Users/niqk/ownCloud/kemianqin/muon/Algorithm/face_to_object/'
for i in range(36):
    _Index.append('chn_{:2>d}'.format(i))
_Index.append('temperature')
_Index.append('triggerID')
_Index.append('boardID')

chnList = []
for i in range(0, 36, 1):
    chnList.append("chn_" + str(i))
chnList.append('boardID')

def linear_fit_fun(x, a1, a2):  # 定义拟合函数形式
    return a1 * x + a2

def err(p, x, y):
    return p[0] * x ** 2 + p[1] * x + p[2] - y

def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept

class POCA_Analysis(object):
    """POCA analysis for muon positions"""

    def __init__(self):
        self.CPA_List = []
        self.MSC_List = []
        filename = sys.argv[0]
        dirname = os.path.dirname(filename)
        _temppath = os.path.abspath(dirname) + '/res/'
        print(_temppath)
        if not os.path.exists(_temppath):
            os.mkdir(_temppath)
        _today = datetime.date.today()
        self.res_path = _temppath + '/' + str(_today)
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

    def run_poca(self, _df: pd.DataFrame):
        self.get_basic_2(_df)
        theta = self.get_angle()
        # if abs(theta) < 10:
        self.MSC_List.append(theta)
        cpa = self.get_cpa()
        self.CPA_List.append(cpa)

    def get_basic(self, _df: pd.DataFrame):
        self.p0 = _df.iloc[0, 0:3]
        self.p1 = _df.iloc[0, 3:6]
        self.p2 = _df.iloc[0, 6:9]
        self.p3 = _df.iloc[0, 9:12]
        self.u = (self.p1 - self.p0) / np.linalg.norm(self.p1 - self.p0)  # incoming vector
        self.v = (self.p3 - self.p2) / np.linalg.norm(self.p3 - self.p2)  # outgoing vector
        self.w0 = self.p0 - self.p1
        self.a = np.dot(self.u, self.u)
        self.b = np.dot(self.u, self.v)
        self.c = np.dot(self.v, self.v)
        self.d = np.dot(self.u, self.w0)
        self.e = np.dot(self.v, self.w0)

    def get_basic_2(self, _df):
        self.p0 = np.array([_df[0], _df[1], _df[2]])
        self.p1 = np.array([_df[3], _df[4], _df[5]])
        self.p2 = np.array([_df[6], _df[7], _df[8]])
        self.p3 = np.array([_df[9], _df[10], _df[11]])
        self.u = (self.p1 - self.p0) / np.linalg.norm(self.p1 - self.p0)  # incoming vector
        self.v = (self.p3 - self.p2) / np.linalg.norm(self.p3 - self.p2)  # outgoing vector
        self.w0 = self.p0 - self.p2
        self.a = np.dot(self.u, self.u)
        self.b = np.dot(self.u, self.v)
        self.c = np.dot(self.v, self.v)
        self.d = np.dot(self.u, self.w0)
        self.e = np.dot(self.v, self.w0)

    def get_cpa(self):
        D = np.dot(self.a, self.c) - np.dot(self.b, self.b)
        if D < 1e-4:
            self.sc = 0
            if self.b > self.c:
                self.tc = self.b / self.c
            else:
                self.tc = self.e / self.c
        else:
            self.sc = (np.dot(self.b, self.e) - np.dot(self.c, self.d)) / D
            self.tc = (np.dot(self.a, self.e) - np.dot(self.b, self.d)) / D
        dP = self.w0 + (self.u * self.sc) - (self.v * self.tc)
        return self.p0 + (self.u * self.sc) - (dP * self.sc)

    def get_angle(self):
        costheta = np.dot(self.u, self.v) / np.linalg.norm(self.u) * np.linalg.norm(self.v)
        sintheta = math.sqrt(1 - costheta ** 2)
        thetaR = math.asin(sintheta)
        theta = thetaR * 180 / math.pi
        return theta

    def poca_imaging(self):
        """poca points imaging"""
        # _data = np.array(np.concatenate(self.CPA_List, ignore_index=True).to_list()).reshape(len(self.CPA_List), 3)
        _data = np.array(np.concatenate(self.CPA_List)).reshape(len(self.CPA_List), 3)
        np.savetxt(os.path.join(self.res_path, 'data.csv'), _data, delimiter=',')
        _data = pd.DataFrame(_data, columns=['x', 'y', 'z'])
        # _data = _data[_data.iloc[:, 0] >= 0]
        # _data = _data[_data.iloc[:, 1] >= 0]
        # _data = _data[_data.iloc[:, 2] >= 40]
        # _data = _data[_data.iloc[:, 0] <= 49.5]
        # _data = _data[_data.iloc[:, 1] <= 49.5]
        fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(12, 6))
        fig.suptitle('POCA')
        ax[0].hist2d(_data.iloc[:, 0], _data.iloc[:, 1], bins=[100, 100])
        ax[0].set_title('x-y')
        ax[0].set_ylabel('y')
        ax[0].set_xlim(0, 50)
        ax[0].set_xlabel('x')
        ax[0].set_ylim(0, 50)
        ax[1].hist2d(_data.iloc[:, 0], _data.iloc[:, 2], bins=[100, 100])
        ax[1].set_title('x-z')
        ax[1].set_ylabel('z')
        ax[1].set_xlim(0, 50)
        ax[1].set_xlabel('x')
        ax[1].set_ylim(40, 90)
        ax[2].hist2d(_data.iloc[:, 1], _data.iloc[:, 2], bins=[100, 100])
        ax[2].set_title('y-z')
        ax[2].set_ylabel('z')
        ax[2].set_xlim(0, 50)
        ax[2].set_xlabel('y')
        ax[2].set_ylim(40, 90)
        plt.show()
        fig.savefig(os.path.join(self.plt_path, 'poca.png'), dpi=600)

class MuonEvent(object):
    """analysis individual muon events"""
    Status: str
    _event_id: int

    def __init__(self, _basicpath: str, **kwargs):
        """
        @type _basicpath: str
        @type data: pd.DataFrame()
        @type data_useful: pd.DataFrame()
        """
        global st
        # below are basic important files
        # self.layer_distance = [0, 3.5, 40.5, 44, 101, 104.5, 141.5, 145]
        self.layer_distance = [0, 3.5, 40.5, 44, 101, 104.5, 141.5, 145]
        self.bl = pd.read_csv(os.path.join(_basicpath, 'bl.csv'), sep=',', index_col=0, header=0)
        self.tr = pd.read_csv(os.path.join(_basicpath, 'tr.csv'), sep=',', index_col=0, header=0)
        self.mean_scale = pd.read_csv(os.path.join(_basicpath, 'mean_scale.csv'), sep=',', index_col=0, header=0)
        self.bl = self.bl.iloc[:, 0:32].mul(self.mean_scale.iloc[:, 0:32])
        self.tr = self.tr.iloc[:, 0:32].mul(self.mean_scale.iloc[:, 0:32])
        # below are important Lists
        self.BadEventList = []
        self.GoodCandidateList = []
        self.NotLinerList = []
        self.NLTest = []
        self.M_F_diffList = []
        self.M_F_diffList_scaled = []
        self.G_E_ID_List = []
        self.MIList = []
        self.PositionList = []
        self.MultiFired = []
        self.Not_8_Layer = []
        self.NotNeibourFired = []
        self.POCA_List = []
        self.CPA_List = []
        # initialize some properties
        self.data = pd.DataFrame()
        self.data_useful = pd.DataFrame()
        self.res = pd.DataFrame()
        self.POCA_input = pd.DataFrame(np.zeros([6, 3]), columns=['x', 'y', 'z'])
        self.system_check = 1
        self.SysList = []

        if kwargs.get("res_path") is not None:
            self.res_path = kwargs.get("res_path")
            if not os.path.exists(self.res_path):
                os.mkdir(self.res_path)
            self.plt_path = self.res_path + '/plts/'
            if not os.path.exists(self.plt_path):
                os.mkdir(self.plt_path)
        else:
            filename = sys.argv[0]
            dirname = os.path.dirname(filename)
            _TempPath = os.path.abspath(dirname) + '/res/'
            print(_TempPath)
            if not os.path.exists(_TempPath):
                os.mkdir(_TempPath)
            _today = datetime.date.today()
            self.res_path = _TempPath + '/' + str(_today)
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
        print('All results/ figures will be saved to:\n\t', self.plt_path)

    def load_event(self, _data: pd.DataFrame, **kwargs):
        """
            main function for analysis individual events
        """
        if kwargs.get('system_check'):
            # if some one wants to check the different distribution, set system_check = any number but not 1
            self.system_check = kwargs.get('system_check')
        _eid = _data.loc[0, 'triggerID']
        self._event_id = _eid
        #@tianh:检查是否由八层
        if _data.shape[0] == 8:
            self.Status = 'Good'
            # print('passed first check')
        else:
            self.Not_8_Layer.append(_data)
            self.Status = 'Err'
            self.BadEventList.append(_data.iloc[0, 37])
            return
        # @tianh:替换坏道
        for bid in range(8):
            if bid == 0:
                _data.iloc[bid, 9] = _data.iloc[bid, 32]
            elif bid == 1:
                _data.iloc[bid, 21] = _data.iloc[bid, 32]
            elif bid == 2:
                _data.iloc[bid, 11] = _data.iloc[bid, 32]
        # 用平均值法均一化
        self.data = _data.iloc[:, 0:32].mul(self.mean_scale.iloc[:, 0:32])  # scale the data
        _temp_data_threshold_info = self.data - self.tr.iloc[:, 0:32] # @tianh:将小于阈值的置零
        _temp_data_threshold_info[_temp_data_threshold_info <= 0] = 0
        _temp_data_threshold_info[_temp_data_threshold_info > 0] = 1
        self.data = self.data.mul(_temp_data_threshold_info)  # greater than threshold
        self.data = self.data - self.bl.iloc[:, 0:32]
        self.data[self.data <= 0] = 0

        # 检查事件是否符合条件1~2个bar触发
        if self.Status == 'Good':
            self.data["hits"] = 32 - self.data.apply(lambda s: s.value_counts().get(key=0, default=0), axis=1)
            # print(time.time()-st)
            """
            the code below is check if this event is a good candidate
                and if yes, minus baseline
            """
            if 2 >= self.data["hits"].mean() >= 1:
                self.Status = 'Good'
                self.data_useful = self.data.iloc[:, 0:32]

            else:
                self.MultiFired.append(_data)
                self.Status = 'Err'
                self.BadEventList.append(self._event_id)
                return
        if self.Status == 'Good':
            temp = self.data_useful.replace(0, np.nan).abs()
            np_temp_max = np.array(temp.replace(np.nan, 0))
            np_temp_min = np.array(temp.replace(np.nan, 1000))
            self.res = pd.DataFrame()
            self.res['max'] = temp.max(axis=1)
            self.res['min'] = temp.min(axis=1)
            self.res['max_index'] = np.argmax(np_temp_max, axis=1)
            self.res['min_index'] = np.argmin(np_temp_min, axis=1)
            self.res['chn_diff'] = (self.res['max_index'] - self.res['min_index']).abs()
            _checkpoint = self.res['chn_diff'].drop_duplicates(keep='first')
            _checkpoint = _checkpoint[_checkpoint != 0]
            _checkpoint = _checkpoint[_checkpoint != 1].to_numpy()
            # print(_checkpoint)
            #检查事件是否符合条件两个bar触发时必须相邻
            if len(_checkpoint) != 0:
                self.NotNeibourFired.append(_data)
                self.Status = 'Err'
                self.BadEventList.append(self._event_id)
                return
            else:
                # print('passed 3rd check')
                if self.res.isnull().values.any():
                    self.Status = 'Err'
                    self.BadEventList.append(self._event_id)
                    return
                self.get_zero_position()
                # 开始计算poca点
                if self.Status == 'Good':
                    self.res['eventID'] = self._event_id
                    if self.system_check == 1:
                        self.POCA_List.append(self.generate_poca_inputs())
                    else:
                        self.res['fitted'] = 0
                        self.SystemCheck()
                    self.GoodCandidateList.append(self.res)

    def SystemCheck(self):
        # 0/2 -x 1/3 -y
        # 4/6 -x 5/7 -y
        _x = [self.res.loc[0, 'position'], self.res.loc[2, 'position'], self.res.loc[4, 'position'],
              self.res.loc[6, 'position']]
        _x_z = [self.res.loc[0, 'z'], self.res.loc[2, 'z'], self.res.loc[4, 'z'], self.res.loc[6, 'z']]
        a_x, b_x = rsquared(_x, _x_z)
        _y = [self.res.loc[1, 'position'], self.res.loc[3, 'position'], self.res.loc[5, 'position'],
              self.res.loc[7, 'position']]
        _z_y = [self.res.loc[1, 'z'], self.res.loc[3, 'z'], self.res.loc[5, 'z'], self.res.loc[7, 'z']]
        a_y, b_y = rsquared(_y, _z_y)

        for _i in range(0, 8, 2):
            self.res.loc[_i, 'fitted'] = (self.res.loc[_i, 'z'] - b_x) / a_x
            self.res.loc[_i + 1, 'fitted'] = (self.res.loc[_i + 1, 'z'] - b_y) / a_y

    # 计算触发位置
    def get_zero_position(self):
        # 重组为dataframe
        self.res['max_Parity'] = self.res['max_index'] % 2
        self.res['left_chn'] = self.res['max_index'].ge(self.res['min_index'])
        self.res['boardID'] = 0
        self.res['position'] = 0
        self.res['z'] = 0
        for bid in range(8):
            self.res.loc[bid, 'boardID'] = bid
            d = self.res.loc[bid, 'max'] / (self.res.loc[bid, 'min'] + self.res.loc[bid, 'max']) * 1.5
            if self.res.loc[bid, 'chn_diff'] == 0:
                self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * 1.5 + 1.5
            else:
                if self.res.loc[bid, 'left_chn']:
                    self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * 1.5 + d
                else:
                    self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * 1.5 + 3 - d

            self.res.loc[bid, 'z'] = (self.layer_distance[bid]) + self.res.loc[bid, 'max_index'] % 2 * 1.5 + \
                                     (-1) ** self.res.loc[bid, 'max_index'] * d

    # 计算粒子径迹
    def generate_poca_inputs(self):
        # 0/2 -x 1/3 -y
        # 4/6 -x 5/7 -y
        _Cal_Range = [0, 1, 4, 5]
        wanted_z = [2.5, 43, 103.5, 144]
        _cpa = []

        for _i in range(len(_Cal_Range)):
            _x = [self.res.loc[_Cal_Range[_i], 'position'], self.res.loc[_Cal_Range[_i] + 2, 'position']]
            _y = [self.res.loc[_Cal_Range[_i], 'z'], self.res.loc[_Cal_Range[_i] + 2, 'z']]
            a, b = rsquared(_x, _y)
            if _Cal_Range[_i] < 4:
                _cpa.append((wanted_z[0] - b) / a)
                _cpa.append((wanted_z[1] - b) / a)
            else:
                _cpa.append((wanted_z[2] - b) / a)
                _cpa.append((wanted_z[3] - b) / a)
        if len(_cpa) == 8:
            _CPA = pd.DataFrame(np.zeros([3, 4]))
            _CPA.iloc[0, 0] = _cpa[0]
            _CPA.iloc[0, 1] = _cpa[1]
            _CPA.iloc[1, 0] = _cpa[2]
            _CPA.iloc[1, 1] = _cpa[3]
            _CPA.iloc[0, 2] = _cpa[4]
            _CPA.iloc[0, 3] = _cpa[5]
            _CPA.iloc[1, 2] = _cpa[6]
            _CPA.iloc[1, 3] = _cpa[7]
            for _i in range(4):
                _CPA.iloc[2, _i] = wanted_z[_i]
                return _CPA.T.to_numpy().reshape(1, 12)

    def resolution_plt(self):
        """check if measure - fit different list empty"""
        if not self.M_F_diffList:
            self.get_resolution_list()
        for _i in range(len(self.M_F_diffList)):
            df = pd.DataFrame(self.M_F_diffList[_i]).iloc[:, 0]
            df = df[df <= 3]
            df = df[df >= -3]
            df2 = df
            df2 = df2[df2 <= 1]
            df2 = df2[df2 >= -1]
            mu, std = norm.fit(df2)
            x = np.linspace(-3, 3, 1200)
            p = norm.pdf(x, mu, std)

            fig, ax = plt.subplots(figsize=(10, 8))
            ax.hist(df, bins=600, histtype='step', facecolor='green',
                    alpha=0.75, density=True, label='mean scale')
            ax.plot(x, p, 'k', linewidth=2, label=' mu  = %.4f\n std = %.4f' % (mu, std))

            ax.legend(loc='upper right')
            ax.grid(True)
            ax.set_xlabel('cm')
            ax.set_xlim(-2, 2)
            fig.suptitle('position resolution without iteration')
            fig.savefig(os.path.join(self.plt_path, 'resolution_%d.png' % _i), dpi=600)
            plt.show()

    def get_resolution_list(self, ):
        diffList1 = []
        GoodEventIDList = []
        Max_index_List = []
        posList = []
        for _i in range(len(self.GoodCandidateList)):
            df = self.GoodCandidateList[_i]
            caled1 = (df.loc[4, 'z'] - df.loc[4, 'b0']) / df.loc[4, 'tan0']
            meaed1 = df.loc[4, 'position']
            diffList1.append(meaed1 - caled1)
            GoodEventIDList.append(self.GoodCandidateList[_i].loc[0, 'eventID'])
            Max_index_List.append(self.GoodCandidateList[_i].loc[4, 'max_index'])
            posList.append(meaed1)

        self.M_F_diffList.append(diffList1)
        self.G_E_ID_List.append(GoodEventIDList)
        self.MIList.append(Max_index_List)
        self.PositionList.append(posList)

    def cross_check_resolution(self, lower_limit, upper_limit):
        """partically check resolution """
        diff_df = pd.DataFrame(self.M_F_diffList[0])  # get different list
        diff_df.reset_index(inplace=True)  # set index for each event
        diff_sliced = diff_df[diff_df.iloc[:, 1] > lower_limit]  # slice data and focus on (-1,0]
        diff_sliced = diff_sliced[diff_sliced.iloc[:, 1] <= upper_limit]
        diff_sliced.reset_index(drop=True, inplace=True)
        diff_sliced["chn"] = 0
        diff_sliced["position"] = 0
        diff_sliced["angle"] = 0

        templist1 = self.MIList[0]
        tempPL = self.PositionList[0]
        for _i in range(diff_sliced.shape[0]):
            index = int(diff_sliced.iloc[_i, 0])
            diff_sliced.loc[_i, 'chn'] = int(templist1[index])
            diff_sliced.loc[_i, 'position'] = tempPL[index]
            diff_sliced.loc[_i, 'angle'] = self.GoodCandidateList[index].loc[4, 'theta0']
        diff_sliced['zenith'] = 90 - np.abs(diff_sliced['angle'])

        fig, ax = plt.subplots(figsize=(10, 8))
        h = ax.hist2d(diff_sliced.iloc[:, 1], diff_sliced.iloc[:, 2],
                      bins=[int((upper_limit - lower_limit) * 10) + 1, 32], density=True)
        ax.set_title(
            'Measured - fit position difference in (%s,%s] vs channel number of board 4' % (lower_limit, upper_limit))
        ax.set_xlabel('Measured - fit position difference')
        ax.set_ylabel('channel number')
        fig.colorbar(h[3], ax=ax)
        fig.savefig(os.path.join(self.plt_path, 'chn_%s_%s.png' % (lower_limit, upper_limit)), dpi=600)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.hist2d(diff_sliced.iloc[:, 1], diff_sliced.iloc[:, 3], bins=[int((upper_limit - lower_limit) * 10) + 1, 48],
                  density=True)
        ax.set_title('Measured - fit position difference in (%s,%s] vs measured position of board 4' % (
            lower_limit, upper_limit))
        ax.set_xlabel('Measured - fit position difference')
        ax.set_ylabel('Measured position')
        fig.colorbar(h[3], ax=ax)
        fig.savefig(os.path.join(self.plt_path, 'meaed_%s_%s.png' % (lower_limit, upper_limit)), dpi=600)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.hist2d(diff_sliced.iloc[:, 1], 90 - np.abs(diff_sliced.iloc[:, 4]),
                  bins=[int((upper_limit - lower_limit) * 10) + 1, 30], density=True)
        ax.set_title(
            'Measured - fit position difference in (%s,%s] vs zenith angle of board 4' % (lower_limit, upper_limit))
        ax.set_xlabel('Measured - fit position difference')
        ax.set_ylabel('zenith angle in radian')
        fig.colorbar(h[3], ax=ax)
        fig.savefig(os.path.join(self.plt_path, 'zenith_%s_%s.png' % (lower_limit, upper_limit)), dpi=600)

        lower_lim = 0
        path = self.plt_path + '/zenith/'
        if not os.path.exists(path):
            os.mkdir(path)
        for _i in range(30):
            upper_lim = (_i + 1) * 0.01
            DiffTemp = diff_sliced[diff_sliced['zenith'] >= lower_lim]
            DiffTemp = DiffTemp[DiffTemp['zenith'] < upper_lim]
            fig, ax = plt.subplots()
            fig.suptitle('zenith_%.1f_%.1f.png' % (lower_lim, upper_lim))
            ax.hist(DiffTemp, bins=1200, density=True, label='[%.2f, %.2f)' % (lower_lim, upper_lim))
            ax.legend(loc='upper right')
            ax.set_xlim(-1, 1)
            fig.savefig(os.path.join(path, 'zenith_%.1f_%.1f.png' % (lower_lim, upper_lim)), dpi=600)
            lower_lim = upper_lim

    def layer_checker(self):
        for _i in range(len(self.Not_8_Layer)):
            pass

def mp_analysis(_basicpath, _data):
    global basicpath
    # print(basicpath)
    Event_analysis = MuonEvent(basicpath)
    _EventId = _data['triggerID'].drop_duplicates().to_list()
    for _event in tqdm(_EventId):
        _df = _data[_data['triggerID'] == _event].reset_index(drop=True)
        Event_analysis.load_event(_df)
    return Event_analysis

def Merge_class(x: MuonEvent, y: MuonEvent):
    x.BadEventList.extend(y.BadEventList)
    x.GoodCandidateList.extend(y.GoodCandidateList)
    x.NotLinerList.extend(y.NotLinerList)
    x.NLTest.extend(y.NLTest)
    x.M_F_diffList.extend(y.M_F_diffList)
    x.G_E_ID_List.extend(y.G_E_ID_List)
    x.MIList.extend(y.MIList)
    x.PositionList.extend(y.PositionList)
    x.MultiFired.extend(y.MultiFired)
    x.Not_8_Layer.extend(y.Not_8_Layer)
    x.NotNeibourFired.extend(y.NotNeibourFired)
    x.POCA_List.extend(y.POCA_List)
    x.CPA_List.extend(y.CPA_List)
    x.SysList.extend(y.SysList)
    return x

"""-------------------------------------------------------------------------"""
if __name__ == '__main__':

    st = time.time()
    HitFile = 'testData/h5Data/tempData_22_59_16.h5'#"/Users/niqk/ownCloud/kemianqin/muon/Algorithm/8_layer_test/data/tempData_22_59_16.h5"  # background data

    _data = h5Data(HitFile, 'r')
    data = _data.getData(0)
    result = MuonEvent(basicpath)
    EID_List = data['triggerID'].drop_duplicates().to_list()
    for eid in tqdm(EID_List, ):
        df = data[data['triggerID'] == eid].reset_index(drop=True)
        result.load_event(df)

