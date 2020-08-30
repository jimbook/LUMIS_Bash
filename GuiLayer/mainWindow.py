import os,sys, time
import threading
from PyQt5 import QtGui
from dataLayer.shareMemory import dataChannel
from pyqtgraph.dockarea import *
from dataLayer.connectionTools import linkGBT
from GuiLayer.myPlotWidget import subPlotWin_singal,subPlotWin_coincidence
from GuiLayer.myWidget import setConfigurationDailog
from dataLayer.dataStorage import addDataInMemory
from dataLayer.constantParameter import _Index
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow

class window(QMainWindow,Ui_MainWindow):
    updateSingal = pyqtSignal()
    messageSingal = pyqtSignal(str)
    def __init__(self,*args,manager = None):
        super(window, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore(manager)
        self.setEvent()

    def setMore(self,manager):
        self.init_loadConfigIndex()
        self.log = ""
        self.timer_measure = QTimer(self)
        self.timer_measure.setSingleShot(True)
        self.timer = QTimer(self)
        self.time = time.time()
        #从数据服务端获取共享对象
        self.dataChn = dataChannel(manager)
        # 单通道能谱
        self.comboBox_singal_tier.addItems(["0","1","2","3","4","5","6","7"])
        self.comboBox_singal_channel.addItems(_Index)
        # 符合能谱
        self.comboBox_coincidence_tier.addItems(["0","1","2","3","4","5","6","7"])
        self.comboBox_coincidence_showChannel.addItems(_Index)
        self.comboBox_coincidence_coinChannel.addItems(_Index)
        # 开启从数据服务进程接收消息的服务
        t = threading.Thread(target=self.getMessge)
        t.start()
        # 开启从数据服务进程接收数据的服务
        t_data = threading.Thread(target=self.synchronizeData)
        t_data.start()
        # 数据项
        self.dataInMemory = [] # 内存中的数据
        self.dataInDisk = [] # 硬盘中数据的路径

    def setEvent(self):
        #communication event
        self.pushButton_config.clicked.connect(self.sendConfigFile_event)
        self.pushButton_dataReceive.clicked.connect(self.switchReceiveDataThread_event)
        self.pushButton_sendCommand.clicked.connect(self.sendShortCommand_evet)
        #plot event
        self.pushButton_singal_addPlot.clicked.connect(self.plotSingalEnergySpectum_event)
        #auxiliary event
        self.messageSingal.connect(self.addMessage) # 将消息队列中的消息打印到消息栏
        # stop measurment
        self.timer_measure.timeout.connect(self.stopMeasurment_event)
        self.timer.timeout.connect(self.timeOut_event)
        # menu action event
        self.action_configuration.triggered.connect(self.action_configuration_event)


    # init: load config file index
    # 初始化：读入配置文件列表
    def init_loadConfigIndex(self):
        for _r,_d,files in os.walk(".\configurationFile"):
            configList = []
            for file in files:
                _e = os.path.splitext(file)
                print(_e)
                if (_e[-1] == '.lmbc') or (_e[-1] == '.dat'):
                    configList.append(file)
            self.comboBox_configFile.addItems(configList)

    # 线程函数：获取从数据服务中获取的消息，同时根据数据服务进程的状态使按钮可用
    def getMessge(self):
        while True:
            # 从消息队列中获取消息
            msg = self.dataChn.mq.get() # 会阻塞
            self.messageSingal.emit(msg)
            # 如果此时数据接收已经结束
            if self.dataChn.dataTag.is_set():
                # 让配置/开始接收数据按钮可用
                self.pushButton_sendCommand.setEnabled(True)
                self.pushButton_config.setEnabled(True)
                self.pushButton_dataReceive.setEnabled(True)
                # 让定时器可用
                self.checkBox_timer.setEnabled(True)
                self.spinBox_timer_minute.setEnabled(True)
                self.spinBox_timer_minute.setEnabled(True)

    # 线程函数：同步数据并更新图像
    def synchronizeData(self):
        self.dataChn.dataTag.wait()
        while True:
            _newData,_clearTag = self.dataChn.dataStorage.get_newData()
            if len(_newData) != 0:
                addDataInMemory(_newData,reset=_clearTag) # 向dataStorage添加新数据
                self.updateSingal.emit() # 更新图像
            print("数据同步成功")
            time.sleep(5)

    # 辅助函数：向area中添加图像
    def addPlot(self,widget: QWidget):
        try:
            name = widget.windowTitle()
            _dock = Dock(name=name, widget=widget,closable=True)
            self.dockArea.addDock(_dock)
        except:
            pass

    # auxiliary/event Function: add message to text Browser
    # 辅助函数/事件：向消息队列中添加消息
    @pyqtSlot(str)
    def addMessage(self,inputMessage: str):
        try:
            self.log += inputMessage+'\n'
            self.textBrowser_messageQueue.setPlainText(self.log)
            self.textBrowser_messageQueue.moveCursor(QTextCursor.End) # 设置自动滚动到底部
        except:
            import traceback
            traceback.print_exc()

    # event Function:send configuration file to device
    # 事件：发送配置文件
    @pyqtSlot()
    def sendConfigFile_event(self):
        filePath = os.path.join("./configurationFile", self.comboBox_configFile.currentText())
        self.addMessage("准备发送配置文件{0}".format(filePath))
        try:
            reply,message = linkGBT.sendConfigFile(filePath)
            if reply:
                self.addMessage("发送成功")
            else:
                self.addMessage("发送失败")
                self.addMessage(message)
        except Exception as e:
            self.addMessage("错误：")
            self.addMessage(e.__str__())

    # 事件：发送字符串指令
    @pyqtSlot()
    def sendShortCommand_evet(self):
        text = self.lineEdit_sendCommand.text()
        if len(text) == 4:
            cmd = bytes.fromhex(text)
            try:
                linkGBT.sendCommand(cmd)
                self.addMessage("成功发送命令：{}".format(cmd.hex('-')))
            except Exception as e:
                self.addMessage("发送命令失败\n{}".format(e.__str__()))
        else:
            self.addMessage("只能发送2bytes的命令！")

    # event: start or stop data receive thread.Meanwhile,it will show the measuring time.
    # 事件：通过更改标志来开启/结束数据接收线程
    @pyqtSlot(bool)
    def switchReceiveDataThread_event(self,switch: bool):
        try:
            if switch:
                self.time = time.time() #初始化时间
                self.dataChn.threadTag.set()
                self.pushButton_dataReceive.setText("停止接收数据")
                # 采集时禁止其他通讯方式使用TCP连接
                self.pushButton_config.setDisabled(True)
                self.pushButton_sendCommand.setDisabled(True)
                # 采集时禁止更改定时器
                self.checkBox_timer.setDisabled(True)
                self.spinBox_timer_minute.setDisabled(True)
                self.spinBox_timer_hour.setDisabled(True)
                if self.checkBox_timer.isChecked():
                    sec = self.spinBox_timer_hour.value() * 60 * 60 + self.spinBox_timer_minute.value() * 60
                    self.timer_measure.start(sec * 1000)
                self.timer.start(50)
            else:
                self.dataChn.threadTag.clear()
                self.pushButton_dataReceive.setText("开始接收数据")
                self.pushButton_dataReceive.setDisabled(True)
                self.addMessage("等待数据服务进程停止接收数据")
                self.timer.stop()
        except:
            import traceback
            traceback.print_exc()

    #事件：停止数据接收（由定时器触发）
    @pyqtSlot()
    def stopMeasurment_event(self):
        self.dataChn.threadTag.clear()
        self.pushButton_dataReceive.setText("开始接收数据")
        self.pushButton_dataReceive.setDisabled(True)
        self.addMessage("等待数据服务进程停止接收数据")
        self.timer.stop()

    # 事件：添加单通道能谱
    @pyqtSlot()
    def plotSingalEnergySpectum_event(self):
        singalEnergryPlot = subPlotWin_singal()
        _teir = int(self.comboBox_singal_tier.currentText())
        _channel = _Index.index(self.comboBox_singal_channel.currentText())
        singalEnergryPlot.setData(tier=_teir,channel=_channel)
        self.updateSingal.connect(singalEnergryPlot.dataUpdate)
        singalEnergryPlot.changeBaseLine(self.spinBox_baseLine.value())
        self.addPlot(singalEnergryPlot)

    # 事件：添加符合能谱
    @pyqtSlot()
    def plotCoincidenceEmergySpectrum_event(self):
        coincidenceEnergyPlot = subPlotWin_coincidence()
        _teir = int(self.comboBox_coincidence_tier.currentText())
        _channel = _Index.index(self.comboBox_coincidence_showChannel.currentText())
        _channel_coin = _Index.index(self.comboBox_coincidence_coinChannel.currentText())
        coincidenceEnergyPlot.setData(tier=_teir,channel=_channel,channel_coin=_channel_coin)
        self.updateSingal.connect(coincidenceEnergyPlot.dataUpdate)
        coincidenceEnergyPlot.changeBaseLine(self.spinBox_coincidence_baseline.value())
        self.addPlot(coincidenceEnergyPlot)

    # 事件：设置配置参数
    @pyqtSlot()
    def action_configuration_event(self):
        setConfigurationDailog().dialogShow()
        self.init_loadConfigIndex()

    #auxiliary: erver interval will call this function to refresh clock widget
    #辅助函数：每过一个时间间隔将会调用一次，来刷新时间显示控件显示的时间
    @pyqtSlot()
    def timeOut_event(self):
        _t = time.time() - self.time
        _hour = int(_t // (60*60) % 24)
        _min = int(_t % (60*60) // 60)
        _sec = _t % 60
        self.lcdNumber_s_ms.display("{:4.2f}".format(_sec))
        self.lcdNumber_h_m.display("{:0>d}:{:0>d}".format(_hour,_min))

    @pyqtSlot(QtGui.QCloseEvent)
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.dataChn.processTag.set()
        if self.pushButton_dataReceive.isChecked():
            self.switchReceiveDataThread_event(False)
        self.dataChn.dataTag.wait()
        super(window, self).closeEvent(a0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_())