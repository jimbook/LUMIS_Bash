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
import time,copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm
from tqdm import tqdm
from matplotlib import cm
from dataLayer.baseCore import h5Data
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import sys

# __all__ = ['h5Data','shareStorage']
# -----------数据索引-----------
_Index = []
basicpath = 'tmpStorage'
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
        self.get_basic(_df)
        theta = self.get_angle()
        # if abs(theta) < 10:
        if math.isnan(theta):
            pass
        else:
            self.MSC_List.append(theta)
            cpa = self.get_cpa()
            self.CPA_List.append([cpa[0], cpa[1], cpa[2], theta,
                                  _df[3], _df[4], _df[5],
                                  _df[6], _df[7], _df[8]])

    def get_basic(self, _df):
        self.p0 = np.array([_df[0], _df[1], _df[2]])
        self.p1 = np.array([_df[3], _df[4], _df[5]])
        self.p2 = np.array([_df[6], _df[7], _df[8]])
        self.p3 = np.array([_df[9], _df[10], _df[11]])
        self.u = (self.p1 - self.p0)  # incoming vector
        self.v = (self.p3 - self.p2)  # outgoing vector
        self.w0 = self.p2 - self.p0
        self.a = np.dot(self.u, self.v)
        self.b = np.dot(self.u, self.u)
        self.c = np.dot(self.v, self.v)
        self.d = np.dot(self.w0, self.u)
        self.e = np.dot(self.w0, self.v)

    def get_cpa(self):
        if self.a == 0:
            t1 = self.d / self.b
            t2 = -self.e / self.c
        else:
            t1 = (self.a * self.e - self.c * self.d) / ( self.a ** 2 - self.b * self.c)
            t2 = self.b / self.a * t1 - self.d / self.a
        p0 = self.p0 + t1 * self.u
        q0 = self.p2 + t2 * self.v

        return (p0 + q0) / 2

    def get_angle(self):
        return math.acos(math.sqrt((self.a * self.a) / (self.b * self.c))) * 180 / math.pi

    def poca_imaging(self,data = None):
        """poca points imaging"""
        if data is None:
            print(len(self.CPA_List))
            _MC_data = np.concatenate(self.CPA_List, axis=0).reshape([len(self.CPA_List), 10])
        else:
            _MC_data = data
        _MC_data = _MC_data[_MC_data[:, 3] > 10, :]
        X = _MC_data[:, 0]
        Y = _MC_data[:, 1]
        Z = _MC_data[:, 2]
        PoCA = _MC_data[:, 3]
        sca_P = np.sqrt((PoCA - np.min(PoCA)) / (np.max(PoCA) - np.min(PoCA))) * 40.
        fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        fig.suptitle('Lanzhou University Muon Imaging System, Algorithm: PoCA')
        cbar1 = ax[0].scatter(X, Y, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        # ColorBar and other settings
        fig.colorbar(cbar1, ax=ax[0])
        ax[0].grid(True)
        ax[0].set_xlim(0., 650.)
        ax[0].set_ylim(0., 650.)
        ax[0].set_xlabel('x (mm)')
        ax[0].set_ylabel('y (mm)')
        cbar2 = ax[1].scatter(X, Z, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        fig.colorbar(cbar2, ax=ax[1])
        ax[1].grid(True)
        ax[1].set_xlim(0., 650.)
        ax[1].set_ylim(400, 900)
        ax[1].set_xlabel('x (mm)')
        ax[1].set_ylabel('z (mm)')
        cbar3 = ax[2].scatter(Y, Z, s=sca_P, c=PoCA, cmap=cm.jet, alpha=0.1, edgecolors='face')  # plotting
        fig.colorbar(cbar3, ax=ax[2])
        ax[2].grid(True)
        ax[2].set_xlim(0., 650.)
        ax[2].set_ylim(400, 900)
        ax[2].set_xlabel('y (mm)')
        ax[2].set_ylabel('z (mm)')
        plt.show()
        fig.savefig(os.path.join(self.plt_path, 'poca.png'), dpi=600)

    def show_3D_poca(self):
        _MC_data = np.concatenate(self.CPA_List, axis=0).reshape([len(self.CPA_List), 10])
        MC_data = _MC_data[_MC_data[:, 3] > 10, :]

        X_or = MC_data[:, 0]
        Y_or = MC_data[:, 1]
        Z_or = MC_data[:, 2]
        Scale_or = MC_data[:, 3]
        scale_max = np.max(Scale_or)
        scale_min = np.min(Scale_or)
        s_color = (Scale_or - scale_max) / (scale_max - scale_min)
        fig, ax = plt.subplot(projection='3d')
        ax.scatter(X_or, Y_or, Z_or, c=s_color, s=Scale_or, cmap=cm.jet, alpha=0.5, edgecolors='face')
        ax.set_xlim(0., 650.)
        ax.set_xlabel('X (mm)')
        ax.set_ylim(0., 650.)
        ax.set_ylabel('Y (mm)')
        ax.set_zlim(400., 1000.)
        ax.set_zlabel('Z (mm)')
        plt.show()

class AnalyzeMuonEvent(object):
    """analysis individual muon events"""
    Status: str
    _event_id: int

    def __init__(self, _basicpath: str, **kwargs):
        """
        @type _basicpath: str
        @type data: pd.DataFrame()
        @type data_useful: pd.DataFrame()
        """

        # below are basic important files
        # self.layer_distance = [0, 3.5, 40.5, 44, 101, 104.5, 141.5, 145] # in cm
        self.layer_distance = [0, 25.36 + 10.64, 405, 405 + 25.36 + 10.64,
                               1010, 1010 + 25.36 + 10.64, 1415, 1415 + 25.36 + 10.64]  # in mm
        self.layer_distance_np = np.array([0, 25.36 + 10.64, 405, 405 + 25.36 + 10.64,
                                           1010, 1010 + 25.36 + 10.64, 1415, 1415 + 25.36 + 10.64]).T
        self._x_list = [0, 2, 4, 6]
        self.bl = pd.read_csv(os.path.join(_basicpath, 'bl.csv'), sep=',', index_col=0, header=0)
        self.tr = pd.read_csv(os.path.join(_basicpath, 'tr.csv'), sep=',', index_col=0, header=0)
        self.mean_scale = pd.read_csv(os.path.join(_basicpath, 'mean_scale.csv'), sep=',', index_col=0, header=0)
        self.bl = self.bl.iloc[:, 0:32].mul(self.mean_scale.iloc[:, 0:32])
        self.tr = self.tr.iloc[:, 0:32].mul(self.mean_scale.iloc[:, 0:32])
        self.length = 30.72  # in mm
        self.half_length = self.length / 2
        # below are important Lists
        self.BadEventList = []
        self.GoodCandidateList = []
        self.PositionList = []
        self.MultiFired = []
        self.Not_8_Layer = []
        self.NotNeibourFired = []
        self.POCA_List = []
        self.CPA_List = []
        self.M_F_diffList = []
        # initialize some properties
        self.data = pd.DataFrame()
        self.data_useful = pd.DataFrame()
        self.res = pd.DataFrame()
        self.POCA_input = pd.DataFrame(np.zeros([6, 3]), columns=['x', 'y', 'z'])
        # self.system_check = 1
        # self.SysList = []
        self.Shift_Check_List = []  # check layer displacement shift
        for _i in range(8):
            _temp = []
            self.Shift_Check_List.append(_temp)

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

    def data_report(self, ):
        print('-----Statistic Report------')
        print('Not 8 layer events: %d;\nMultiFired Events: %d;\nNot Neibourhood bar Fired Event: %d;\n'
              % (len(self.Not_8_Layer), len(self.MultiFired), len(self.NotNeibourFired)))
        print('Vaild events: %d with in %d loaded events' % (len(self.GoodCandidateList),
                                                             (len(self.GoodCandidateList) + len(self.BadEventList))))

    def load_event(self, _data: pd.DataFrame):
        """
            main function for analysis individual events
        """
        # if kwargs.get('system_check'):
        #     self.system_check = kwargs.get('system_check')
        _eid = _data.loc[0, 'triggerID']
        self._event_id = _eid
        if _data.shape[0] == 8:  # check if 8 layers all exist
            self.Status = 'Good'
        else:
            self.Not_8_Layer.append(_data)
            self.Status = 'Err'
            self.BadEventList.append(_data.iloc[0, 37])
            return
        # shift wrong channel
        for bid in range(8):
            if bid == 0:
                _data.iloc[bid, 9] = _data.iloc[bid, 32]
            elif bid == 1:
                _data.iloc[bid, 21] = _data.iloc[bid, 32]
            elif bid == 2:
                _data.iloc[bid, 11] = _data.iloc[bid, 32]

        self.data = _data.iloc[:, 0:32]  # .mul(self.mean_scale.iloc[:, 0:32])  # scale the data
        _temp_data_threshold_info = self.data - self.tr.iloc[:, 0:32]  # get valid hit data
        _temp_data_threshold_info[_temp_data_threshold_info <= 0] = 0
        _temp_data_threshold_info[_temp_data_threshold_info > 0] = 1
        self.data = self.data.mul(_temp_data_threshold_info)  # greater than threshold
        self.data = self.data - self.bl.iloc[:, 0:32]  # minus baseline
        self.data[self.data <= 0] = 0

        if self.Status == 'Good':
            _temp = copy.deepcopy(self.data)  # avoid memory error
            _temp[_temp <= 0] = 0
            _temp[_temp > 0] = 1
            # self.data["hits"] = 32 - self.data.apply(lambda s: s.value_counts().get(key=0, default=0), axis=1)
            self.data["hits"] = _temp.sum(axis=1)
            del _temp
            """
            the code below is check if this event is a good candidate
                and if yes, minus baseline
            """
            if 2 >= self.data["hits"].mean() >= 1:  # check whether event has been multi fired or not
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
            _checkpoint = self.res['chn_diff'].drop_duplicates(keep='first')  # check if the fired bar are closed or not
            _checkpoint = _checkpoint[_checkpoint != 0]
            _checkpoint = _checkpoint[_checkpoint != 1].to_numpy()
            # print(_checkpoint)
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
                # self.get_zero_position()
                self.get_zero_position_numpy()
                if self.Status == 'Good':
                    self.res['eventID'] = self._event_id
                    aaa = self.generate_poca_inputs_np()
                    # bbb = self.generate_poca_inputs()
                    self.POCA_List.append(aaa)
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
        for _i in range(8):
            self.Shift_Check_List[_i].append(self.res.loc[_i, 'fitted'] - self.res.loc[_i, 'position'])

    def get_zero_position(self):
        # 重组为dataframe
        # the origin is the
        _shift = [-2.02264937, -0.789919915, 1.223523393, 1.296914005,
                  0.556464601, -0.417131352, 0.242661376, -0.089862738]
        _XMode = [0, 2, 4, 6]
        _YMode = [1, 3, 5, 7]
        self.res['max_Parity'] = self.res['max_index'] % 2
        self.res['left_chn'] = self.res['max_index'].ge(self.res['min_index'])
        self.res['boardID'] = 0
        self.res['position'] = 0
        self.res['z'] = 0
        for bid in range(8):
            self.res.loc[bid, 'boardID'] = bid
            d = self.res.loc[bid, 'max'] / (self.res.loc[bid, 'min'] + self.res.loc[bid, 'max']) * 15
            if bid in self._x_list:
                if self.res.loc[bid, 'chn_diff'] == 0:
                    self.res.loc[bid, 'position'] = (self.res.loc[bid, 'max_index'] + 1) * self.half_length + 71.56 - \
                                                    _shift[bid]
                    self.res.loc[bid, 'z'] = (self.layer_distance[bid]) + self.res.loc[
                        bid, 'max_Parity'] * self.half_length
                else:
                    if self.res.loc[bid, 'left_chn']:  # RIGHT CHANNEL > LEFT
                        self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * self.half_length + \
                                                        d + 71.56 - _shift[bid]
                    else:
                        self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * self.half_length + \
                                                        self.length - d + 71.56 - _shift[bid]
                    self.res.loc[bid, 'z'] = self.layer_distance[bid] + self.res.loc[
                        bid, 'max_index'] % 2 * self.half_length + (-1) ** self.res.loc[bid, 'max_index'] * d
            else:
                if self.res.loc[bid, 'chn_diff'] == 0:
                    self.res.loc[bid, 'position'] = (self.res.loc[bid, 'max_index'] + 1) * self.half_length + 71.24 - \
                                                    _shift[bid]
                    self.res.loc[bid, 'z'] = (self.layer_distance[bid]) + self.res.loc[
                        bid, 'max_Parity'] * self.half_length
                else:
                    if self.res.loc[bid, 'left_chn']:
                        self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * self.half_length + d + 71.24
                    else:
                        self.res.loc[bid, 'position'] = self.res.loc[bid, 'max_index'] * self.half_length + \
                                                        self.length - d + 71.24 - _shift[bid]
                    self.res.loc[bid, 'z'] = self.layer_distance[bid] + self.res.loc[bid, 'max_index'] % 2 * \
                                             self.half_length + (-1) ** self.res.loc[bid, 'max_index'] * d

    def get_zero_position_numpy(self):
        # 重组为dataframe
        # the origin is the

        _shift = np.array([-2.02264937, -0.789919915, 1.223523393, 1.296914005,
                  0.556464601, -0.417131352, 0.242661376, -0.089862738]).T
        _XMode = [0, 2, 4, 6]
        _YMode = [1, 3, 5, 7]
        self.res['max_Parity'] = self.res['max_index'] % 2
        self.res['left_chn'] = self.res['max_index'].ge(self.res['min_index'])
        self.res['temp'] = 0
        self.res['temp'] = self.res['max'] / (self.res['min'] + self.res['max']) * self.half_length
        self.res_np = np.array(self.res)
        self.np_res = np.zeros([8, 2])
        set_bar = self.res_np[_XMode, 2] * self.half_length
        en_offset = self.res_np[_XMode, 4] * ((-1) ** (self.res_np[_XMode, 6] - 1) * self.res_np[_XMode, 7])
        odd_offset = (self.res_np[_XMode, 4] - 1) ** 2 * self.half_length+(self.res_np[_XMode, 6] - 1) ** 2 * self.length
        geo_offset = 71.56 - _shift[_XMode]
        all = set_bar + en_offset + odd_offset + geo_offset

        self.np_res[_XMode, 0] = self.res_np[_XMode, 2] * self.half_length + 71.56 + \
                                 (self.res_np[_XMode, 4] - 1) ** 2 * self.half_length + \
                                 self.res_np[_XMode, 4] * \
                                 ((-1) ** (self.res_np[_XMode, 6] - 1) * self.res_np[_XMode, 7] + \
                                  (self.res_np[_XMode, 6] - 1) ** 2 * self.length) - _shift[_XMode]
        # 全都有的部分
        # chn diff = 0 的部分 + half length
        # # RIGHT CHANNEL > LEFT
        set_bar = self.res_np[_YMode, 2] * self.half_length
        en_offset = self.res_np[_YMode, 4] * ((-1) ** (self.res_np[_YMode, 6] - 1) * self.res_np[_YMode, 7])
        odd_offset = (self.res_np[_YMode, 4] - 1) ** 2 * self.half_length + (
                    self.res_np[_YMode, 6] - 1) ** 2 * self.length
        geo_offset = 71.24 - _shift[_YMode]
        all = set_bar + en_offset + odd_offset + geo_offset
        #
        self.np_res[_YMode, 0] = self.res_np[_YMode, 2] * self.half_length + 71.24 + \
                                 (self.res_np[_YMode, 4] - 1) ** 2 * self.half_length + \
                                 self.res_np[_YMode, 4] * \
                                 ((-1) ** (self.res_np[_YMode, 6] - 1) * self.res_np[_YMode, 7] + \
                                  (self.res_np[_YMode, 6] - 1) ** 2 * self.length) - _shift[_YMode]

        self.np_res[:, 1] = (self.layer_distance_np[:]) - (self.res_np[:, 4] - 1) * self.res_np[:,5] * self.half_length + \
                            self.res_np[:, 4] * (self.res_np[:, 2] % 2 * self.half_length + (-1) ** self.res_np[:, 2]
                                                 * self.res_np[:, 7])

    def generate_poca_inputs_np(self):

        _Cal_Range = [0, 1, 4, 5]
        wanted_z = [25.36, 430, 1035, 1440]

        _cpa = []
        for _i in range(len(_Cal_Range)):
            _x = [self.np_res[_Cal_Range[_i], 0], self.np_res[_Cal_Range[_i] + 2, 0]]
            _y = [self.np_res[_Cal_Range[_i], 1], self.np_res[_Cal_Range[_i] + 2, 1]]
            a,b = rsquared(_y,_x)
            if _Cal_Range[_i] < 4:
                _cpa.append((wanted_z[0] * a + b))
                _cpa.append((wanted_z[1] * a + b))
            else:
                _cpa.append((wanted_z[2] * a + b))
                _cpa.append((wanted_z[3] * a + b))
            # a, b = rsquared(_x, _y)
            # if _Cal_Range[_i] < 4:
            #     _cpa.append((wanted_z[0] - b) / a)
            #     _cpa.append((wanted_z[1] - b) / a)
            # else:
            #     _cpa.append((wanted_z[2] - b) / a)
            #     _cpa.append((wanted_z[3] - b) / a)
        if len(_cpa) == 8:
            _CPA = np.array([_cpa[0], _cpa[2], wanted_z[0],
                             _cpa[1], _cpa[3], wanted_z[1],
                             _cpa[4], _cpa[6], wanted_z[2],
                             _cpa[5], _cpa[7], wanted_z[3]])
            return _CPA

    def generate_poca_inputs(self):
        _Cal_Range = [0, 1, 4, 5]
        wanted_z = [25.36, 430, 1035, 1440]

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
            _CPA = np.array([_cpa[0], _cpa[2], wanted_z[0],
                             _cpa[1], _cpa[3], wanted_z[1],
                             _cpa[4], _cpa[6], wanted_z[2],
                             _cpa[5], _cpa[7], wanted_z[3]])
            return _CPA


"""-------------------------------------------------------------------------"""
if __name__ == '__main__':
    # data = pd.read_csv('./testData/csvData/tempData_10.27_14_12_02poca_data.csv', header = 0, index_col=0, sep='\t')
    # data = data.iloc[:, :12]
    # Ana = POCA_Analysis()
    # for i in range(data.shape[0]):
    #     _df = data.iloc[i,:]
    #     Ana.run_poca(_df)
    # Ana.poca_imaging()
    Z_data = 'testData/h5Data/tempData_10.27_14_12_02.h5'
        #r'/Users/niqk/ownCloud/xujialuo/Muon/Test_of_8_layers/New_frame_8_layer_test/data/tempData_10.27_14_12_02.h5'
    basicpath = 'tmpStorage'

    _data = h5Data(Z_data, 'r')
    data = _data.getData(-2)
    result = AnalyzeMuonEvent(basicpath)
    EID_List = data['triggerID'].drop_duplicates().to_list()

    for eid in tqdm(EID_List):
        df = data[data['triggerID'] == eid].reset_index(drop=True)
        result.load_event(df)
    result.data_report()
    get_ratio_input = POCA_Analysis()
    for _ in result.POCA_List:
        get_ratio_input.run_poca(_)

    get_ratio_input.poca_imaging()
    get_ratio_input.show_3D_poca()
    # _MC_data = np.concatenate(get_ratio_input.CPA_List, axis=0).reshape([len(get_ratio_input.CPA_List), 10])
    # pd.DataFrame(_MC_data).to_csv(os.path.join(get_ratio_input.res_path, 'Z_input.txt'),
    #                               sep='\t', header=False, index=False)
