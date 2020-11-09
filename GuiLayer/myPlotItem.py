import sys
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import dataLayer
class boardBarsPlot(QWidget):
    def __init__(self,*args, boardNum: int):
        super(boardBarsPlot, self).__init__(*args)
        self.boardNum = boardNum
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.setGeometry(300, 300, 1400, 150)
        self.boardData = np.zeros(32,'int64')
        self.setMinimumSize(850, 120)
        self.barSize = 5
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor(255,255,255))
        self.setPalette(palette)

    def setEvent(self):
        pass

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        super(boardBarsPlot, self).mousePressEvent(a0)
        print(a0.pos())

    # 设置数据
    def setBoardData(self, data: np.array):
        if data.shape == (38,):
            self.boardData = data
        else:
            raise ValueError('The shape of argument(data) should be (36+,)')

    # 绘图事件
    def paintEvent(self, a0: QPaintEvent) -> None:
        #super(boardBarsPlot, self).paintEvent(a0)
        qp = QPainter()
        qp.begin(self)
        self.drawingTitile(qp)
        self.drawingTriangle(qp)
        self.drawingHistogram(qp)
        qp.end()

    # 辅助函数：绘制标题
    def drawingTitile(self, qp: QPainter):
        pen = QPen(Qt.black)
        qp.setPen(pen)
        qp.setFont(QFont('SimSun', 8))
        rect = QRect(
            QPoint(int(0.2/34 * self.size().width()),int(2 / 10 * self.size().height())),
            QPoint(int(1/34 * self.size().width()), int(6 / 10 * self.size().height()))
        )
        qp.drawText(rect, Qt.AlignCenter, '第\n{}\n层'.format(self.boardNum))

    # 辅助函数：绘制直方图函数
    def drawingHistogram(self, qp: QPainter):
        # 绘制x轴
        pen = QPen(Qt.black)
        qp.setPen(pen)
        line = QLine(
            int(1/34 * self.size().width()), int(4.5 / 10 * self.size().height()),
            int(33/34 * self.size().width()),int(4.5 / 10 * self.size().height())
                     )
        qp.drawLine(line)
        # 绘制标签
        if self.size().width() > 1500:
            fontPointSize = 8
        elif self.size().width() > 1000:
            fontPointSize = 5 + (self.size().width() - 1000) / 166
        else:
            fontPointSize = 5
        qp.setFont(QFont('SimSun', fontPointSize))
        for i in range(32):
            rect = QRect(
                QPoint(int((i + 0.5)/34 * self.size().width()), int(4.5 / 10 * self.size().height())),
                QPoint(int((i + 2.5) / 34 * self.size().width()), int(4.5 / 10 * self.size().height() + 15))
                         )
            qp.drawText(rect, Qt.AlignCenter, str(dataLayer._Index[i]))
            len = QLine(
                QPoint(int((i+1.5)/34 * self.size().width()), int(4.5 / 10 * self.size().height() + 2)),
                QPoint(int((i + 1.5) / 34 * self.size().width()), int(4.5 / 10 * self.size().height()))
            )
            qp.drawLine(len)
        # 绘制数据bar
        pen = QPen(QColor(0, 0, 0, alpha=0))
        qp.setPen(pen)
        brush = QBrush(QColor('#0497DE'))
        qp.setBrush(brush)

        maxHeight = 0.5 / 10 * self.size().height() - 4.5 / 10 * self.size().height() - 1
        for i in range(32):
            if self.boardData[i] != 0:
                h = maxHeight * self.boardData[i] / 1000
                rect = QRect(
                    QPoint(int((i+1.5)/34 * self.size().width() - self.barSize), int(4.5 / 10 * self.size().height() - 1 + h)),
                    QPoint(int((i+1.5)/34 * self.size().width() + self.barSize), int(4.5 / 10 * self.size().height() - 1))
                )
                qp.drawRect(rect)

    #辅助函数：绘制三角形
    def drawingTriangle(self,qp: QPainter):
        up = True
        for i in range(32):
            # 设置颜色变化
            if self.boardData[i] == 0:
                brush = QBrush(QColor('#37DE6A'))
            elif self.boardData[i] > 800:
                brush = QBrush(QColor(255, 0, 0))
            else:
                r = int((800 - self.boardData[i]) / (800 - 150) * 255)
                brush = QBrush(QColor(255, r, r))
            qp.setBrush(brush)

            pen = QPen(Qt.white, 1, Qt.SolidLine)
            qp.setPen(pen)

            polygon = self.trianglePointF(i, up)
            up = not up
            qp.drawConvexPolygon(polygon)
            fontPointSize = int(1 / 150 * (self.size().width() ** 2 + self.size().width() ** 2) ** 0.5 - 3)
            qp.setFont(QFont('SimSun', fontPointSize))

            rect = QRect(
                QPoint(int((i + 0.5) / 34 * self.size().width()), int(6 / 10 * self.size().height())),
                QPoint(int((i + 2.5) / 34 * self.size().width()), int(9 / 10 * self.size().height()))
            )
            qp.drawText(rect, Qt.AlignCenter, str(self.boardData[i]))

    # 辅助函数：返回第i个三角形对象
    def trianglePointF(self, vertex_x: int, upsideDown: bool):
        p = vertex_x + 0.5
        if upsideDown:
            return QPolygonF([
                QPoint(int(p / 34 * self.size().width()), int(6 / 10 * self.size().height())),
                QPoint(int((p + 2) / 34 * self.size().width()), int(6 / 10 * self.size().height())),
                QPoint(int((p + 1) / 34 * self.size().width()), int(9 / 10 * self.size().height()))
            ])
        else:
            return QPolygonF([
                QPoint(int(p / 34 * self.size().width()), int(9 / 10 * self.size().height())),
                QPoint(int((p + 2) / 34 * self.size().width()), int(9 / 10 * self.size().height())),
                QPoint(int((p + 1) / 34 * self.size().width()), int(6 / 10 * self.size().height()))
            ])

