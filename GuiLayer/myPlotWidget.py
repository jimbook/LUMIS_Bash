import pyqtgraph.opengl as gl
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
from dataLayer.calculationTools import ToCoincidentEnergySpetrumData, ChooseGoodEvent,PocaPosition
from dataLayer import dataStorage
import functools
from GuiLayer.myPlotItem import boardBarsPlot, xyBoardsPlot


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
    @pyqtSlot(int)
    def dataUpdate(self,reset: int):
        '''

        :param reset: 当reset为1时，重置数据索引(设置离线数据时才用)
        :return:
        '''
        if reset == 1:
            self.energy_data, self.index_memory = dataStorage.calculationData(self.DataFunc)
        else:
            d, self.index_memory = dataStorage.calculationData(self.DataFunc,startIndex=self.index_memory)
            self.energy_data += d
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
    def __init__(self,*args):
        super(subPlotWin_eventTrackShow, self).__init__(*args)
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

# xy触发事件图像
class subPlotWin_eventXYTrackShow(QScrollArea):
    def __init__(self,*args):
        super(subPlotWin_eventXYTrackShow, self).__init__(*args)
        self.setMore()

    def setMore(self):
        self.setWindowTitle('触发事件_xy')
        self.index_memory = 0
        self.boardList = []
        self.xyList = []
        self.containerWidget = QWidget()
        self.containerWidget.setMinimumSize(1200, 170 * 4 + 10)
        layout = QGridLayout(self.containerWidget)
        self.containerWidget.setLayout(layout)
        for i in range(4):
            for j in range(2):
                b = boardBarsPlot(boardNum=i*2 + j)
                self.boardList.append(b)
                layout.addWidget(b, i, j)
        layout_xy_0 = QHBoxLayout(self)
        layout_xy_1 = QHBoxLayout(self)
        for i in range(4):
            _xy = xyBoardsPlot(boardNum=i)
            self.xyList.append(_xy)
            if i < 2:
                layout_xy_0.addWidget(_xy)
            else:
                layout_xy_1.addWidget(_xy)
        w_0 = QWidget()
        w_0.setLayout(layout_xy_0)
        w_0.setMinimumSize(480,480)
        w_1 = QWidget()
        w_1.setLayout(layout_xy_1)
        w_1.setMinimumSize(480,480)
        layout.addWidget(w_0, 4, 0)
        layout.addWidget(w_1, 4, 1)
        self.setWidget(self.containerWidget)

    def setData(self, data: np.array):
        if data.shape[1] >= 38:
            for i in range(data.shape[0]):
                self.boardList[i].setBoardData(data[i])
            for i in range(int(data.shape[0]/2)):
                self.xyList[i].setBoardsData(xData=data[i*2],yData=data[i*2+1])
        else:
            raise ValueError('The shape of argument(data) should be (39,1~8)')

    def dataUpdate(self):
        event, self.index_memory = dataStorage.calculationData(ChooseGoodEvent, startIndex=self.index_memory)
        self.setData(event.values)
        print('event update')
        self.containerWidget.repaint()


