from dataLayer.calculateForPoca import *
from poca import POCA_Analysis
from dataLayer.baseCore import h5Data
if __name__ == '__main__':
    # d = pd.read_csv("./tmpStorage/channelReplace.csv")
    data_L = h5Data("./testData/h5Data/tempData_10.28_10_20_54.h5","r")
    data_Z = h5Data("./testData/h5Data/tempData_10.27_14_12_02.h5","r")
    data_U = h5Data("./testData/h5Data/tempData_10.30_13_19_39.h5", "r")
    data = data_L.getData(-2)
    fd = pocaAnalizy(data)
    # pos = fd.HitPositions
    # Ana = POCA_Analysis()
    # for i in pos:
    #     _df = i.reshape((12,))
    #     Ana.run_poca(_df)
    # Ana.poca_imaging()

    # data = pd.read_csv('./testData/csvData/tempData_10.27_14_12_02poca_data.csv', header=0, index_col=0, sep='\t')
    # pos = data.values[:,:12].reshape((-1,4,3))
    # poca = calculatePocaPostions_forNumba(pos)


    # start = time.time()
    # points_ratio = ratio_main(_poca,pd.read_csv("./tmpStorage/detectPlace.csv",header=0,index_col=0).values)
    # print("poca event:{},ratio running time:{}s".format(_poca.shape[0],time.time()-start))
    # print(points_ratio.shape)

    # 3D
    poca = fd.pocaPositions
    poca = poca[(poca[:,3] > 10) & (poca[:,3] <30)]
    poca = poca[(poca[:,2] > 600) & (poca[:,2] < 850)]

    from pyqtgraph.Qt import QtCore, QtGui
    import pyqtgraph.opengl as gl
    import pyqtgraph as pg
    app = QtGui.QApplication([])
    w = gl.GLViewWidget()
    w.opts['distance'] = 20
    w.show()
    w.setWindowTitle('3D example')
    g = gl.GLGridItem()
    w.addItem(g)
    colorMap = pg.ColorMap(np.array([0,10,20,30]),
                           np.array([[1,1,1,0.3],[1,1,0,0.6],[0,0,1,0.6],[0,0,0,0.6]])
                           ,pg.ColorMap.RGB).mapToFloat(poca[:,3])
    colorMap[:,3] = 0.006
    sp2 = gl.GLScatterPlotItem(pos=poca[:,:3]/100, color=colorMap*100, size=poca[:,3]/np.max(poca[:,3]) * 10)
    w.addItem(sp2)
    # colorMap = pg.ColorMap(np.array([0, 10, 20, 30]),
    #                        np.array([[1, 1, 1, 0.3], [1, 1, 0, 0.6], [0, 0, 1, 0.6], [0, 0, 0, 0.6]]),
    #                        pg.ColorMap.RGB).mapToFloat(points_ratio[:, 4])
    # colorMap[:, 3] = 0.006
    # sp2 = gl.GLScatterPlotItem(pos=points_ratio[:, :3] / 100, color=colorMap * 100, size=points_ratio[:, 4] * 5+1)
    # w.addItem(sp2)
    QtGui.QApplication.instance().exec_()





