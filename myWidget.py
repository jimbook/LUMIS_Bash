import pyqtgraph as pg
import os,sys
import gc
import copy
import pandas as pd
import numpy as np
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

    # 设置数据和参数
    def setData(self,data: dataStorage,tier: int,channel: str,HighGain: bool):
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
        self.index_disk = 0
        self.index_memory = 0
        self.energy_data_disk = None
        self.energy_data_memory = None
        self.bars = None
        #set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier,channel,"高" if HighGain else "低"))
        self.data = data
        self.dataUpdate()

    # 模块测试用
    def _setData(self,data: dataStorage,tier: int,channel: str,HighGain: bool):
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
        self.index_disk = 0
        self.index_memory = 0
        self.energy_data_disk = None
        self.energy_data_memory = None
        self.bars = None
        #set title
        self.setWindowTitle("第{0}层-第{1}通道-{2}增益能谱".format(tier,channel,"高" if HighGain else "低"))
        self.data = data
        self._dataUpdate()

    # 模块测试用
    def _dataUpdate(self):
        # 读取内存中的数据
        listOfData = self.data
        npOfData = np.array(listOfData)
        frameOfData = pd.DataFrame(npOfData,columns=[_chnList, _typeList])
        self.energy_data_memory, self.bars = self.selectData(frameOfData)
        self.plotUpdate()
        gc.collect()

    # 辅助函数：将目标采集板和通道上被触发的数据筛选出来,然后通过函数np.histogram转化为直方图坐标x,y
    def selectData(self,d: pd.DataFrame):
        _d = d[self.channel][self.HighGain]
        index = (d["SCAinfo"]["BoardID"] == self.tier)&(d[self.channel][self.HighGain + "_hit"] == 1)
        _d = _d.values[index]  # 将目标板子和通道已触发的数据筛选出
        y, x = np.histogram(_d, bins=np.linspace(0, 2 ** 12, 2 ** 12))
        return y,x

    # 更新数据
    def dataUpdate(self):
        if self.energy_data_memory is None:    # 如果是新开启的界面，要从内存和硬盘读取全部数据
            # 读取内存中的数据
            listOfData = self.data.get_memoryData()
            frameOfData = pd.DataFrame(listOfData,index=[0],columns=[_chnList,_typeList])
            self.index_memory = len(listOfData)
            self.energy_data_memory,self.bars = self.selectData(frameOfData)
            # 读取所有硬盘中的数据
            files = self.data.get_diskData()
            for i in files:
                _data = pd.read_csv(i)
                _x,y = self.selectData(_data)
                if self.energy_data_disk is None:
                    self.energy_data_disk = y
                else:
                    self.energy_data_disk = self.energy_data_disk + y
            self.index_disk = len(files)
        else:   # 如果不是新开的界面，只会读取新的数据，处理后与当前数据相加
            listOfData = self.data.get_memoryData()
            # 如果数据只在内存中更新
            if len(listOfData) >= self.index_memory:
                d = pd.DataFrame(listOfData[self.index_memory:],index=[0],columns=[_chnList,_typeList])
                self.index_memory = len(d)
                self.energy_data_memory = self.energy_data_memory + self.selectData(d)[1]
            else: #如果内存中的数据已经达到128MB而清空过，读取硬盘中最新的那个数据文件，同时读取内存中的数据
                # 读取硬盘中新文件的数据
                files = self.data.get_diskData()
                _dataFromFile = pd.DataFrame(files[self.index_disk])
                self.energy_data_disk = self.energy_data_disk + self.selectData(_dataFromFile)[1]
                # 读取内存中的数据
                self.index_memory = len(listOfData)
                d = pd.DataFrame(listOfData,index=[0],columns=[_chnList,_typeList])
                self.energy_data_memory = self.selectData(d)[1]
        self.plotUpdate()
        gc.collect()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    data =pd.read_csv(".\\data\\mydata.txt",sep=',',header=[0,1],index_col=0)
    d1 = data.values.tolist()
    ex = subPlotWin_singal()
    ex._setData(d1,1,"chn_12",False)
    ex.show()
    sys.exit(app.exec_())
