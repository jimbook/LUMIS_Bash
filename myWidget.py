import pyqtgraph as pg
import os,sys
import pandas as pd
import numpy as np
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
        self.graphicsView.setBackground("w")
        self.graphicsView.setCentralItem(self.plotItem)
        self.plotItem.addItem(self.plotDataItem)
        self.spinBox_baseLine.setValue(435)
        self.horizontalSlider_baseLine.setValue(435)

    def setEvent(self):
        self.spinBox_baseLine.valueChanged.connect(self.changeBaseLine)
        self.horizontalSlider_baseLine.valueChanged.connect(self.changeBaseLine)

    def setData(self,data: pd.DataFrame,tier: int,channel: str,HighGain: bool):
        self.data = data
        self.tier = tier
        self.channel = channel
        self.HighGain = HighGain
        #set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier,channel,"高" if self.HighGain else "低"))
        self.dataUpdate()

    def dataUpdate(self):
        high = "charge/HighGain" if self.HighGain else "time/LowGain"
        data = self.data[self.channel][high]
        index =np.equal(self.data["SCAinfo"]["BoardID"] == self.tier,
                        self.data[self.channel][high + "_hit"] == 1)
        self._d = data.values[index]
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y,x = np.histogram(d,bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x,y,stepMode=True, fillLevel=0, fillOutline=False, brush=(0,0,255,150),
                                  pen = pg.mkPen((0,0,255,150)))

    def changeBaseLine(self,new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y, x = np.histogram(d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x, y, stepMode=True, fillLevel=0, fillOutline=False, brush=(0, 0, 255, 150),
                                  pen=pg.mkPen((0, 0, 255, 150)))

#双通道符合能谱图像
class subPlotWin_coincidence(Ui_Form, QWidget):
    def __init__(self, *args):
        super(subPlotWin_coincidence, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.data = pd.DataFrame()
        self.plotItem = pg.PlotItem()
        self.plotDataItem = pg.PlotDataItem()
        self.graphicsView.setBackground("w")
        self.graphicsView.setCentralItem(self.plotItem)
        self.plotItem.addItem(self.plotDataItem)
        self.spinBox_baseLine.setValue(435)
        self.horizontalSlider_baseLine.setValue(435)

    def setEvent(self):
        self.spinBox_baseLine.valueChanged.connect(self.changeBaseLine)
        self.horizontalSlider_baseLine.valueChanged.connect(self.changeBaseLine)

    def setData(self, data: pd.DataFrame, tier_1: int, channel_1: str,tier_2: int, channel_2: str, HighGain: bool):
        self.data = data
        self.tier_1 = tier_1
        self.channel_1 = channel_1
        self.tier_2 = tier_2
        self.channel_2 = channel_2
        self.HighGain = HighGain
        # set title
        self.setWindowTitle("第{0}层-第{1}通道&第{2}层-第{3}通道-{4}增益能谱".format(tier_1, channel_1,tier_2,channel_2, "高" if self.HighGain else "低"))
        self.dataUpdate()

    def dataUpdate(self):
        high = "charge/HighGain" if self.HighGain else "time/LowGain"
        data = self.data[self.channel_1][high]
        _i = self.data["SCAinfo"]["BoardID"] == self.tier_1
        _j = self.data["SCAinfo"]["BoardID"] == self.tier_2
        _b1 = self.data["SCAinfo"]["triggerID"].values[_i]
        _b2 = self.data["SCAinfo"]["triggerID"].values[_j]
        _a = (_b1[:len(_b2)] == _b2).reshape((-1,1))
        _ch1 = self.data[self.channel_1][high + "_hit"].values[_i]
        _ch2 = self.data[self.channel_2][high + "_hit"].values[_j]
        print(_ch1.shape[0]>_ch2.shape[0])
        if _ch1.shape[0] > _ch2.shape[0]:
            _ch2 = np.append(_ch2,0)
        elif _ch1.shape[0] < _ch2.shape[0]:
            _ch2 = _ch2[:-1]
        index = np.equal(_ch1,_ch2)
        self._d = data[_i].values[index]
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y, x = np.histogram(d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x, y, stepMode=True, fillLevel=0, fillOutline=False, brush=(0, 0, 255, 150),
                                  pen=pg.mkPen((0, 0, 255, 150)))

    def changeBaseLine(self, new: int):
        self.spinBox_baseLine.setValue(new)
        self.horizontalSlider_baseLine.setValue(new)
        d = self._d[self._d >= self.spinBox_baseLine.value()]
        y, x = np.histogram(d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        self.label_count.setText(str(len(d)))
        self.plotDataItem.setData(x, y, stepMode=True, fillLevel=0, fillOutline=False, brush=(0, 0, 255, 150),
                                  pen=pg.mkPen((0, 0, 255, 150)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    data =pd.read_csv(".\\data\\mydata.txt",sep=',',header=[0,1],index_col=0)
    ex = subPlotWin_singal()
    ex.setData(data,1,"chn_12",False)
    ex.show()
    sys.exit(app.exec_())
