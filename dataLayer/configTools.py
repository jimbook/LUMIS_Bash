'''
包含用于生成向设备发送的二进制配置命令的类
'''
from enum import unique,Enum
@unique
class property(Enum):
    TRIG_DAC = 'TRIG_DAC'
    DELAY_TRIGGER = 'DELAY_TRIGGER'
    INDAC0 = 'INDAC0'
    INDAC1 = 'INDAC1'
    INDAC2 = 'INDAC2'
    INDAC3 = 'INDAC3'
    INDAC4 = 'INDAC4'
    INDAC5 = 'INDAC5'
    INDAC6 = 'INDAC6'
    INDAC7 = 'INDAC7'
    INDAC8 = 'INDAC8'
    INDAC9 = 'INDAC9'
    INDAC10 = 'INDAC10'
    INDAC11 = 'INDAC11'
    INDAC12 = 'INDAC12'
    INDAC13 = 'INDAC13'
    INDAC14 = 'INDAC14'
    INDAC15 = 'INDAC15'
    INDAC16 = 'INDAC16'
    INDAC17 = 'INDAC17'
    INDAC18 = 'INDAC18'
    INDAC19 = 'INDAC19'
    INDAC20 = 'INDAC20'
    INDAC21 = 'INDAC21'
    INDAC22 = 'INDAC22'
    INDAC23 = 'INDAC23'
    INDAC24 = 'INDAC24'
    INDAC25 = 'INDAC25'
    INDAC26 = 'INDAC26'
    INDAC27 = 'INDAC27'
    INDAC28 = 'INDAC28'
    INDAC29 = 'INDAC29'
    INDAC30 = 'INDAC30'
    INDAC31 = 'INDAC31'
    INDAC32 = 'INDAC32'
    INDAC33 = 'INDAC33'
    INDAC34 = 'INDAC34'
    INDAC35 = 'INDAC35'
    PREAMP_GAIN0 = 'PREAMP_GAIN0'
    PREAMP_GAIN1 = 'PREAMP_GAIN1'
    PREAMP_GAIN2 = 'PREAMP_GAIN2'
    PREAMP_GAIN3 = 'PREAMP_GAIN3'
    PREAMP_GAIN4 = 'PREAMP_GAIN4'
    PREAMP_GAIN5 = 'PREAMP_GAIN5'
    PREAMP_GAIN6 = 'PREAMP_GAIN6'
    PREAMP_GAIN7 = 'PREAMP_GAIN7'
    PREAMP_GAIN8 = 'PREAMP_GAIN8'
    PREAMP_GAIN9 = 'PREAMP_GAIN9'
    PREAMP_GAIN10 = 'PREAMP_GAIN10'
    PREAMP_GAIN11 = 'PREAMP_GAIN11'
    PREAMP_GAIN12 = 'PREAMP_GAIN12'
    PREAMP_GAIN13 = 'PREAMP_GAIN13'
    PREAMP_GAIN14 = 'PREAMP_GAIN14'
    PREAMP_GAIN15 = 'PREAMP_GAIN15'
    PREAMP_GAIN16 = 'PREAMP_GAIN16'
    PREAMP_GAIN17 = 'PREAMP_GAIN17'
    PREAMP_GAIN18 = 'PREAMP_GAIN18'
    PREAMP_GAIN19 = 'PREAMP_GAIN19'
    PREAMP_GAIN20 = 'PREAMP_GAIN20'
    PREAMP_GAIN21 = 'PREAMP_GAIN21'
    PREAMP_GAIN22 = 'PREAMP_GAIN22'
    PREAMP_GAIN23 = 'PREAMP_GAIN23'
    PREAMP_GAIN24 = 'PREAMP_GAIN24'
    PREAMP_GAIN25 = 'PREAMP_GAIN25'
    PREAMP_GAIN26 = 'PREAMP_GAIN26'
    PREAMP_GAIN27 = 'PREAMP_GAIN27'
    PREAMP_GAIN28 = 'PREAMP_GAIN28'
    PREAMP_GAIN29 = 'PREAMP_GAIN29'
    PREAMP_GAIN30 = 'PREAMP_GAIN30'
    PREAMP_GAIN31 = 'PREAMP_GAIN31'
    PREAMP_GAIN32 = 'PREAMP_GAIN32'
    PREAMP_GAIN33 = 'PREAMP_GAIN33'
    PREAMP_GAIN34 = 'PREAMP_GAIN34'
    PREAMP_GAIN35 = 'PREAMP_GAIN35'

