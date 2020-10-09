from dataLayer.baseCore import  h5Data
from dataLayer.calculationTools import *
from dataLayer.dataStorage import *
import dataLayer
import pyqtgraph.examples
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.Qt import QApplication
import sys
import numpy as np
from GuiLayer.myPlotWidget import subPlotWin_singal,subPlotWin_coincidence
#pyqtgraph.examples.run()
file = h5Data('data/2020_10_06/temp_1.h5', 'r')
d = file.getData(-2)
print(d.shape)
d.to_csv('testData/csvData/temp_csv_20201006.txt')
# setH5Path('data/2020_10_06/temp_1.h5')
# print(getDataIndex())
# update()
# print(getDataIndex())
# app = QApplication(sys.argv)
# ex = subPlotWin_coincidence()
# ex.setData(1, 16,17)
# ex.show()
# ex_0 = subPlotWin_singal()
# ex_0.setData(0,16)
# ex_0.show()
# sys.exit(app.exec_())

# win = pg.GraphicsLayoutWidget(show=True)
# win.resize(800,350)
# win.setWindowTitle('pyqtgraph example: Histogram')
# x = np.linspace(0,4096,4096)
#
# for i in range(9):
#     for j in range(4):
#         plt = win.addPlot()
#         plt.plot(x, getEnergySpetrumData(0, i*4+j), stepMode=True, fillLevel=0, fillOutline=True, brush=(0,0,255,150))
#     win.nextRow()