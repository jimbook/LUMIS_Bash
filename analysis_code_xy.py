import h5py
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import random
from tqdm import tqdm


class MyIO:
    # filter the data by the correlation of serveral plane
    ###########################################################################################
    # HDF5 fILE STRUCTURE
    #     # --HDF5 Group: dataGroup
    #     #     HDF5 Dataset: data(39 x Unlimited)(charge * 36, temperature, trigID, boardID)
    #     #     HDF5 Dataset: index(1 x Unlimited)(max_len, each index when trigID reset)
    #     # - -HDF5 Group: info
    #     #     HDF5 Dataset: device_status(1 x 17)(coincidence, threshold * 8, voltage * 8)
    #     #     HDF5 Dataset: time(1 x 3)(start, stop, measure time)
    ###########################################################################################
    def __init__(self, fname):
        self._file = h5py.File(fname, 'r')
        _temp_index = list(self._file["dataGroup/index"][()])
        self._data_set = self._file["dataGroup/data"]
        self._index = [([1] + _temp_index[1:] + [_temp_index[0]]), ([1] + _temp_index)][
            len(_temp_index) == 1]  # 仿-条件表达式，用二维数组后缀索引实现
        self._data_cell = len(self._index) - 1
        #   'r'     ->  read only, file must exist
        #   'r+'    ->  read/write, file must exist
        #   'w'     ->  create file, truncate if exists
        # 'w- or x' ->  create file, fail if exists
        #   a       ->  read/write if file exists, create otherwise (default)

    def get_cell_num(self):
        return self._data_cell

    def get_spectrum(self, hist_range: tuple = (0, 1000)):
        _title = ['chn_{}'.format(_x) for _x in range(36)] + ["temperature", "eventID",
                                                                 "boardID"]  # or array.extend(x_list)
        _spectrums = np.zeros(shape=(8 * 36, hist_range[1] - hist_range[0]), dtype=int)
        for _i in range(len(self._index) - 1):
            _df = pd.DataFrame(self._data_set[self._index[_i] - 1: self._index[_i + 1] - 1], columns=_title)
            _hist_data = []
            for _board in range(8):
                for _chn in range(36):
                    _hist_n, _hist_bins = np.histogram(
                        _df[_df["boardID"].values == _board]["chn_{}".format(_chn)].values,
                        bins=hist_range[1] - hist_range[0], range=hist_range)
                    _hist_data.append(_hist_n)
            _hist_data = np.array(_hist_data)
            _spectrums += _hist_data
        return _spectrums, np.linspace(hist_range[0] + 0.5, hist_range[1] - 0.5, hist_range[1] - hist_range[0])

    def get_a_part_of_event(self, _i: int):
        _title = ['chn_{}'.format(x) for x in range(36)] + ["temperature", "eventID",
                                                             "boardID"]  # or array.extend(x_list)
        if (_i >= len(self._index)) | (_i < 0):
            print("error occurs! it doesn't match dataGroup's index")
            return 0
        else:
            return pd.DataFrame(self._data_set[self._index[_i] - 1: self._index[_i + 1] - 1], columns=_title)

    def close_h5(self):
        self._file.close()


