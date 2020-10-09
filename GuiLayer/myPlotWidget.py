import pyqtgraph as pg
import sys
import copy
import pandas as pd
import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget,QApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from UI.myPlot import Ui_Form
from dataLayer.calculationTools import ToCoincidentEnergySpetrumData, ChooseGoodEvent
from dataLayer import dataStorage
import functools
from GuiLayer.myPlotItem import boardBarsPlot

#单通道能谱图像
class subPlotWin_singal(Ui_Form,QWidget):
    def __init__(self,*args):
        super(subPlotWin_singal, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.plotItem = pg.PlotItem()   # 图像对象
        self.plotDataItem = pg.PlotDataItem()   # 图像数据对象
        self.bars = np.arange(2**12)    # x轴数据
        self.graphicsView.setBackground("w")    # 设置背景为白色
        self.graphicsView.setCentralItem(self.plotItem)
        self.plotItem.addItem(self.plotDataItem)
        self.spinBox_baseLine.setValue(435) # 设置默认的基线
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
            :return:
        '''
        self.tier = tier
        self.channel = channel
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
        # 获取仓库中能谱
        y = copy.copy(dataStorage.getEnergySpetrumData(self.tier,self.channel))
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
class subPlotWin_coincidence(QWidget,Ui_Form):
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
        # set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier, channel, "低"))
        # 从dataStorage计算符合能谱
        self.DataFunc = functools.partial(ToCoincidentEnergySpetrumData,
                                          tier=self.tier, channel=self.channel,
                                          channel_coin=self.channel_coin) # 一个用于计算当前层当前选择通道符合能谱的偏函数
        self.energy_data, self.index_memory = dataStorage.calculationData(self.DataFunc)
        self.plotUpdate()

    # 更新数据
    @pyqtSlot()
    def dataUpdate(self):
        d, self.index_memory = dataStorage.calculationData(self.DataFunc,startIndex=self.index_memory)
        self.energy_data = d
        print("index", self.index_memory)
        print("plotUpdate")
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
        
#触发事件图像
class subPlotWin_eventTrackShow(QScrollArea):
    def __init__(self):
        super(subPlotWin_eventTrackShow, self).__init__()
        self.setMore()

    def setMore(self):
        self.setWindowTitle('触发事件')
        self.index_memory = 0
        self.boardList = []
        self.containerWidget = QWidget()
        self.containerWidget.setMinimumSize(1500, 140 * 8 +10)
        self.containerWidget.setLayout(QVBoxLayout(self.containerWidget))
        for i in range(8):
            b = boardBarsPlot(boardNum=i)
            self.boardList.append(b)
            self.containerWidget.layout().addWidget(b)
        self.setWidget(self.containerWidget)

    def Event(self):
        pass

    def setData(self, data: np.array):
        if data.shape[1] >= 38:
            for i in range(data.shape[0]):
                self.boardList[i].setBoardData(data[i])
        else:
            raise ValueError('The shape of argument(data) should be (39,1~8)')

    def dataUpdate(self):
        event, self.index_memory = dataStorage.calculationData(ChooseGoodEvent, startIndex=self.index_memory)
        self.setData(event.values)
        print('event update')
        self.containerWidget.repaint()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    # data = pd.read_csv("data/2020_08_11/152700_data/tempData_0.txt", sep=',', header=[0, 1], index_col=0)
    # d1 = data.values.tolist()
    # ex = subPlotWin_singal()
    # ex._setData(d1, 1, "chn_0", False)
    # ex.show()
    demo = subPlotWin_eventTrackShow()
    n = np.zeros((8, 39), 'int64')
    for i in range(8):
        r = np.random.random(4)
        n[i][int(r[0] * 32)] = int(r[1] * 500 + 350)
        n[i][int(r[2] * 32)] = int(r[3] * 500 + 350)
    print(n)
    demo.show()
    demo.setData(n)
    sys.exit(app.exec_())
