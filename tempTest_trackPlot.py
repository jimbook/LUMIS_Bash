import sys
from PyQt5.Qt import QApplication
from dataLayer.baseCore import h5Data
from dataLayer.calculationTools import ChooseGoodEvent
from GuiLayer.myPlotWidget import subPlotWin_eventTrackShow
import pyqtgraph.examples
pyqtgraph.examples.run()

# if __name__=='__main__':
#     data = h5Data('data/2020_10_06/temp_1.h5', 'r')
#     d = data.getData(index=-2)
#     print(d.shape)
#     event = ChooseGoodEvent(d)
#     print(event.shape)
#     app=QApplication(sys.argv)
#     demo = subPlotWin_eventTrackShow()
#     demo.setData(event.values)
#     demo.show()
#     sys.exit(app.exec_())


# if __name__ =='__main__':
#     app = QApplication(sys.argv)
#     demo = TriangleDrawing()
#     demo.show()
#     sys.exit(app.exec_())