class Spectrum:
    def __init__(self, sp_data, x_axis):
        self._sp_data = sp_data
        self._xaxis = x_axis
        self._baseline = np.zeros(shape=(8 * 36), dtype=int)
        self._threshold = np.zeros(shape=(8 * 36), dtype=int)
        self._threshold_index = np.zeros(shape=(8 * 36), dtype=int)
        self._scale_factor = np.ones(shape=(8 * 36), dtype=int)
        self._exchanged_chns = []

    def set_threshold(self, artifi_data):
        # 这里artifi_data应该是一个tuple或者list，每个元素内部又包含两个元素，第一个为8*plane+chn以代表位置，第二个代表阈值的数值
        for _i in range(len(artifi_data)):
            self._threshold[artifi_data[_i][0]] = artifi_data[_i][1]

    def calcula_baseline(self):  # need smoooth?
        for _i in range(len(self._sp_data)):
            _max_x_index = np.argmax(self._sp_data[_i])
            self._baseline[_i] = self._xaxis[_max_x_index]
        # return self._baseline

    def calcula_threshold(self):  # need smoooth?
        for _i in range(len(self._sp_data)):
            _max_x_index = np.argmax(self._sp_data[_i])
            _thre_x_index = np.argmin(self._sp_data[_i][_max_x_index: _max_x_index + 30])
            self._threshold_index[_i] = _max_x_index + _thre_x_index
            self._threshold[_i] = self._xaxis[_max_x_index + _thre_x_index]
        # return self._threshold

    def calcula_scale_factor(self):  # need smoooth?
        _scale_reference = []
        for _i in range(len(self._sp_data)):
            _one_sp = np.array(self._sp_data[_i])
            _integral = []
            for _bin in range(len(self._xaxis)):
                if _bin < self._threshold_index[_i]:
                    _integral.append(0)
                elif _bin == self._threshold_index[_i]:
                    _integral.append(_one_sp[self._threshold_index[_i]])
                else:
                    _integral.append(np.sum(_one_sp[self._threshold_index[_i]:_bin]))
            if _integral[-1] > 10:
                _nor_integral = np.array(_integral) / _integral[-1]
                _max_value = self._xaxis[np.argmax(_nor_integral[_nor_integral < 0.98])] - self._baseline[_i]
                _scale_reference.append(_max_value)
            else:
                _scale_reference.append(1)
        self._scale_factor = _scale_reference[0] / np.array(_scale_reference)
        # return self._scale_factor

    def get_exchange_chn_num(self):
        # [Attention: channels exchanged must be arranged as their previous order]
        for _i in range(8):
            _temp = np.array([np.sum(_item) for _item in self._sp_data[_i * 36:(_i + 1) * 36]])
            self._exchanged_chns.append([np.arange(0, 32, 1, dtype=int)[_temp[:32] < np.sum(_temp) / 3200],
                                          np.arange(32, 36, 1, dtype=int)[_temp[32:] > np.sum(_temp) / 3200]])
        # return self._exchanged_chn

    def get_result(self):
        return self._baseline, self._threshold, self._scale_factor, self._exchanged_chns


class Channel:
    def __init__(self):
        self._charge = 0
        self._hit = False

    def initial(self, charge: int = 0, baseline: int = 0, threshold: int = 0, scale_factor: float = 1.0):
        self._hit = (charge > threshold)
        self._charge = (charge - baseline) * scale_factor

    def get_values(self):
        return self._hit, self._charge


