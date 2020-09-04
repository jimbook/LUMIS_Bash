# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\setConfigurtion_channelGroupBox_unfit.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(697, 299)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_5.addWidget(self.label_4)
        self.spinBox_globalThreshole = QtWidgets.QSpinBox(Form)
        self.spinBox_globalThreshole.setMaximum(1023)
        self.spinBox_globalThreshole.setProperty("value", 280)
        self.spinBox_globalThreshole.setObjectName("spinBox_globalThreshole")
        self.horizontalLayout_5.addWidget(self.spinBox_globalThreshole)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.spinBox_globalBais = QtWidgets.QSpinBox(Form)
        self.spinBox_globalBais.setMaximum(255)
        self.spinBox_globalBais.setProperty("value", 141)
        self.spinBox_globalBais.setObjectName("spinBox_globalBais")
        self.horizontalLayout_5.addWidget(self.spinBox_globalBais)
        self.checkBox_globalBias = QtWidgets.QCheckBox(Form)
        self.checkBox_globalBias.setObjectName("checkBox_globalBias")
        self.horizontalLayout_5.addWidget(self.checkBox_globalBias)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_14 = QtWidgets.QLabel(Form)
        self.label_14.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_3.addWidget(self.label_14)
        self.line_2 = QtWidgets.QFrame(Form)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout_3.addWidget(self.line_2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.gridLayout_channelBias = QtWidgets.QGridLayout()
        self.gridLayout_channelBias.setObjectName("gridLayout_channelBias")
        self.verticalLayout.addLayout(self.gridLayout_channelBias)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_31 = QtWidgets.QLabel(Form)
        self.label_31.setMinimumSize(QtCore.QSize(70, 0))
        self.label_31.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_31.setObjectName("label_31")
        self.horizontalLayout_2.addWidget(self.label_31)
        self.line_3 = QtWidgets.QFrame(Form)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.horizontalLayout_2.addWidget(self.line_3)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout_spareChannelBias = QtWidgets.QGridLayout()
        self.gridLayout_spareChannelBias.setObjectName("gridLayout_spareChannelBias")
        self.horizontalLayout.addLayout(self.gridLayout_spareChannelBias)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_4.setText(_translate("Form", "阈值："))
        self.label_5.setText(_translate("Form", "全局偏压："))
        self.checkBox_globalBias.setText(_translate("Form", "全部设为此"))
        self.label_14.setText(_translate("Form", "各通道偏压"))
        self.label_31.setText(_translate("Form", "备用通道偏压"))

