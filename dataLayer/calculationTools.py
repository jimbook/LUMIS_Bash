'''
包含一些用于计算工具函数
'''
import pandas as pd
import numpy as np
from . import _Index

# 计算添加能谱数据
def ToEnergySpectrumData(data: pd.DataFrame) -> np.array:
    '''
    计算能谱数据
    :param data:原始数据
        ------------INPUT STRUCTURE------------
                    0~35        36          37
        COLUMNS: chn_00~chn_35 triggerID boardID
        shape:  (None,38)
    :return:
        ------------OUTPUT STRUCTURE-----------
        shape:(8, 36, 4095)
        AXIS0:boardID           AXIS1:channel           AXIS2:energy spectrum data
        0~7                     0~35                    0~4094
    '''
    ESD = np.zeros((8, 36, 4095),dtype='int64')
    for i in range(36):
        _chn = data[_Index[i]].values
        for j in range(8):
            boardIndex = (data[_Index[-1]] == j)
            index = (_chn != 0) & boardIndex
            chn = _chn[index]
            y, x = np.histogram(chn,bins=np.arange(2**12))
            ESD[j][i] = y
    return ESD

# 计算符合能谱
def ToCoincidentEnergySpetrumData(data: pd.DataFrame,tier: int, channel: int, channel_coin: int) -> np.array:
    '''
    计算符合能谱
    :param data: 原始数据
    ------------INPUT STRUCTURE------------
                    0~35        36          37
        COLUMNS: chn_00~chn_35 triggerID boardID
        shape:  (None,38)
    :param tier: boardID 层数
    :param channel: 输出的道
    :param channel_coin: 用于符合的道
    :return: shape: (4095,)
    '''
    index = (data[_Index[-1]] == tier) & \
            (data[_Index[channel]] != 0) & \
            (data[_Index[channel_coin]] != 0)
    _d = data[_Index[channel]].values[index]  # 将目标板子和通道已触发的数据筛选出
    y, x = np.histogram(_d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
    return y

# 对一个事件数据进行打分
def MarkOneEvent(event: pd.DataFrame) -> int:
    '''
    对一个事件的数据打分
    :param event:
    ===========EVENT STRUCTURE======
    COLUMN include: chn00~chn35
    shape: (0~8, 36+)
    :return: score
    ===========SCORING RULE=========
    认定为有8层
    一层数据情况      基准分为0时      基准分为64时
    0.没有数据          +8              +0
    1.只有一个数据       +10             +2
    2.有两个数据
        ├连续          +13             +5
        └不连续         +9             +1
    3.有三个数据
        ├连续          +10             +2
        └不连续        +4              -1
    4.有四个数据
        ├连续          +8             +0
        └不连续        +2              -4
    5.5~8个数据        +1              -7
    6.大于八个数据      +0              -8
    '''
    event = event[_Index[:36]]
    score = 64
    temp = np.arange(36)
    countIndex = (event != 0)
    for i in range(event.shape[0]):
        validIndex = temp[countIndex.iloc[i][:36]]
        count = validIndex.shape[0]
        if count == 1:
            score += 2
            continue
        if validIndex[-1] - validIndex[0] + 1 == count:
            _unc = False
        else:
            _unc = True
        if count == 2:
            score += 5
            if _unc:
                score -= 4
        elif count == 3:
            score += 2
            if _unc:
                score -= 3
        elif count == 4:
            if _unc:
                score -= 4
        elif count > 4 and count <= 8:
            score -= 7
        else:
            score -= 8
    return score

# 从一段数据中选择一个较好事件
def ChooseGoodEvent(data: pd.DataFrame) -> pd.DataFrame:
    '''

    :param data:
    :return: shape = (None, 38),triggerID被扔掉
    '''
    triggerID = np.unique(data[_Index[-2]].values)
    boardNum = np.unique(data[_Index[-1]].values).shape[0]
    d = data.set_index('triggerID')
    score = 0
    ID = None
    for i in triggerID:
        _d = d.loc[i]
        if isinstance(_d, pd.Series):
            continue
        _s = MarkOneEvent(_d)
        if _s == boardNum*13:
            return d.loc[i]
        if _s > score:
            ID = i
            score = _s
    if ID is None:
        return pd.DataFrame(columns=_Index)
    else:
        return d.loc[ID]

# 计算温度信息
def translateTemperature(data: np.array) -> np.array:
    _sign = int.from_bytes(b'\xf0\x00' ,byteorder='big', signed=False)
    _value = int.from_bytes(b'\x0f\xff' , byteorder='big', signed=False)
    result = np.empty(data.shape,dtype='float64')
    minus = (data & _sign) == 0
    value = data & _value
    result[~minus] = value[~minus] / 16
    result[minus] = -( (~value[minus] + 1) / 16)
    return result

# 轨迹测试

# 计算poca点
from threeD import pocaAnalizy
def PocaPosition(data: pd.DataFrame) -> np.array:
    '''

    :param data:
    :return: shape = (None,4) [x,y,z,theta]
    '''
    a0 = pocaAnalizy(data).pocaPositions
    if a0.shape[0] > 0:
        return a0[:, :4]
    else:
        return a0

# 判断是否存在高Z物体
def checkHighZ(PoCAPos:np.array,threshole = 3):
    '''

    :param PoCAPos: (None,4) [x,y,z,theta]
    :return: bool
    '''
    PoCA_angel = PoCAPos
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 2] < 900) & (PoCA_angel[:, 2] > 600)]
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 0] > 325-50) & (PoCA_angel[:, 0] < 325+50)]
    PoCA_angel = PoCA_angel[(PoCA_angel[:, 1] > 325-50) & (PoCA_angel[:, 1] < 325+50)]

    PoCA_voxels = PoCA_angel[:, 0] // 40 + PoCA_angel[:, 1] // 40 * 100 + PoCA_angel[:, 2] // 40 * 100 * 100
    PoCA_angel_weight = PoCA_angel[:, -1] < 0.3
    PoCA_angel_weight = PoCA_angel_weight * 0.1
    PoCA_angel_weight[PoCA_angel_weight == 0] = 1
    PoCA = pd.DataFrame({"theta": np.power(PoCA_angel[:, -1], 2) / 20 * PoCA_angel_weight,
                         "voxels": PoCA_voxels.astype(np.int)}).sort_values("voxels")
    voxels = PoCA.groupby("voxels").mean()
    voxel_max = np.max(voxels["theta"].values)
    if voxel_max >= threshole:
        return True
    else:
        return False

if __name__ == '__main__':
    pass