class Plane:
    def __init__(self, plane_num: int):
        self._plane_num = plane_num
        # build 36 channels in this Plane
        self._chns = []
        for _i in range(36):
            self._chns.append(Channel())  # 得到包含36chn的一层平板
        # initial some parameters
        self._hit_36 = np.zeros(shape=36, dtype=bool)
        self._charge_36 = np.zeros(shape=36, dtype=float)
        # initial several plots
        self._position = []  # positions calculated
        self._dose_hist = np.zeros(shape=36, dtype=int)
        self._hit_hist = np.zeros(shape=36, dtype=int)

    def initial(self, chn_data: list, instance_sp: Spectrum):
        # ****************** 这里的instance_sp是把Spectrum类的一个实例作为成员进行操作，只是用到了它完成的能量刻度部分的其中一小块儿，以及阈值和基线相关内容
        _baseline, _threshold, _scale_factor, _exchanged_chns = instance_sp.get_result()
        # if _exchanged_chns[self._plane_num] != [[],[]]:
        if (_exchanged_chns[self._plane_num][0].size > 0) & (_exchanged_chns[self._plane_num][1].size > 0):
            for _previous, _subsequent in zip(_exchanged_chns[self._plane_num][0],
                                                _exchanged_chns[self._plane_num][1]):
                _temp = chn_data[_previous]
                chn_data[_previous] = chn_data[_subsequent]
                chn_data[_subsequent] = _temp
            # print(self._plane_num, chn_data)
        for _i in range(36):
            self._chns[_i].initial(chn_data[_i],
                                     _baseline[self._plane_num * 36 + _i],
                                     _threshold[self._plane_num * 36 + _i],
                                     _scale_factor[self._plane_num * 36 + _i])  # 得到包含36chn的一层平板
            self._hit_36[_i], self._charge_36[_i] = self._chns[_i].get_values()  # 获取各chn的电荷信息

    def calcula_positions(self):
        self._position = []  # positions需要初始化，防止下一次的position叠加进来
        # find all neighbour bars, then calculate every position
        # ****** 要求只能是两个相邻bar的触发，三个及以上的情况都应该抛弃掉这个点
        # ****** 如果发现一层里面几乎全部被触发，应该直接舍弃掉这一层的数据
        # ****** if no neighbour bars, then 把所有触发bar的直角顶点当作位置
        _bar_num = np.arange(36, dtype=int)
        _fired_chn = _bar_num[self._hit_36 == 1]
        _i = 0
        _position_z = [0, 3.6, 40.45, 44.05, 100.75, 104.35, 141.2, 144.8]
        while _i < len(_fired_chn):
            _neighbour_bar_num = 0
            if _i < len(_fired_chn) - 1:
                while _fired_chn[_i + 1] - _fired_chn[_i] == 1:
                    _neighbour_bar_num += 1
                    _i += 1
                    if _i < len(_fired_chn) - 1:
                        continue
                    else:
                        break
            if _neighbour_bar_num == 0:  # find or left a single fired bar
                self._position.append(
                    ((_fired_chn[_i] + 1) * 1.5 + _fired_chn[_i] * 0.038355 - 25.3445,
                     _position_z[self._plane_num] + (_fired_chn[_i] + 1) % 2 * 1.5))
            elif _neighbour_bar_num == 1:  # find a paid of neighbour bar
                _e1 = self._charge_36[_fired_chn[_i - 1]]
                _e2 = self._charge_36[_fired_chn[_i]]
                self._position.append(
                    ((_fired_chn[_i] + _e2 / (_e1 + _e2)) * 1.5 + _fired_chn[_i - 1] * 0.038355 - 25.3445,
                     _position_z[self._plane_num] + _fired_chn[_i] % 2 * 1.5 + (-1) ** _fired_chn[
                         _i] * 1.5 * _e2 / (_e1 + _e2)))
            else:
                pass
            _i += 1
        if len(self._position) != 1:
            self._position = []
        # print(self._position)

    def fill_dose(self):
        self._dose_hist = self._dose_hist + self._charge_36 * self._hit_36

    def fill_hit(self):
        self._hit_hist = self._hit_hist + self._hit_36

    def get_position(self):
        return self._position

    def get_dose_hist(self):
        return self._dose_hist

    def get_hit_hist(self):
        return self._hit_hist


