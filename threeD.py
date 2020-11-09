from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import numpy as np
app = QtGui.QApplication([])
w = gl.GLViewWidget()
w.opts['distance'] = 20
w.show()
w.setWindowTitle('3D example')

g = gl.GLGridItem()
w.addItem(g)
#1.red,green and blue
pos = np.empty((53,3))
size = np.empty(53)
color = np.empty((53,4))

pos[0] = (1,0,0)
size[0] = 0.5
color[0] = (1.0,0.,0.,0.5)

pos[1] = (0,1,0)
size[1] = 0.2
color[1] = (0.,0.,1.,0.5)

pos[2] = (0,0,1)
size[2] = 2./3
color[2] = (0.,1.,0.,0.5)

z = 0.5
d = 6.0
for i in range(3,53):
    pos[i] = (0,0,z)
    size[i] = 2./d
    color[i] = (0.,1.,0.,0.5)
    z *= 0.5
    d *= 2.0

sp1 = gl.GLScatterPlotItem(pos=pos, size=size, color=color, pxMode=False)
sp1.translate(5,5,0)
w.addItem(sp1)

#
pos = np.random.random((10000,3))
pos *= [10,-10,10]
pos[0] = (0,0,0)
color = np.ones((pos.shape[0],4))
d2 = (pos**2).sum(axis=1)**0.5
size = np.random.random(size=pos.shape[0])*10
sp2 = gl.GLScatterPlotItem(pos=pos,color=(1,1,1,0.1), size=size)
w.addItem(sp2)
side00 = gl.GLLinePlotItem(pos=np.array([[10,0,0],[10,0,10]]),color=(1,1,1,0.3),width=1)
w.addItem(side00)


if __name__ == '__main__':
    import sys
    QtGui.QApplication.instance().exec_()