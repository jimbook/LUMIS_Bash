# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\myPlot.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(980, 614)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = GraphicsView(Form)
        self.graphicsView.setObjectName("graphicsView")
        self.verticalLayout.addWidget(self.graphicsView)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.spinBox_baseLine = QtWidgets.QSpinBox(Form)
        self.spinBox_baseLine.setMaximum(4095)
        self.spinBox_baseLine.setObjectName("spinBox_baseLine")
        self.horizontalLayout_3.addWidget(self.spinBox_baseLine)
        self.horizontalSlider_baseLine = QtWidgets.QSlider(Form)
        self.horizontalSlider_baseLine.setMaximumSize(QtCore.QSize(100, 16777215))
        self.horizontalSlider_baseLine.setMaximum(4095)
        self.horizontalSlider_baseLine.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_baseLine.setObjectName("horizontalSlider_baseLine")
        self.horizontalLayout_3.addWidget(self.horizontalSlider_baseLine)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setMaximumSize(QtCore.QSize(16777215, 30))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.label_count = QtWidgets.QLabel(Form)
        self.label_count.setMinimumSize(QtCore.QSize(30, 0))
        self.label_count.setMaximumSize(QtCore.QSize(16777215, 30))
        self.label_count.setText("")
        self.label_count.setObjectName("label_count")
        self.horizontalLayout.addWidget(self.label_count)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_2.setText(_translate("Form", "设置基线"))
        self.label.setText(_translate("Form", "计数："))

from pyqtgraph import GraphicsView
