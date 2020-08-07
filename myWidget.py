import pyqtgraph as pg
import os,sys
import pandas as pd
import numpy as np
from globelParameter import dataLock
from PyQt5.QtWidgets import QWidget,QApplication
from UI.myPlot import Ui_Form
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

    # 设置数据和参数
    def setData(self,data: pd.DataFrame,tier: int,channel: str,HighGain: bool):
        '''

        :param data: 数据
        :param tier: 层数
        :param channel: 通道
        :param HighGain: 是否是高增益
        :return:
        '''
        self.tier = tier
        self.channel = channel
        self.HighGain = HighGain
        #set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier,channel,"高" if self.HighGain else "低"))
        dataLock.acquire(timeout=5)  # 数据载入时加锁防止错乱
        self.data = data
        self.plotUpdate()
        dataLock.release()

    # 更新数据
    def dataUpdate(self,newData: pd.DataFrame = None):
        if newData is None or newData == 1:
            from linkGBT import dataStorage
            dataLock.acquire(timeout=5)
            self.data = dataStorage.to_dataFrame()
            self.plotUpdate()
            dataLock.release()
        elif isinstance(newData,pd.DataFrame):
            dataLock.acquire(timeout=5)
            self.data= newData
            self.plotUpdate()
            dataLock.release()

    # 更新图像
    def plotUpdate(self):
        high = "charge/HighGain" if self.HighGain else "time/LowGain"
        data = self.data[self.channel][high]
        index =(self.data["SCAinfo"]["BoardID"] == self.tier)&(self.data[self.channel][high + "_hit"] == 1)
        self._d = data.values[index]
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y,x = np.histogram(d,bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x,y,stepMode=True, fillLevel=0, fillOutline=False, brush=(0,0,255,150),
                                  pen = pg.mkPen((0,0,255,150)))

    # 更改基线
    def changeBaseLine(self,new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y, x = np.histogram(d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x, y, stepMode=True, fillLevel=0, fillOutline=False, brush=(0, 0, 255, 150),
                                  pen=pg.mkPen((0, 0, 255, 150)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    data =pd.read_csv(".\\data\\2020_08_06\\132632_tempData.txt", sep=',', header=[0, 1], index_col=0)
    ex = subPlotWin_singal()
    ex.setData(data,2,"chn_2",False)
    ex.show()
    sys.exit(app.exec_())