class Cluster:
    # event by event analysis
    # 将Spectrum类和Plane类（Plane类又将Spectrum类和Channel类作为成员）作为成员
    def __init__(self):
        # build 8 planes in this Detector
        self._planes = []
        for _i in range(8):
            self._planes.append(Plane(_i))
        self._poca_l = []  # array内部是三维的poca数据点

    def calcula_poca(self, positions: np.array):
        # part_one:
        #       x: positions[0], position[2];
        #       y: positions[1], positions[3]
        # part_two:
        #       x: positions[4], position[6];
        #       y: positions[5], positions[7]

        _A_point = np.array([(3.6 - positions[2][1]) * (positions[0][0] - positions[2][0]) / (
                positions[0][1] - positions[2][1]) + positions[2][0],
                              (3.6 - positions[3][1]) * (positions[1][0] - positions[3][0]) / (
                                      positions[1][1] - positions[3][1]) + positions[3][0], 3.6])
        _B_point = np.array([(41.95 - positions[2][1]) * (positions[0][0] - positions[2][0]) / (
                positions[0][1] - positions[2][1]) + positions[2][0],
                              (41.95 - positions[3][1]) * (positions[1][0] - positions[3][0]) / (
                                      positions[1][1] - positions[3][1]) + positions[3][0], 41.95])

        _C_point = np.array([(104.35 - positions[6][1]) * (positions[4][0] - positions[6][0]) / (
                positions[4][1] - positions[6][1]) + positions[6][0],
                              (104.35 - positions[7][1]) * (positions[5][0] - positions[7][0]) / (
                                      positions[5][1] - positions[7][1]) + positions[7][0], 104.35])
        _D_point = np.array([(142.7 - positions[6][1]) * (positions[4][0] - positions[6][0]) / (
                positions[4][1] - positions[6][1]) + positions[6][0],
                              (142.7 - positions[7][1]) * (positions[5][0] - positions[7][0]) / (
                                      positions[5][1] - positions[7][1]) + positions[7][0], 142.7])
        _vector_ab = _B_point - _A_point
        _vector_cd = _D_point - _C_point
        _vector_n = np.cross(_vector_ab, _vector_cd)
        _theta = 180 / 3.1416 * math.asin(np.sqrt(np.dot(_vector_n, _vector_n)) / np.sqrt(
            np.dot(_vector_ab, _vector_ab) * np.dot(_vector_cd, _vector_cd)))
        if _theta > 1:
            _vector_n1 = np.cross(_vector_ab, _vector_n)
            _vector_n2 = np.cross(_vector_cd, _vector_n)
            _t1 = (np.dot(_vector_n2, _A_point) - np.dot(_vector_n2, _C_point)) / np.dot(_vector_n2, _vector_ab)
            _t2 = (np.dot(_vector_n1, _C_point) - np.dot(_vector_n1, _A_point)) / np.dot(_vector_n1, _vector_cd)
            _poca = 0.5 * (_A_point + _vector_ab * _t1 + _C_point + _vector_cd * _t2)
            return list(_A_point) + list(_B_point) + list(_C_point) + list(_D_point) + [_theta] + list(_poca)
        else:
            return []

    def analysis_ebe(self, df: pd.DataFrame, instance_sp: Spectrum):
        # 读入一个event事件，将信息下派分发给各个plane的各个channel；并将操作好了的实例化的能谱处理类丢给Plane，完成各个channel信息的初始化，以及扣本底，确定阈值，完成能量刻度
        # 根据得到的能量信息，进行各个plane的fire位置确定，并且最终整合在一起，进行Track检验。通过则合适，不通过，则读取下一个事件
        # 在上一步中，还可以进行一些常规信息的累加，比如hit hist和dose hist
        _positions = []
        if (len(df) == 8) & (len(np.unique(df["boardID"].values)) == 8):
            for _i in range(8):
                self._planes[_i].initial(df[df.boardID == _i].iloc[0].values[:36], instance_sp)
                self._planes[_i].calcula_positions()
                _positions += self._planes[_i].get_position()
            if len(_positions) == 8:
                # calculate poca point
                _result = self.calcula_poca(_positions)
                if _result:
                    self._poca_l.append(_result)
                    for _i in range(8):
                        self._planes[_i].fill_dose()
                        self._planes[_i].fill_hit()

    def get_poca(self):
        return self._poca_l

    def get_hist_data(self):
        _dose_hist_l = []
        _hit_hist_l = []
        for _i in range(8):
            _dose_hist_l.append(self._planes[_i].get_dose_hist())
            _hit_hist_l.append(self._planes[_i].get_hit_hist())
        return _dose_hist_l, _hit_hist_l


class Display:
    pass
    # First display the distribution of A, B, C, D的x与y的情况，判断是否对称分布。
    # Then, angle changed after scatter distribution
    # Also, poca distribution under different angle interval
    # Some plots, such as seaborn.heatmap or scatter plot with diff color refer to angle changed
    # efficiency display