import clr
clr.AddReference(r".\dependence\DAQ_IO")
from DAQ_IO_DLL import DAQ_IO
# 对于单板的可变配置部分
class boardConfig(object):
    def __init__(self):
        self._csharp = DAQ_IO()
        self.setProperty('TRIG_DAC',250)
        for i in range(36):
            self.setProperty('INDAC{}'.format(i),511)
            self.setProperty('PREAMP_GAIN{}'.format(i),2744)
        self.setProperty('DELAY_TRIGGER',172)
        self.setProperty('DELAY_VALIDHOLD',int(172 / 4))
        self.setProperty('DELAY_RSTCOL',int(172 / 4))

    def setProperty(self,propertyName: property or str, newValue: int):
        if isinstance(propertyName,property):
            self._csharp.set_property(propertyName.value, newValue)
        elif isinstance(propertyName,str):
            self._csharp.set_property(propertyName,newValue)

    def getProperty(self,propertyName: property or str) -> int:
        if isinstance(propertyName,property):
            return self._csharp.get_property(propertyName.value)
        elif isinstance(propertyName,str):
            return self._csharp.get_property(propertyName)

    def getOrderBytes(self) -> bytes:
        length = self._csharp.exportConfig()
        rawData = self._csharp.getConfigBytes()
        output = b''
        for i in range(length):
            output += rawData[i].to_bytes(1,byteorder='big',signed=False)
        return output

from functools import reduce
# 总配置类
class configuration(object):
    # 每个单板不变的头和尾
    headBytes = b'\x13\x01\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x0e\x01\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x15\x02\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x19\x64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x01' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x01\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00'
    tailBytes = b'\x05\x00\x08\x00\xee\xee'
    def __init__(self):
        self.boardList = []
        self.boardNum = 0
        self.triggerMode = (0,1)

    # 设置连接的板子数量
    def setBoardsQuantity(self,boardNum: int):
        if boardNum > 8 or boardNum < 2:
            raise ValueError('The range of boardNum must be within 2~8')
        if self.boardNum < boardNum:
            for i in range(boardNum - self.boardNum):
                self.boardList.append(boardConfig())
        elif self.boardNum > boardNum:
            self.boardList = self.boardList[:boardNum]
        self.boardNum = boardNum

    # 设置触发模式
    def setTriggerMode(self,*triggerBoards):
        # 辅助函数：检验设置触发模式函数输入参数是否正确
        def _checkArgs( arg):
            if not isinstance(arg, int):
                raise ValueError('input parameter must be int,but {} is <{}>'.format(arg, type(arg)))
            if arg >= self.boardNum or arg < 0:
                raise ValueError('The range of input arg must be within 0~{},but {}'.format(self.boardNum - 1, arg))
        map(_checkArgs,triggerBoards)
        self.triggerMode = triggerBoards

    # 配置阈值
    def setThreshold(self, newValue: int, boardID: int = None):
        if newValue < 0 or newValue > 1023:
            raise ValueError('The range of newValue must be within 0~1023')
        if boardID is None:
            for i in self.boardList:
                i.setProperty('TRIG_DAC', newValue)
        else:
            self.boardList[boardID].setProperty('TRIG_DAC', newValue)

    # 配置延迟
    def setDelay(self, newValue: int, boardID: int = None):
        if newValue < 0 or newValue > 255:
            raise ValueError('The range of newValue must be within 0~255')
        if boardID is None:
            for i in self.boardList:
                i.setProperty('DELAY_TRIGGER', newValue)
        else:
            self.boardList[boardID].setProperty('DELAY_TRIGGER', newValue)

    # 配置偏压
    def setBiasVoltage(self, newValue: int, boardID: int = None, channelID: int = None):
        if isinstance(newValue, int):
            if newValue < 0 or newValue > 255:
                raise ValueError('The range of newValue must be within 0~255')
            else:
                newValue = int(newValue * 2 + 1)
        else:
            raise ValueError("Type of newValue should be int")
        # 如果未选择指定板，则配置所有板，会忽略指定的通道
        if boardID is None:
            for i in self.boardList:
                for j in range(36):
                    i.setProperty('INDAC{}'.format(j),newValue=newValue)
        else:
            # 若指定了板子，但未指定通道，则配置目标板上所有通道
            if channelID is None:
                for j in range(36):
                    self.boardList[boardID].setProperty('INDAC{}'.format(j),newValue=newValue)
            else:
                self.boardList[boardID].setProperty('INDAC{}'.format(channelID), newValue=newValue)

    # 获取二进制数据
    def getOrderBytes(self) -> bytes:
        output = self._boardOrder(self.boardNum)
        output += self._triggerMode(*self.triggerMode)
        for i in range(self.boardNum):
            output += (b'\xff' + (240 + i).to_bytes(1, byteorder='big', signed=False))
            output += self.headBytes
            output += self.boardList[i].getOrderBytes()
            output += self.tailBytes
        return output

    # 辅助函数：获取触发方式命令
    def _triggerMode(self, *triggerBoards) -> bytes:
        # 辅助函数：用于合并得到对应的二进制指令
        def merge(x,y):
            return (2**x) | (2**y)
        if len(triggerBoards) == 0:
            return b'\xfe\x00'
        idx = reduce(merge,triggerBoards)
        return b'\xfe' + idx.to_bytes(length=1, byteorder='big', signed=False)

    # 辅助函数：获取板子数命令
    def _boardOrder(self, boardNum: int) -> bytes:
        b = boardNum + 224
        _b = b.to_bytes(1,'big',signed=False)
        print(len(_b),_b.hex())
        return b'\xff' + _b

