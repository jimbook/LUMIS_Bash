import pyqtgraph as pg
import sys
import copy
import pandas as pd
import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget,QApplication
from UI.myPlot import Ui_Form
from dataLayer.calculationTools import ToCoincidentEnergySpetrumData
from dataLayer.dataStorage import getEnergySpetrumData, calculationAllData, getSizeInMemory,getDataInMemory
import functools

#单通道能谱图像
class subPlotWin_singal(Ui_Form,QWidget):
    def __init__(self,*args):
        super(subPlotWin_singal, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.plotItem = pg.PlotItem()
        self.plotDataItem = pg.PlotDataItem()
        self.bars = np.arange(2**12)
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
    def setData(self,tier: int,channel: int):
        '''
            :param tier: 层数
            :param channel: 通道
            :param HighGain: 是否是高增益
            :return:
        '''
        # 若为高增益，则从处理元数据
        # 若为低增益，则获取仓库中的能谱数据
        global dataInDisk,dataInMemory
        self.tier = tier
        self.channel = channel
        self.index_memory = 0
        self.energy_data = None # 处理得到的能谱结果
        # set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier, channel,"低"))
        self.plotUpdate()

    # 更新数据
    @pyqtSlot()
    def dataUpdate(self):
        # 若为低增益，则从仓库中获取数据
        self.plotUpdate()

    # 更新图像
    def plotUpdate(self):
        # 若为低增益，获取仓库中能谱
        y = copy.copy(getEnergySpetrumData(self.tier,self.channel))
        np.place(y,self.bars[:-1] < self.spinBox_baseLine.value(),[0])
        self.label_count.setText(str(np.sum(y)))
        self.plotDataItem.setData(self.bars,y,stepMode=True, fillLevel=0, fillOutline=False, brush=(0,0,255,150),
                                  pen = pg.mkPen((0,0,255,150)))

    # 更改基线
    @pyqtSlot(int)
    def changeBaseLine(self,new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        self.plotUpdate()

#符合能谱图像
class subPlotWin_coincidence(Ui_Form,QWidget):
    def __init__(self):
        super(subPlotWin_coincidence, self).__init__()
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.plotItem = pg.PlotItem()
        self.plotDataItem = pg.PlotDataItem()
        self.bars = np.arange(2**12)
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
    def setData(self, tier: int, channel: int, channel_coin: int):
        '''

        :param tier: 层数
        :param channel: 显示通道
        :param channel_coin: 用于符合的通道
        :return:
        '''
        self.tier = tier
        self.channel = channel
        self.channel_coin = channel_coin
        self.index_memory = 0   # 目前获取到的数据行数
        self.energy_data = None # 符合能谱信息
        # set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier, channel, "低"))
        # 从dataStorage计算符合能谱
        self.DataFunc = functools.partial(ToCoincidentEnergySpetrumData,
                                          tier=self.tier, channel=self.channel,
                                          channel_coin=self.channel_coin)# 一个用于计算当前层当前选择通道符合能谱的偏函数
        self.energy_data = calculationAllData(self.DataFunc,lambda x,y:x+y)
        self.index_memory = getSizeInMemory()
        self.plotUpdate()

    # 更新数据
    @pyqtSlot()
    def dataUpdate(self):
        length = getSizeInMemory()
        # 如果数据只在内存中更新,只计算新增的数据
        if length >= self.index_memory:
            d = getDataInMemory(self.index_memory)
            self.index_memory = length
            self.energy_data = self.energy_data + self.DataFunc(d)
        else:
            # 更新：若内存中的数据已经到达限定值而清空过，由于代码改进，清空前新增数据不会因此不向GUI进程传达
            # 因此，无需再读取硬盘中的数据，只有在新开启时才需要从硬盘中获取元数据
            d = getDataInMemory()
            self.index_memory = length
            self.energy_data = self.energy_data + self.DataFunc(d)
        print("index", self.index_memory)
        print("plotUpdata")
        self.plotUpdate()

    # 更新图像
    def plotUpdate(self):
        y = copy.copy(self.energy_data)
        np.place(y, self.bars[:-1] < self.spinBox_baseLine.value(), [0])
        self.label_count.setText(str(np.sum(y)))
        self.plotDataItem.setData(self.bars, y, stepMode=True, fillLevel=0, fillOutline=False, brush=(0, 0, 255, 150),
                                  pen=pg.mkPen((0, 0, 255, 150)))

    # 更改基线
    @pyqtSlot(int)
    def changeBaseLine(self, new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        self.plotUpdate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = pd.read_csv("data/2020_08_11/152700_data/tempData_0.txt", sep=',', header=[0, 1], index_col=0)
    d1 = data.values.tolist()
    ex = subPlotWin_singal()
    ex._setData(d1, 1, "chn_0", False)
    ex.show()
    sys.exit(app.exec_())