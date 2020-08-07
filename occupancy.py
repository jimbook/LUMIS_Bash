from dataAnalyse import dataAnalyse,chnList,typeList,SCAinfoList
import pandas as pd
import numpy as np
import os
import pyqtgraph.examples
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
def occupy(dataPath: str):
    data = pd.read_csv(dataPath, index_col=0, header=[0, 1])
    out = []
    for i in chnList[:32]:
        l = data[i][typeList[-1]]
        index = (data[i][typeList[-2]] == 1)&(data[chnList[-1]][SCAinfoList[-1]] == 2)
        c = l.values[index]
        out.append(c[c > 435].shape[0])
    return  np.array(out)
count = None
for root,dirs,files in os.walk(".\\data\\2020_08_06"):
    for f in files:
        _count = occupy(os.path.join(root,f))
        if count is None:
            count = _count
        else:
            count = count + _count
print(count)

win = pg.GraphicsLayoutWidget(show=True)
win.resize(800,350)
win.setWindowTitle('occupancy rate of bars')
win.setBackground('w')
plt1 = win.addPlot()
plt1.showGrid(x = True,y = True,alpha = 1)
x = [i - 0.5 for i in range(33)]
plt1.plot(x, count, stepMode=True, fillLevel=0, fillOutline=True, brush="#7FDC7F9F")
## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