class xyBoardsPlot(QWidget):
    def __init__(self, *args, boardNum: int):
        super(xyBoardsPlot, self).__init__(*args)
        self.boardNum = boardNum
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.setGeometry(300, 300, 420, 420)
        self.setMinimumSize(QSize(420,420))
        self.xData = np.zeros(32,'int64')
        self.yData = np.zeros(32, 'int64')
        palette = QPalette()
        palette.setColor(self.backgroundRole(), QColor(255,255,255))
        self.setPalette(palette)

    def setEvent(self):
        pass

    def setBoardsData(self,xData: np.array, yData: np.array):
        if xData.shape[0] != 38:
            raise ValueError('The shape of argument(xData) should be (38,)')
        elif yData.shape[0] != 38:
            raise ValueError('The shape of argument(yData) should be (38,)')
        else:
            self.xData = xData
            self.yData = yData
        self.repaint()

    def resizeEvent(self, a0: QResizeEvent):
        if a0.size().width() == a0.size().height():
            super(xyBoardsPlot, self).resizeEvent(a0)
        else:
            s = max(a0.size().width(), a0.size().height())
            self.resize(s, s)


    def paintEvent(self, a0: QPaintEvent):
        qp = QPainter()
        qp.begin(self)
        self.drawingText(qp)
        self.drawingRectangle(qp)
        qp.end()

    # 绘制标签
    def drawingText(self, qp: QPainter):
        pen = QPen(Qt.black)
        qp.setPen(pen)
        if self.size().width() > 1000:
            fontPointSize = 9
        elif self.size().width() > 600:
            fontPointSize = 5 + (self.size().width() - 600) / 100
        else:
            fontPointSize = 5
        qp.setFont(QFont('SimSun', int(fontPointSize)))
        # 绘制x轴的标签
        for i in range(32):
            p = i + 1.5
            rect = QRect(
                QPoint(int(p / 36 * self.size().width()), int(0.5 / 36 * self.size().height())),
                QPoint(int((p + 1) / 36 * self.size().width()), int(1.5 / 36 * self.size().height()))
            )
            qp.drawText(rect, Qt.AlignCenter, str(i))
        # 绘制y轴的标签
        for i in range(32):
            p = i + 1.5
            rect = QRect(
                QPoint(int(0.5 / 36 * self.size().width()), int(p / 36 * self.size().height())),
                QPoint(int(1.5 / 36 * self.size().width()), int((p + 1) / 36 * self.size().height()))
            )
            qp.drawText(rect, Qt.AlignCenter, str(i))
        # 绘制轴标签
        xRect = QRect(
            QPoint(int(33.5 / 36 * self.size().width()), int(1.5 / 36 * self.size().height())),
            QPoint(int(34.5 / 36 * self.size().width()), int(33.5 / 36 * self.size().height()))
        )
        qp.drawText(xRect, Qt.AlignCenter, '第\n{}{}\n层'.format(self.boardNum*2, self.boardNum * 2 + 1))
        # yRect = QRect(
        #     QPoint(int(1.5 / 36 * self.size().width()), int(33.5 / 36 * self.size().height())),
        #     QPoint(int(33.5 / 36 * self.size().width()),int(34.5 / 36 * self.size().height()))
        # )
        # qp.drawText(yRect, Qt.AlignCenter, '第{}层'.format(self.boardNum * 2 + 1))


    # 绘制bar网格
    def drawingRectangle(self,qp: QPainter):
        pen = QPen(QColor(0,0,0,alpha=0),1)
        qp.setPen(pen)
        for i in range(32):
            rect = self.barPointF(i,True)
            if self.xData[i] == 0:
                brush = QBrush(QColor(0, 204, 0, alpha=70))
            elif self.xData[i] > 800:
                brush = QBrush(QColor(255, 0, 0, alpha=70))
            else:
                r = int((800 - self.xData[i]) / (800 - 150) * 255)
                brush = QBrush(QColor(255, r, r, alpha=70))
            qp.setBrush(brush)
            qp.drawRect(rect)
        for i in range(32):
            rect = self.barPointF(i, False)
            if self.yData[i] == 0:
                brush = QBrush(QColor(0, 204, 0, alpha=70))
            elif self.yData[i] > 800:
                brush = QBrush(QColor(255, 0, 0, alpha=70))
            else:
                r = int((800 - self.yData[i]) / (800 - 150) * 255)
                brush = QBrush(QColor(255, r, r, alpha=70))
            qp.setBrush(brush)
            qp.drawRect(rect)

    # 辅助函数：返回目标方向的第i个矩形
    def barPointF(self,vertex: int, direction_up: bool) -> QRect:
        p = vertex + 1.5
        if direction_up:
            rect = QRect(
                QPoint(int(p / 36 * self.size().width()), int(1.5 / 36 * self.size().height())),
                QPoint(int((p + 1) / 36 * self.size().width()), int(33.5 / 36 * self.size().height()))
            )
        else:
            rect = QRect(
                QPoint(int(1.5 / 36 * self.size().width()), int(p / 36 * self.size().height())),
                QPoint(int(33.5 / 36 * self.size().width()), int((p + 1) / 36 * self.size().height()))
            )
        return rect



if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = xyBoardsPlot(boardNum=1)
    demo.show()
    x = np.zeros(38,'int64')
    y = np.zeros(38, 'int64')
    x[16] = 466
    x[17] = 800
    y[18] = 799
    y[19] = 350
    demo.setBoardsData(x,y)

    sys.exit(app.exec_())