import pandas as pd
import numpy as np
from io import StringIO
from scipy.optimize import curve_fit
# 获取某一块芯片36通道的转换参数
def getArgs_VoltageToDigital(chipID: int or str) -> list:
    '''

    :param chipID: 芯片的序列ID
    :return: list结构：list[tuple(arg_a,arg_b)],shape=(36,2)，列表中的每一个元组元素都是一个通道的参数
    '''
    #  用于拟合的函数
    def voltageFunc(x, a, b):
        return a * x + b
    # 从文件读取数据
    with open('dependence/chipAbout/CalibrationData/Test_SP2E_BGA_FRA 703-{}.data'.format(chipID)) as file:
        _lines = file.readlines()
    _i = [' ']
    _i.extend(np.arange(36).astype(np.str).tolist())
    indexLine = '\t'.join(_i)
    indexLine += '\n'
    dataLines = [indexLine]
    dataLines.extend(_lines[53:63])
    source = ''.join(dataLines).replace(',', '.')
    with StringIO(source) as f:
        dataFrame = pd.read_csv(f, header=0, sep='\t', index_col=0)
    print(dataFrame)
    # 计算拟合参数
    y = dataFrame.index.values
    result = []
    for i in range(36):
        x = dataFrame.iloc[:, i].values
        popt, pcov = curve_fit(voltageFunc, x, y)
        result.append(popt)
        print(popt)
    return result

# 获取各层板子的芯片序列号(在此称为ChipID)
def getChipID() ->dict:
    with open('dependence/chipAbout/chipID.txt') as file:
        buff = file.readlines()
    chipDic = {}
    for line in buff:
        line.strip()
        _temp = line.split()
        if len(_temp) == 2:
            chipDic[int(_temp[0])] = _temp[1]
    return chipDic

# 根据拟合结果参数的电压命令转换函数
def Func_VoltageToDigital(x,a,b):
    return a*(29.79 - x - 0.5) + b


if __name__ == '__main__':
    l = getChipID()
    for i in l.values():
        print(i)

    c = configuration()
    c.setBoardsQuantity(8)
    c.setThreshold(280)
    c.setBiasVoltage(141)
    b = c.getOrderBytes()
    print(b.hex('-'))
    # with open('../configurationFile/conf.lmbc', 'wb') as f:
    #     f.write(b)
