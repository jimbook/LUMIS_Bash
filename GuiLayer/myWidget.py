import sys
import os
from dataLayer.configTools import configuration
from dataLayer.connectionTools import linkGBT
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget,QApplication,QLabel,QDoubleSpinBox,QDialog,QMessageBox,QGridLayout,QCheckBox,QSpinBox
from UI.configSaveAsDialog import Ui_Dialog
# 导出为配置文件-输入配置名-对话框
class configSaveAsDialog(QDialog,Ui_Dialog):
    def __init__(self,*args):
        super(configSaveAsDialog, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.OK = False

    def setEvent(self):
        self.pushButton_OK.clicked.connect(self.OK_event)
        self.pushButton_Cancel.clicked.connect(self.Cancel_event)

    @pyqtSlot()
    def OK_event(self):
        self.OK = True
        self.close()

    @pyqtSlot()
    def Cancel_event(self):
        self.close()

    @staticmethod
    def showDialog():
        dialog = configSaveAsDialog()
        dialog.exec_()
        return dialog.OK,dialog.lineEdit.text()

from UI.setConfigurtion_channelGroupBox_basic import Ui_Form
# 各个板的配置界面-基本-控件
# 不会根据输入的芯片参数来将电压转化为二进制命令码，而是直接修改命令码的值
class setConfiguration_channelWidget_basic(QWidget,Ui_Form):
    def __init__(self,*args):
        super(setConfiguration_channelWidget_basic, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.channelBiasSpinBoxList = []
        self._ChannelWidgetInit()
        self.checkBox_globalBias.setChecked(True)
        self.checkBox_globalBias_event(True)

    def setEvent(self):
        self.checkBox_globalBias.clicked.connect(self.checkBox_globalBias_event)
        self.spinBox_globalBais.valueChanged.connect(self.spinBox_globalBias_changeValue_event)

    # 事件：开启/关闭当前板各通道偏压全局设置
    @pyqtSlot(bool)
    def checkBox_globalBias_event(self,check: bool):
        for i in self.channelBiasSpinBoxList:
            i.setDisabled(check)
        self.spinBox_globalBais.setEnabled(check)

    # 事件：更改当前板各通道偏压
    @pyqtSlot(int)
    def spinBox_globalBias_changeValue_event(self, newValue: int):
        for i in self.channelBiasSpinBoxList:
            i.setValue(newValue)

    # 事件：开启/关闭各板阈值全局设置
    @pyqtSlot(bool)
    def globalThreshold_event(self,check: bool):
        self.spinBox_globalThreshole.setDisabled(check)

    # 事件：开启/关闭各板偏压全局设置
    @pyqtSlot(bool)
    def globalBias_event(self,check: bool):
        if check:
            self.spinBox_globalBais.setDisabled(check)
            for i in self.channelBiasSpinBoxList:
                i.setDisabled(check)
        else:
            self.spinBox_globalBais.setEnabled(self.checkBox_globalBias.isChecked())
            for i in self.channelBiasSpinBoxList:
                i.setDisabled(self.checkBox_globalBias.isChecked())
        self.checkBox_globalBias.setDisabled(check)


    # 辅助函数：初始化各个通道偏压的控件
    def _ChannelWidgetInit(self):
        for i in range(4):
            for j in range(8):
                _label = QLabel(text='通道{}'.format(i*8+j),parent=self)
                _spinBox = QSpinBox(parent=self)
                _spinBox.setMaximum(255)
                _spinBox.setMinimum(0)
                _spinBox.setValue(141)
                self.channelBiasSpinBoxList.append(_spinBox)
                self.gridLayout_channelBias.addWidget(_label,i*2,j)
                self.gridLayout_channelBias.addWidget(_spinBox,i*2+1,j)
        for j in range(4):
            _label = QLabel(text='通道{}'.format(32+j),parent=self)
            _spinBox = QSpinBox(parent=self)
            _spinBox.setMaximum(255)
            _spinBox.setMinimum(0)
            _spinBox.setValue(141)
            self.channelBiasSpinBoxList.append(_spinBox)
            self.gridLayout_spareChannelBias.addWidget(_label,0,j)
            self.gridLayout_spareChannelBias.addWidget(_spinBox,1,j)

    # 返回配置信息
    def configInfo(self) -> list:
        output = []
        output.append(self.spinBox_globalThreshole.value())
        if self.checkBox_globalBias.isChecked():
            for i in range(36):
                output.append(self.spinBox_globalBais.value())
        else:
            for i in self.channelBiasSpinBoxList:
                output.append(i.value())
        return output

from UI.setConfigurtionDailog_basic import Ui_Dialog
# 配置参数主界面-基本-对话框
# 不会根据输入的芯片参数来将电压转化为二进制命令码，而是直接修改命令码的值
class setConfigurationDailog_basic(QDialog, Ui_Dialog):
    def __init__(self, *args):
        super(setConfigurationDailog_basic, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.boardTabList = []
        self.triggerModeList = []
        self.spinBox.setValue(8)
        self._triggerModeWidgetInit()
        self.boardNumberChange_event(8)

    def setEvent(self):
        self.spinBox.valueChanged.connect(self.boardNumberChange_event)
        self.pushButton_exportAsFile.clicked.connect(self.exportConfigFile_event)
        self.pushButton_sendBinaryOrder.clicked.connect(self.sendConfigToDevice_event)

    # 事件：改变层数
    @pyqtSlot(int)
    def boardNumberChange_event(self, newValue: int):
        self.tabWidget.clear()
        self.boardTabList.clear()
        for i in self.triggerModeList:
            i.setDisabled(True)
        for i in range(newValue):
            _group = setConfiguration_channelWidget_basic()
            self.layout().addWidget(_group)
            self.boardTabList.append(_group)
            self.checkBox_globalThreshold.clicked.connect(_group.globalThreshold_event)
            self.checkBox_globalBias.clicked.connect(_group.globalBias_event)
            self.tabWidget.addTab(_group, '第{}层'.format(i))
            # 设置触发模块可用/禁用
            self.triggerModeList[i].setDisabled(False)
            # 设置阈值可用/禁用
            if self.checkBox_globalThreshold.isChecked():
                _group.globalThreshold_event(True)
            # 设置偏压可用/禁用
            if self.checkBox_globalBias.isChecked():
                _group.globalBias_event(True)

    # 事件：导出为配置文件
    @pyqtSlot()
    def exportConfigFile_event(self):
        OK, name = configSaveAsDialog.showDialog()
        if OK:
            path = os.path.join('..\configurationFile', os.path.splitext(name)[0] + '.lmbc')
            if os.path.exists(path):
                if QMessageBox.warning(self, '导出失败', '已经存在同名配置文件，是否覆盖该文件？', QMessageBox.Ok | QMessageBox.Cancel):
                    with open(path, 'wb') as file:
                        binary = self._getConfigBinary()
                        print(binary.hex())
                        file.write(binary)
            else:
                with open(path, 'wb') as file:
                    binary = self._getConfigBinary()
                    print(binary.hex())
                    file.write(binary)

    # 事件：发送配置命令
    @pyqtSlot()
    def sendConfigToDevice_event(self):
        _binary = self._getConfigBinary()
        try:
            linkGBT.sendCommand(_binary)
        except Exception as e:
            QMessageBox.Information(self, '错误', e.__str__())

    # 辅助函数：获取二进制配置命令
    def _getConfigBinary(self) -> bytes:
        config = configuration()
        config.setBoardsQuantity(self.spinBox.value())  # 设置板子数
        _trigger = []
        for i in range(self.spinBox.value()):
            # 添加触发模式信息
            if self.triggerModeList[i].isChecked():
                _trigger.append(i)
            # 获取对应板的配置信息
            l = self.boardTabList[i].configInfo()
            # 配置阈值
            if self.checkBox_globalThreshold.isChecked():
                config.setThreshold(self.spinBox_globalThreshold.value(), i)
            else:
                config.setThreshold(l[0], i)
            # 配置偏压
            for j in range(36):
                if self.checkBox_globalBias.isChecked():
                    config.setBiasVoltage(self.spinBox_globalBais.value(), boardID=i, channelID=j)
                else:
                    config.setBiasVoltage(l[j + 1], boardID=i, channelID=j)
        # 配置触发模式
        config.setTriggerMode(*_trigger)
        return config.getOrderBytes()

    # 辅助函数：初始化触发模式内容
    def _triggerModeWidgetInit(self):
        _layout = QGridLayout()
        self.groupBox_triggerMode.setLayout(_layout)
        for i in range(2):
            for j in range(4):
                _checkBox = QCheckBox('第{}层'.format(i * 4 + j), parent=self)
                _layout.addWidget(_checkBox, i, j)
                self.triggerModeList.append(_checkBox)

    @staticmethod
    # 开启当前对话框
    def dialogShow():
        dialog = setConfigurationDailog_basic()
        dialog.exec_()
        return None

#todo:根据不同的芯片获取不同的电压转换公式来配置偏压
from UI.setConfigurtionDailog import Ui_Dialog
# 配置参数主界面-对话框
class setConfigurationDailog(QDialog,Ui_Dialog):
    def __init__(self,*args):
        super(setConfigurationDailog, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.boardTabList = []
        self.triggerModeList = []
        self.spinBox.setValue(8)
        self._triggerModeWidgetInit()
        self.boardNumberChange_event(8)


    def setEvent(self):
        self.spinBox.valueChanged.connect(self.boardNumberChange_event)
        self.pushButton_exportAsFile.clicked.connect(self.exportConfigFile_event)
        self.pushButton_sendBinaryOrder.clicked.connect(self.sendConfigToDevice_event)

    # 事件：改变层数
    @pyqtSlot(int)
    def boardNumberChange_event(self,newValue: int):
        self.tabWidget.clear()
        self.boardTabList.clear()
        for i in self.triggerModeList:
            i.setDisabled(True)
        for i in range(newValue):
            _group = setConfiguration_channelWidget()
            self.layout().addWidget(_group)
            self.boardTabList.append(_group)
            self.checkBox_globalThreshold.clicked.connect(_group.globalThreshold_event)
            self.checkBox_globalBias.clicked.connect(_group.globalBias_event)
            self.tabWidget.addTab(_group,'第{}层'.format(i))
            # 设置触发模块可用/禁用
            self.triggerModeList[i].setDisabled(False)
            # 设置阈值可用/禁用
            if self.checkBox_globalThreshold.isChecked():
                _group.globalThreshold_event(True)
            # 设置偏压可用/禁用
            if self.checkBox_globalBias.isChecked():
                _group.globalBias_event(True)

    # 事件：导出为配置文件
    @pyqtSlot()
    def exportConfigFile_event(self):
        OK,name = configSaveAsDialog.showDialog()
        if OK:
            path = os.path.join('.\configurationFile', os.path.splitext(name)[0] + '.lmbc')
            if os.path.exists(path):
                if QMessageBox.warning(self,'导出失败','已经存在同名配置文件，是否覆盖该文件？',QMessageBox.Ok | QMessageBox.Cancel):
                    with open(path,'wb') as file:
                        binary = self._getConfigBinary()
                        print(binary.hex())
                        file.write(binary)
            else:
                with open(path, 'wb') as file:
                    binary = self._getConfigBinary()
                    print(binary.hex())
                    file.write(binary)

    # 事件：发送配置命令
    @pyqtSlot()
    def sendConfigToDevice_event(self):
        _binary = self._getConfigBinary()
        try:
            linkGBT.sendCommand(_binary)
        except Exception as e:
            QMessageBox.Information(self,'错误',e.__str__())

    # 辅助函数：获取二进制配置命令
    def _getConfigBinary(self) ->bytes:
        config = configuration()
        config.setBoardsQuantity(self.spinBox.value())  # 设置板子数
        _trigger = []
        for i in range(self.spinBox.value()):
            # 添加触发模式信息
            if self.triggerModeList[i].isChecked():
                _trigger.append(i)
            # 获取对应板的配置信息
            l = self.boardTabList[i].configInfo()
            # 配置阈值
            if self.checkBox_globalThreshold.isChecked():
                config.setThreshold(self.spinBox_globalThreshold.value(), i)
            else:
                config.setThreshold(l[0], i)
            # 配置偏压
            for j in range(36):
                if self.checkBox_globalBias.isChecked():
                    config.setBiasVoltage(self.doubleSpinBox_globalBias.value(), boardID=i, channelID=j)
                else:
                    config.setBiasVoltage(l[j + 1], boardID=i, channelID=j)
        # 配置触发模式
        config.setTriggerMode(*_trigger)
        return config.getOrderBytes()

    # 辅助函数：初始化触发模式内容
    def _triggerModeWidgetInit(self):
        _layout = QGridLayout()
        self.groupBox_triggerMode.setLayout(_layout)
        for i in range(2):
            for j in range(4):
                _checkBox = QCheckBox('第{}层'.format(i*4+j),parent=self)
                _layout.addWidget(_checkBox,i, j)
                self.triggerModeList.append(_checkBox)

    @staticmethod
    # 开启当前对话框
    def dialogShow():
        dialog = setConfigurationDailog()
        dialog.exec_()
        return None

from UI.setConfigurtion_channelGroupBox import Ui_Form
# 各个板的配置界面-转换为电压-控件
class setConfiguration_channelWidget(QWidget,Ui_Form):
    def __init__(self,*args):
        super(setConfiguration_channelWidget, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.channelBiasSpinBoxList = []
        self._ChannelWidgetInit()
        self.checkBox_globalBias.setChecked(True)
        self.checkBox_globalBias_event(True)

    def setEvent(self):
        self.checkBox_globalBias.clicked.connect(self.checkBox_globalBias_event)
        self.doubleSpinBox_globalBias.valueChanged.connect(self.doubleSpinBox_globalBias_changeValue_event)

    # 事件：开启/关闭当前板各通道偏压全局设置
    @pyqtSlot(bool)
    def checkBox_globalBias_event(self,check: bool):
        for i in self.channelBiasSpinBoxList:
            i.setDisabled(check)
        self.doubleSpinBox_globalBias.setEnabled(check)

    # 事件：更改当前板各通道偏压
    @pyqtSlot(float)
    def doubleSpinBox_globalBias_changeValue_event(self, newValue: float):
        for i in self.channelBiasSpinBoxList:
            i.setValue(newValue)

    # 事件：开启/关闭各板阈值全局设置
    @pyqtSlot(bool)
    def globalThreshold_event(self,check: bool):
        self.spinBox_globalThreshole.setDisabled(check)

    # 事件：开启/关闭各板偏压全局设置
    @pyqtSlot(bool)
    def globalBias_event(self,check: bool):
        if check:
            self.doubleSpinBox_globalBias.setDisabled(check)
            for i in self.channelBiasSpinBoxList:
                i.setDisabled(check)
        else:
            self.doubleSpinBox_globalBias.setEnabled(self.checkBox_globalBias.isChecked())
            for i in self.channelBiasSpinBoxList:
                i.setDisabled(self.checkBox_globalBias.isChecked())
        self.checkBox_globalBias.setDisabled(check)


    # 辅助函数：初始化各个通道偏压的控件
    def _ChannelWidgetInit(self):
        for i in range(4):
            for j in range(8):
                _label = QLabel(text='通道{}'.format(i*8+j),parent=self)
                _spinBox = QDoubleSpinBox(parent=self)
                _spinBox.setMaximum(29.29)
                _spinBox.setMinimum(25.29)
                _spinBox.setSuffix("V")
                _spinBox.setValue(28.50)
                self.channelBiasSpinBoxList.append(_spinBox)
                self.gridLayout_channelBias.addWidget(_label,i*2,j)
                self.gridLayout_channelBias.addWidget(_spinBox,i*2+1,j)
        for j in range(4):
            _label = QLabel(text='通道{}'.format(32+j),parent=self)
            _spinBox = QDoubleSpinBox(parent=self)
            _spinBox.setMaximum(29.29)
            _spinBox.setMinimum(25.29)
            _spinBox.setSuffix("V")
            _spinBox.setValue(28.50)
            self.channelBiasSpinBoxList.append(_spinBox)
            self.gridLayout_spareChannelBias.addWidget(_label,0,j)
            self.gridLayout_spareChannelBias.addWidget(_spinBox,1,j)

    # 返回配置信息
    def configInfo(self) -> list:
        output = []
        output.append(self.spinBox_globalThreshole.value())
        if self.checkBox_globalBias.isChecked():
            for i in range(36):
                output.append(self.doubleSpinBox_globalBias.value())
        else:
            for i in self.channelBiasSpinBoxList:
                output.append(i.value())
        return output
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = setConfigurationDailog_basic()
    b = ex._getConfigBinary()
    print(b.hex('-'))
    with open('../configurationFile/config2020_9_5.dat','wb') as file:
        file.write(b)
    ex.show()
    sys.exit(app.exec_())