from UI.GL3D import Ui_Form
from dataLayer.calculateForPoca import *
class GL3DWidget(QWidget,Ui_Form):
    def __init__(self,*args,**kwargs):
        super(GL3DWidget, self).__init__(*args,**kwargs)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        # define parameter
        self.zoom = 30
        self.translate = np.array([320, 350, 600])
        self.modelList = []
        # set color map
        self.widget_colorMap.setOrientation("right")
        colorMap = pg.ColorMap(np.array([0, 0.2, 0.5, 0.8]),
                               np.array([[0, 0, 255,255*0.6],
                                         [0, 133, 133,255*0.6],
                                         [255, 155, 0,255*0.6],
                                         [255, 0, 0,255*0.6]])
                               , pg.ColorMap.RGB)
        self.widget_colorMap.setColorMap(colorMap)
        # data
        self.triggerPos = np.array([])
        self.pocaPos = np.array([[0,0,0,0]])
        # add 3D data item
        self.scatterItem = gl.GLScatterPlotItem()
        self.widget_GL.addItem(self.scatterItem)
        # add 3D auxiliary item
        grid = gl.GLGridItem()
        self.widget_GL.addItem(grid)
        vertex = np.array([[-10,10,0],[-10,10,10]])
        for i in range(8):
            self.widget_GL.addItem(gl.GLLinePlotItem(pos=np.array(vertex.tolist()),color=(255, 255, 255, 76.5),width=0.05,antialias=True))
            if i == 3:
                vertex[0,2] += 10
                vertex[0,1] *= -1
            elif i < 3:
                vertex[:, i%2] *= -1
            else:
                vertex[i%2,:2] *= -1

        # add model
        self.addModel()

    def setEvent(self):
        self.widget_colorMap.sigGradientChanged.connect(self.plotUpdate)
        self.doubleSpinBox_minZ.valueChanged.connect(self.plotUpdate)
        self.doubleSpinBox_maxZ.valueChanged.connect(self.plotUpdate)
        self.doubleSpinBox_minAngle.valueChanged.connect(self.plotUpdate)
        self.doubleSpinBox_maxAngle.valueChanged.connect(self.plotUpdate)

        self.checkBox_showModel.clicked.connect(self.setModelVisible)
        self.checkBox_showPoca.clicked.connect(self.scatterItem.setVisible)


    def addModel(self):
        leaf = leadBrick(0,self.zoom)
        #leaf.rotate(90,1,0,0)
        site = np.array([230-10,224,681])
        site -= self.translate
        site = site/self.zoom
        leaf.translate(*site)
        self.widget_GL.addItem(leaf)
        right = leadBrick(0,self.zoom)
        site = np.array([230-10,650-230-60,681])
        site -= self.translate
        site = site/self.zoom
        right.translate(*site)
        self.widget_GL.addItem(right)
        back = leadBrick(1,self.zoom)
        back.rotate(-90,0,0,1)
        site = np.array([180-10,266+100,681])
        site -= self.translate
        site = site / self.zoom
        back.translate(*site)
        self.widget_GL.addItem(back)
        self.modelList.extend([leaf,right,back])

    @pyqtSlot(bool)
    def setModelVisible(self, visible: bool):
        for i in self.modelList:
            i.setVisible(visible)

    @pyqtSlot()
    def plotUpdate(self):
        if self.pocaPos.shape[0] > 0:
            poca = self.pocaPos[(self.pocaPos[:,3] > self.doubleSpinBox_minAngle.value()) & (self.pocaPos[:,3] < self.doubleSpinBox_maxAngle.value())]
            poca = poca[(poca[:,2] > self.doubleSpinBox_minZ.value()) & (poca[:,2] < self.doubleSpinBox_maxZ.value())]
            tmp = poca[:,3] / np.max(self.pocaPos[:,3])
            pos = (poca[:,:3] - self.translate) / self.zoom
            ColorMap = self.widget_colorMap.colorMap().mapToFloat(data=tmp)
            self.scatterItem.setData(pos=pos,color = ColorMap,size=tmp*10)

    @pyqtSlot(int)
    def dataUpdate(self):
        self.pocaPos = dataStorage.getPocaPosition()
        self.plotUpdate()

class leadBrick(gl.GLMeshItem):
    def __init__(self,modelName = 0,zoom = 30,color = (255,155,33,33)):
        verts = np.zeros((8, 3))
        verts[[1, 2, 5, 6], 0] = 200 if modelName == 0 else 100 # x
        verts[[2, 3, 6, 7], 1] = 50     # y
        verts[4:, 2] = 100              # z
        #
        faces = np.array([
            [0, 4, 7], [7, 3, 0],   # right
            [0, 4, 5], [5, 1, 0],   # back
            [1, 5, 6], [6, 2, 1],   # left
            [3, 7, 6], [6, 2, 3],   # front
            [4, 5, 6], [6, 7, 4],   # up
            [3, 0, 1], [1, 2, 3]    # down
        ])

        colors = np.empty((faces.shape[0], 4), dtype=float)
        for i in range(4):
            colors[:, i] = color[i] / 255

        super(leadBrick, self).__init__(vertexes=verts / zoom,
                                           faces=faces,
                                           faceColors=colors,
                                           smooth=False,
                                           drawEdges=True,
                                           edgeColor=(1,1,1,36/255),
                                           shader='balloon'
                                          )
        self.setGLOptions('additive')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    # data = pd.read_csv("data/2020_08_11/152700_data/tempData_0.txt", sep=',', header=[0, 1], index_col=0)
    # d1 = data.values.tolist()
    # ex = subPlotWin_singal()
    # ex._setData(d1, 1, "chn_0", False)
    # ex.show()
    demo = subPlotWin_eventXYTrackShow()
    n = np.zeros((8, 38), 'int64')
    for i in range(8):
        r = np.random.random(4)
        n[i][int(r[0] * 32)] = int(r[1] * 500 + 350)
        n[i][int(r[2] * 32)] = int(r[3] * 500 + 350)
    print(n)
    demo.show()
    demo.setData(n)
    sys.exit(app.exec_())
