from dataLayer.calculateForNumba import *
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from poca import POCA_Analysis
if __name__ == '__main__':
    d = pd.read_csv("./tmpStorage/channelReplace.csv")
    hd = h5Data("./testData/h5Data/tempData_10.27_14_12_02.h5","r")
    data = hd.getData(-2)
    #getParameter(data)
    fd = pretreatment_forNumba(data)
    print(fd.shape)
    msData = meanScale_forNumba(fd,meanScaleInfo.values[:,:32],threshold.values[:, :32],baseline.values[:,:32])
    cData = checkTriggerAvailable_forNumba(msData)
    geo = pd.read_csv("./tmpStorage/geometrySystem.csv",header=0,index_col = 0)
    dParameter = pd.read_csv("./tmpStorage/detectorGeometryParameter.csv",header=0,index_col=0)
    triggerSite = fastCalculateTriggerPositions_forNumba(cData,geo.values,dParameter.values[0])
    pos = fastCalculateParticleTrack(triggerSite,geo.values,dParameter.values[0],np.array([25.36, 430, 1035, 1440]))
    print(pos)


    # data = pd.read_csv('./testData/csvData/tempData_10.27_14_12_02poca_data.csv', header=0, index_col=0, sep='\t')
    # pos = data.values[:,:12].reshape((-1,4,3))
    # poca = calculatePocaPostions_forNumba(pos)


    # start = time.time()
    # points_ratio = ratio_main(_poca,pd.read_csv("./tmpStorage/detectPlace.csv",header=0,index_col=0).values)
    # print("poca event:{},ratio running time:{}s".format(_poca.shape[0],time.time()-start))
    # print(points_ratio.shape)

    # 3D
    # poca = _poca[(_poca[:,3] > 10 )&( _poca[:, 3] < 30)]
    # poca = poca[(poca[:,2] > 600) & (poca[:,2] < 850)]
    Ana = POCA_Analysis()
    for i in pos:
        _df = i.reshape((12,))
        Ana.run_poca(_df)
    Ana.poca_imaging()


    # app = QtGui.QApplication([])
    # w = gl.GLViewWidget()
    # w.opts['distance'] = 20
    # w.show()
    # w.setWindowTitle('3D example')
    # g = gl.GLGridItem()
    # w.addItem(g)
    # colorMap = pg.ColorMap(np.array([0,10,20,30]),
    #                        np.array([[1,1,1,0.3],[1,1,0,0.6],[0,0,1,0.6],[0,0,0,0.6]])
    #                        ,pg.ColorMap.RGB).mapToFloat(poca[:,3])
    # colorMap[:,3] = 0.006
    # sp2 = gl.GLScatterPlotItem(pos=poca[:,:3]/100, color=colorMap*100, size=poca[:,3]/np.max(poca[:,3]) * 6)
    # w.addItem(sp2)
    # colorMap = pg.ColorMap(np.array([0, 10, 20, 30]),
    #                        np.array([[1, 1, 1, 0.3], [1, 1, 0, 0.6], [0, 0, 1, 0.6], [0, 0, 0, 0.6]]),
    #                        pg.ColorMap.RGB).mapToFloat(points_ratio[:, 4])
    # colorMap[:, 3] = 0.006
    # sp2 = gl.GLScatterPlotItem(pos=points_ratio[:, :3] / 100, color=colorMap * 100, size=points_ratio[:, 4] * 5+1)
    # w.addItem(sp2)
    # QtGui.QApplication.instance().exec_()





