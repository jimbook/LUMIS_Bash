import pyqtgraph as pg
import os
import sys
import gc
import copy
import pandas as pd
import numpy as np
from PyQt5.QtCore import QTimer,pyqtSlot
from PyQt5.QtWidgets import QWidget,QApplication
from UI.myPlot import Ui_Form
from globelParameter import dataStorage,_chnList,_typeList
#单通道能谱图像
class subPlotWin_singal(Ui_Form,QWidget):
    def __init__(self,*args):
        super(subPlotWin_singal, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.data = pd.DataFrame()
        self.plotItem = pg.PlotItem()
        self.plotDataItem = pg.PlotDataItem()
        self._d = np.array([]) # 当前选中通道的数据，用于改变基线时快速计算
        self.graphicsView.setBackground("w")
        self.graphicsView.setCentralItem(self.plotItem)
        self.plotItem.addItem(self.plotDataItem)
        self.spinBox_baseLine.setValue(435)
        self.horizontalSlider_baseLine.setValue(435)


    def setEvent(self):
        # change base line
        self.spinBox_baseLine.valueChanged.connect(self.changeBaseLine)
        self.horizontalSlider_baseLine.valueChanged.connect(self.changeBaseLine)


    # 设置数据和参数，初始化界面时用
    def setData(self,data_memory: list,data_disk: list,tier: int,channel: str,HighGain: bool):
        '''
            :param data: 数据
            :param tier: 层数
            :param channel: 通道
            :param HighGain: 是否是高增益
            :return:
        '''
        self.tier = tier
        self.channel = channel
        self.HighGain = "charge/HighGain" if HighGain else "time/LowGain"
        self.index_memory = 0
        self.energy_data_disk = None
        self.energy_data_memory = None
        self.bars = None  # x轴分bin
        # set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier, channel, "高" if HighGain else "低"))
        #载入内存数据
        listOfData = np.array(data_memory).reshape((-1, 219))
        print("source", listOfData)
        frameOfData = pd.DataFrame(listOfData, columns=[_chnList, _typeList])
        self.index_memory = listOfData.shape[0]
        self.energy_data_memory, self.bars = self.selectData(frameOfData)
        # 读取所有硬盘中的数据
        for i in data_disk[:-1]:
            print(i)
            _data = pd.read_csv(i, index_col=0, header=[0, 1])
            y, _x = self.selectData(_data)
            if self.energy_data_disk is None:
                self.energy_data_disk = y
            else:
                self.energy_data_disk = self.energy_data_disk + y
        self.plotUpdate()

    # 更新数据
    @pyqtSlot(list,list)
    def dataUpdate(self,data_memory: list,data_disk: list):
        listOfData = np.array(data_memory).reshape((-1, 219))
        # 如果数据只在内存中更新,只计算新增的数据
        print("index", self.index_memory, "add:", listOfData)
        if listOfData.shape[0] >= self.index_memory:
            d = pd.DataFrame(listOfData[self.index_memory:], columns=[_chnList, _typeList])
            self.index_memory = listOfData.shape[0]
            self.energy_data_memory = self.energy_data_memory + self.selectData(d)[0]
        else:  # 如果内存中的数据已经达到32MB而清空过，读取硬盘中最新的那个数据文件，同时读取内存中的数据
            # 读取硬盘中新文件的数据
            _dataFromFile = pd.read_csv(data_disk[-2],index_col=0,header=[0,1])
            self.energy_data_disk = self.energy_data_disk + self.selectData(_dataFromFile)[0]
            # 读取内存中的数据
            self.index_memory = listOfData.shape[0]
            d = pd.DataFrame(listOfData, index=[0], columns=[_chnList, _typeList])
            self.energy_data_memory = self.selectData(d)[0]
        print("plotUpdata")
        self.plotUpdate()

    # 更新图像
    def plotUpdate(self):
        if self.energy_data_disk is not None:
            y = copy.copy(self.energy_data_disk + self.energy_data_memory)
        else:
            y = copy.copy(self.energy_data_memory)
        np.place(y,self.bars[:-1] < self.spinBox_baseLine.value(),[0])
        self.label_count.setText(str(np.sum(y)))
        self.plotDataItem.setData(self.bars,y,stepMode=True, fillLevel=0, fillOutline=False, brush=(0,0,255,150),
                                  pen = pg.mkPen((0,0,255,150)))

    # 更改基线
    def changeBaseLine(self,new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        self.plotUpdate()

    # 辅助函数：将目标采集板和通道上被触发的数据筛选出来,然后通过函数np.histogram转化为直方图坐标x,y
    def selectData(self,d: pd.DataFrame):
        _d = d[self.channel][self.HighGain]
        index = (d["SCAinfo"]["BoardID"] == self.tier)&(d[self.channel][self.HighGain + "_hit"] == 1)
        _d = _d.values[index]  # 将目标板子和通道已触发的数据筛选出
        y, x = np.histogram(_d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        return y,x

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = pd.read_csv(".\\data\\2020_08_08\\190101_data\\tempData_0.txt", sep=',', header=[0, 1], index_col=0)
    d1 = data.values.tolist()
    ex = subPlotWin_singal()
    ex._setData(d1, 1, "chn_12", False)
    ex.show()
    sys.exit(app.exec_())