class Ratio:
    def __init__(self, fname, df: pd.DataFrame, cube_radius: float = 5., theta_cut: float = 1.0,
                 amp_factor: int = 30000, start_point: int = 5, myslice: int = 1):
        self._fprefix = fname
        self._data = df
        self._cube_radius = cube_radius
        self._theta_cut = theta_cut
        self._amp_factor = amp_factor
        self._start_point = start_point
        self._slice = myslice
        self._endpoint = self._start_point + len(self._data) // self._slice
        self._RatioList = []

    def get_ratio_points(self):
        for _i in range(self._amp_factor):
            _px = random.uniform(-24, 24)
            _py = random.uniform(-24, 24)
            _pz = random.uniform(50, 80)
            _p_rand = np.array([_px, _py, _pz])
            self.poca_enchance(_p_rand)

    def poca_enchance(self, p_rand):
        _N_all = 0
        _N_cut = 0
        _Angle_sigma = 0.
        for _i in range(self._start_point, self._endpoint):
            _poca = self._data[["pocax", "pocay", "pocaz"]].values[_i]
            _angle = self._data["theta"].values[_i]
            _p0 = self._data[["Bx", "By", "Bz"]].values[_i]
            _q0 = self._data[["Cx", "Cy", "Cz"]].values[_i]
            if _angle > 20.0:
                continue
            _diff = _poca - p_rand
            if (abs(_diff[0]) < self._cube_radius) & (abs(_diff[1]) < self._cube_radius) & \
                    (abs(_diff[2]) < self._cube_radius):
                _N_all += 1
                _angle = _angle * abs(1 - np.sqrt(np.dot(_diff, _diff)) / self._cube_radius / np.sqrt(3))
                _Angle_sigma += _angle ** 2
                if _angle < self._theta_cut:
                    _N_cut += 1
            else:
                if _diff[2] < 0:
                    _line_u = _poca - _p0
                    _x_top = _line_u[0] / _line_u[2] * (p_rand[2] + self._cube_radius - _poca[2]) + _poca[0]
                    _x_low = _line_u[0] / _line_u[2] * (p_rand[2] - self._cube_radius - _poca[2]) + _poca[0]
                    _y_top = _line_u[1] / _line_u[2] * (p_rand[2] + self._cube_radius - _poca[2]) + _poca[1]
                    _y_low = _line_u[1] / _line_u[2] * (p_rand[2] - self._cube_radius - _poca[2]) + _poca[1]
                    if (abs(_x_top - p_rand[0]) < self._cube_radius) & \
                            (abs(_x_low - p_rand[0]) < self._cube_radius) & \
                            (abs(_y_top - p_rand[1]) < self._cube_radius) & \
                            (abs(_y_low - p_rand[1]) < self._cube_radius):
                        _N_all += 1
                        _N_cut += 1
                else:
                    _line_d = _q0 - _poca
                    _x_top = _line_d[0] / _line_d[2] * (p_rand[2] + self._cube_radius - _poca[2]) + _poca[0]
                    _x_low = _line_d[0] / _line_d[2] * (p_rand[2] - self._cube_radius - _poca[2]) + _poca[0]
                    _y_top = _line_d[1] / _line_d[2] * (p_rand[2] + self._cube_radius - _poca[2]) + _poca[1]
                    _y_low = _line_d[1] / _line_d[2] * (p_rand[2] - self._cube_radius - _poca[2]) + _poca[1]
                    if (abs(_x_top - p_rand[0]) < self._cube_radius) & \
                            (abs(_x_low - p_rand[0]) < self._cube_radius) & \
                            (abs(_y_top - p_rand[1]) < self._cube_radius) & \
                            (abs(_y_low - p_rand[1]) < self._cube_radius):
                        _N_all += 1
                        _N_cut += 1
        if _N_all > 100 * (self._cube_radius * 2) ** 2 * 0.01 // self._slice:
            self._RatioList.append([p_rand, np.sqrt(_Angle_sigma / _N_all), _N_cut / _N_all])

    def get_result(self):
        _df = pd.DataFrame(self._RatioList, columns=["randx", "randy", "randz", "theta", "ratio"])
        _df.to_csv(self._fprefix + "final_result.csv", sep='\t')
        # return self._RatioList

    def show_2d(self):
        _pocax_l = self._RatioList[:, 0]
        _pocay_l = self._RatioList[:, 1]
        _pocaz_l = self._RatioList[:, 2]
        _theta_l = self._RatioList[:, 3]
        _ratio_l = self._RatioList[:, 4]
        _sca_P = np.sqrt((_theta_l - np.min(_theta_l)) / (np.max(_theta_l) - np.min(_theta_l))) * 40.
        _sca_R = np.sqrt((np.max(_ratio_l) - _ratio_l) / (np.max(_ratio_l) - np.min(_ratio_l))) * 40.
        _fig, _ax = plt.subplots(2, 3, figsize=(12, 8))
        _fig.suptitle('Lanzhou University Muon Imaging System, upper: MSR/PoCA, lower: Ratio')
        # ************** poca above **************
        _cbar1 = _ax[0, 0].scatter(_pocax_l, _pocay_l, s=_sca_P, c=_theta_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar1, ax=_ax[0, 0])
        _ax[0, 0].grid(True)
        _ax[0, 0].set_xlim(-25, 25)
        _ax[0, 0].set_ylim(-25, 25)
        _ax[0, 0].set_xlabel('x (cm)')
        _ax[0, 0].set_ylabel('y (cm)')
        _cbar2 = _ax[0, 1].scatter(_pocax_l, _pocaz_l, s=_sca_P, c=_theta_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar2, ax=_ax[0, 1])
        _ax[0, 1].grid(True)
        _ax[0, 1].set_xlim(-25, 25)
        _ax[0, 1].set_ylim(50, 80)
        _ax[0, 1].set_xlabel('x (cm)')
        _ax[0, 1].set_ylabel('y (cm)')
        _cbar3 = _ax[0, 2].scatter(_pocay_l, _pocaz_l, s=_sca_P, c=_theta_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar3, ax=_ax[0, 2])
        _ax[0, 2].grid(True)
        _ax[0, 2].set_xlim(-25, 25)
        _ax[0, 2].set_ylim(50, 80)
        _ax[0, 2].set_xlabel('x (cm)')
        _ax[0, 2].set_ylabel('y (cm)')
        # ************** ratio below **************
        _cbar4 = _ax[1, 0].scatter(_pocax_l, _pocay_l, s=_sca_R, c=_ratio_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar4, ax=_ax[1, 0])
        _ax[1, 0].grid(True)
        _ax[1, 0].set_xlim(-25, 25)
        _ax[1, 0].set_ylim(-25, 25)
        _ax[1, 0].set_xlabel('x (cm)')
        _ax[1, 0].set_ylabel('y (cm)')
        _cbar5 = _ax[1, 1].scatter(_pocax_l, _pocaz_l, s=_sca_R, c=_ratio_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar5, ax=_ax[1, 1])
        _ax[1, 1].grid(True)
        _ax[1, 1].set_xlim(-25, 25)
        _ax[1, 1].set_ylim(50, 80)
        _ax[1, 1].set_xlabel('x (cm)')
        _ax[1, 1].set_ylabel('y (cm)')
        _cbar6 = _ax[1, 2].scatter(_pocay_l, _pocaz_l, s=_sca_R, c=_ratio_l, alpha=0.1, edgecolors='faces')
        _fig.colorbar(_cbar6, ax=_ax[1, 2])
        _ax[1, 2].grid(True)
        _ax[1, 2].set_xlim(-25, 25)
        _ax[1, 2].set_ylim(50, 80)
        _ax[1, 2].set_xlabel('x (cm)')
        _ax[1, 2].set_ylabel('y (cm)')

        _fig.savefig('poca_plt.png', dpi=600)


