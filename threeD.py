from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
from dataLayer.baseCore import h5Data
from PyQt5.Qt import QApplication
from PyQt5 import Qt
from PyQt5.QtWidgets import QWidget
import sys
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
        #grid.setSize(x=7,y=7)
        #grid.translate(dx=5,dy=5,dz=5)
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



    def setData(self,data:pd.DataFrame):
        a0 = pocaAnalizy(data)
        self.pocaPos = a0.pocaPositions[:,:4]
        self.plotUpdate()

    @Qt.pyqtSlot(bool)
    def setModelVisible(self, visible: bool):
        for i in self.modelList:
            i.setVisible(visible)

    @Qt.pyqtSlot()
    def plotUpdate(self):
        poca = self.pocaPos[(self.pocaPos[:,3] > self.doubleSpinBox_minAngle.value()) & (self.pocaPos[:,3] < self.doubleSpinBox_maxAngle.value())]
        poca = poca[(poca[:,2] > self.doubleSpinBox_minZ.value()) & (poca[:,2] < self.doubleSpinBox_maxZ.value())]
        tmp = poca[:,3] / np.max(self.pocaPos[:,3])
        pos = (poca[:,:3] - self.translate) / self.zoom
        ColorMap = self.widget_colorMap.colorMap().mapToFloat(data=tmp)
        self.scatterItem.setData(pos=pos,color = ColorMap,size=tmp*10)



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



if __name__ == '__main__':
    # 开启GUI进程
    app = QApplication(sys.argv)
    try:
        ex = GL3DWidget()
        data_L = h5Data("./testData/h5Data/tempData_10.28_10_20_54.h5", "r")
        data_Z = h5Data("./testData/h5Data/tempData_10.27_14_12_02.h5", "r")
        data_U = h5Data("./testData/h5Data/tempData_10.30_13_19_39.h5", "r")
        data = data_U.getData(-2)
        ex.setData(data)
        ex.show()
    except:
        import traceback
        traceback.print_exc()
    app.exec_()