if __name__ == "__main__":
    range_low = 300
    range_up = 1000
    mode = 0
    # ****************** READ ME ******************
    # "tempData_10.27_14_12_02.h5"为”Z“型铅砖测量。
    # "tempData_10.28_10_20_54.h5"为“L”型铅砖测量数据。
    # "tempData_10.30_13_19_39.h5"为“U”型铅砖测量数据。
    # "tempData_11.02_22_59_16.h5"为无铅砖测量数据。
    # *********************************************
    fname = "testData/h5Data/tempData_10.27_14_12_02.h5"
    # 0 for analysis event by event with data read form hdf5 file
    # 1 for detection efficiency analysis of the whole detector
    # 2 for Spectrum test with data read from hdf5 file
    if mode == 0:
        h5io = MyIO(fname)
        sp_288_hist, x_axis = h5io.get_spectrum((range_low, range_up))
        spectrum_analysis = Spectrum(sp_288_hist, x_axis)
        spectrum_analysis.calcula_baseline()
        spectrum_analysis.calcula_threshold()
        spectrum_analysis.calcula_scale_factor()
        spectrum_analysis.get_exchange_chn_num()
        detector = Cluster()
        cell_num = h5io.get_cell_num()
        print("[cell_num]:", cell_num)
        # cell_num = [cell_num, 2][cell_num > 2]
        for i in range(cell_num):
            Part_df = h5io.get_a_part_of_event(i)  # 此处，每一组df都可以单独进行单进程操作，并将结果合并(但是这么做会剧烈地增大内存的使用)
            # print(Part_df, eventID_l)
            eventID_l = np.unique(Part_df.eventID)
            for event_id in tqdm(eventID_l):  # 此处，可以将eventID_L分成若干个部分，每一部分单独进行单进程操作
                detector.analysis_ebe(Part_df[Part_df.eventID == event_id], spectrum_analysis)
        h5io.close_h5()
        dose_hist_l, hit_hist_l = detector.get_hist_data()
        prefix = fname.split(".h5")[0]
        np.savetxt(prefix + "_dose_hist.txt", np.array(dose_hist_l), fmt='%.2f', delimiter=",")
        np.savetxt(prefix + "_hit_hist.txt", np.array(hit_hist_l), fmt='%.2f', delimiter=",")
        df = pd.DataFrame(detector.get_poca(), columns=['ax', 'ay', 'az', 'bx', 'by', 'bz',
                                                        'cx', 'cy', 'cz', 'dx', 'dy', 'dz',
                                                        'theta', 'pocax', 'pocay', 'pocaz'])
        df.to_csv(prefix + "poca_data.csv", sep='\t')
    elif mode == 1:
        # define several params
        fired_plane_counts_in_one_event = np.zeros(shape=9, dtype=int)
        leak_plane_in_seven_fired_event = np.zeros(shape=8, dtype=int)
        # analysis code
        h5io = MyIO(fname)
        cell_num = h5io.get_cell_num()
        print("[cell_num]:", cell_num)
        # cell_num = [cell_num, 1][cell_num > 1]
        for i in range(cell_num):
            Part_df = h5io.get_a_part_of_event(i)  # 此处，每一组df都可以单独进行单进程操作，并将结果合并(但是这么做会剧烈地增大内存的使用)
            eventID_l = np.unique(Part_df.eventID)
            fired_plane_counts_in_one_event[0] += len(eventID_l)
            for event_id in tqdm(eventID_l):  # 此处，可以将eventID_L分成若干个部分，每一部分单独进行单进程操作
                fired_plane_num = len(Part_df[Part_df.eventID == event_id])
                if fired_plane_num in [1, 2, 3, 4, 5, 6, 7, 8]:
                    fired_plane_counts_in_one_event[fired_plane_num] += 1
                    if fired_plane_num == 7:
                        my_boardid = Part_df[Part_df.eventID == event_id]['boardID'].values
                        leak_plane = [x for x in np.arange(8, dtype=int) if x not in my_boardid]
                        # print(my_boardid, '\n', leak_plane)
                        leak_plane_in_seven_fired_event[leak_plane[0]] += 1
        h5io.close_h5()
        print(fired_plane_counts_in_one_event, leak_plane_in_seven_fired_event)
    elif mode == 2:
        h5io = MyIO(fname)
        sp_288_hist, x_axis = h5io.get_spectrum((range_low, range_up))
        # print(x_axis)
        spectrum_analysis = Spectrum(sp_288_hist, x_axis)
        spectrum_analysis.calcula_baseline()
        spectrum_analysis.calcula_threshold()
        spectrum_analysis.calcula_scale_factor()
        baseline, threshold, scale_factor, exchanged_chns = spectrum_analysis.get_result()
        h5io.close_h5()
        # print(sp_288_hist, baseline, threshold, scale_factor)
        my_title = ['bin_{}'.format(x) for x in range(range_up - range_low)]
        df = pd.DataFrame(sp_288_hist, columns=my_title)
        df["baseline"] = baseline
        df["threshold"] = threshold
        df["scale_factor"] = scale_factor
        # df.to_csv('sp_result.csv', sep=',')
        for i in range(len(sp_288_hist)):
            if i % 36 == 0:
                plt.figure()
            plt.subplot(6, 6, i % 36 + 1)
            plt.plot(x_axis, sp_288_hist[i])
            xt = np.zeros(shape=1000)
            for j in range(len(xt)):
                xt[j] = threshold[i]
            yt = np.linspace(0, 200, 1000)
            xb = np.zeros(shape=1000)
            for j in range(len(xb)):
                xb[j] = baseline[i]
            yb = np.linspace(0, 200, 1000)
            plt.plot(xb, yb)
            plt.plot(xt, yt)
            plt.ylim(0, 200)
            plt.xlim(350, 550)
        plt.show()
    else:
        print("wrong mode provided!")
        pass
