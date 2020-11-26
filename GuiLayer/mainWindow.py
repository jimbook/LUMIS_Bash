import os
import sys
import time
import threading
from multiprocessing import Queue
import numpy as np
from PyQt5 import QtGui
from pyqtgraph.dockarea import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from GuiLayer.myPlotWidget import subPlotWin_singal,subPlotWin_coincidence, subPlotWin_eventTrackShow, subPlotWin_eventXYTrackShow,GL3DWidget
from GuiLayer.myWidget import setConfigurationDailog_basic
from dataLayer import _Index
from dataLayer.connectionTools import linkGBT
from dataLayer.baseCore import shareStorage, h5Data
from dataLayer import dataStorage
from UI.mainWindow import Ui_MainWindow

class window(QMainWindow,Ui_MainWindow):
    updateSingal = pyqtSignal(int)
    messageSingal = pyqtSignal(str)

    def __init__(self,*args,shareChannel: shareStorage):
        super(window, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore(shareChannel)
        self.setEvent()

    def setMore(self,s: shareStorage):
        self.init_loadConfigIndex()
        self.log = ""
        self.timer_measure = QTimer(self)
        self.timer_measure.setSingleShot(True)
        self.timer = QTimer(self)
        self.time = time.time()
        #从数据服务端获取共享对象
        self.dataChn = s
        # 单通道能谱
        self.comboBox_singal_tier.addItems(["0","1","2","3","4","5","6","7"])
        self.comboBox_singal_channel.addItems(_Index[:-3])
        # 符合能谱
        self.comboBox_coincidence_tier.addItems(["0","1","2","3","4","5","6","7"])
        self.comboBox_coincidence_showChannel.addItems(_Index[:-3])
        self.comboBox_coincidence_coinChannel.addItems(_Index[:-3])
        # 开启从数据服务进程接收消息的服务
        self.orderQueue = Queue()
        t = threading.Thread(target=self.getMessge)
        t.start()
        # # 开启从数据服务进程接收数据的服务
        # t_data = threading.Thread(target=self.synchronizeData)
        # t_data.start()
        # 数据项
        self.dataInMemory = [] # 内存中的数据
        self.dataInDisk = [] # 硬盘中数据的路径

    def setEvent(self):
        #communication event
        self.pushButton_clockSynchronization.clicked.connect(self.sendClockSynch_event)
        self.pushButton_reset.clicked.connect(self.sendResetOrder_event)
        self.pushButton_config.clicked.connect(self.sendConfigFile_event)
        self.pushButton_dataReceive.clicked.connect(self.switchReceiveDataThread_event)
        self.pushButton_sendCommand.clicked.connect(self.sendShortCommand_evet)
        #plot event
        self.pushButton_singal_addPlot.clicked.connect(self.plotSingalEnergySpectum_event)
        self.pushButton_coincidence_addPlot.clicked.connect(self.plotCoincidenceEmergySpectrum_event)
        self.pushButton_triggerCondition_addPlot.clicked.connect(self.plotTriggerCondition_event)
        self.pushButton_XYTriggerCondition_addPlot.clicked.connect(self.plotXYTrtggerCondition_event)
        self.pushButton_threeD_addPlot.clicked.connect(self.plot3D_event)
        #auxiliary event
        self.messageSingal.connect(self.addMessage) # 将消息队列中的消息打印到消息栏
        # stop measurment
        self.timer_measure.timeout.connect(self.stopMeasurment_event)
        self.timer.timeout.connect(self.timeOut_event)
        # menu action event
        self.action_configuration.triggered.connect(self.action_configuration_event)
        self.action_baseline_measureBaseline.triggered.connect(self.action_receiveBaselineDataThread_event)
        self.action_offlineDataShow.triggered.connect(self.action_offlineDataShow_event)
        self.action_dataPlayBack.triggered.connect(self.action_dataPlayBack_event)

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
            m = self.dataChn.messageQueue().get() # 会阻塞
            result, msg = m[0], m[1:]
            msg = msg[-1]
            self.messageSingal.emit(msg)
            # 如果数据正常接收
            if result == 0:
                dataStorage.update()
                self.updateSingal.emit(0)  # 更新图像
            else:
                order = self.orderQueue.get()
                if result == -1 or result == -2: # 表示数据接收失败
                    self.setEnableReceiveItem(True)
                    # todo:
                elif result == 1 or result == 2:
                    if order == 0:              # 表示数据接收正常结束
                        self.setEnableReceiveItem(True)
                    elif order == 1 or isinstance(order, str): # 数据开始接收，需要重置dataStorage并初始化
                        self.pushButton_dataReceive.setEnabled(True)
                        dataStorage.clearAllData()
                        h5path = self.dataChn.getFilePath()
                        dataStorage.setH5Path(h5path)
                        self.updateSingal.emit(0)  # 更新图像

    # 辅助函数：向area中添加图像
    def addPlot(self,widget: QWidget):
        try:
            name = widget.windowTitle()
            _dock = Dock(name=name, widget=widget,closable=True)
            self.dockArea.addDock(_dock)
        except:
            pass

    # 辅助函数：设置数据接收按钮和定时器可用与否
    def setEnableReceiveItem(self, a0: bool):
        # 配置/开始接收数据按钮
        self.pushButton_sendCommand.setEnabled(a0)
        self.pushButton_config.setEnabled(a0)
        self.pushButton_dataReceive.setEnabled(a0)
        # 定时器
        self.checkBox_timer.setEnabled(a0)
        self.spinBox_timer_minute.setEnabled(a0)
        self.spinBox_timer_hour.setEnabled(a0)

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

    #事件：连接操作，发送同步时钟指令
    @pyqtSlot()
    def sendClockSynch_event(self):
        try:
            reply, message = linkGBT.sendCommand(b'\xff\x03')
            if reply:
                self.addMessage('已发送同步时钟指令')
            else:
                self.addMessage('发送同步时钟命令失败')
                self.addMessage(message)
        except Exception as e:
            self.addMessage('错误：')
            self.addMessage(e.__str__())

    # 事件：连接操作-发送复位命令
    @pyqtSlot()
    def sendResetOrder_event(self):
        try:
            reply,message = linkGBT.sendCommand(b'\xff\x02')
            if reply:
                self.addMessage('已发送复位指令')
            else:
                self.addMessage('发送复位命令失败')
                self.addMessage(message)
        except Exception as e:
            self.addMessage('错误：')
            self.addMessage(e.__str__())

    # event Function:connect-send configuration file to device
    # 事件：连接操作-发送配置文件
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

    # 事件：连接操作-发送字符串指令
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

    # 事件：连接操作-通过管道发送命令来开启/结束基线数据接收线程
    @pyqtSlot()
    def action_receiveBaselineDataThread_event(self):
        try:
            self.time = time.time()  # 初始化时间
            self.dataChn.orderPipe(True).send(2)
            self.orderQueue.put(1)
            self.pushButton_dataReceive.setText("停止接收数据")
            # 采集时禁止其他通讯方式使用TCP连接
            self.setEnableReceiveItem(False)
            if self.checkBox_timer.isChecked():
                sec = self.spinBox_timer_hour.value() * 60 * 60 + self.spinBox_timer_minute.value() * 60
                self.timer_measure.start(sec * 1000)
            self.timer.start(50)
        except:
            import traceback
            traceback.print_exc()

    # event: connect-start or stop data receive thread.Meanwhile,it will show the measuring time.
    # 事件：连接操作-通过管道发送命令来开启/结束数据接收线程
    @pyqtSlot(bool)
    def switchReceiveDataThread_event(self,switch: bool):
        try:
            if switch:
                self.time = time.time() #初始化时间
                self.dataChn.orderPipe(True).send(1)
                self.orderQueue.put(1)
                self.pushButton_dataReceive.setText("停止接收数据")
                # 采集时禁止其他通讯方式使用TCP连接
                self.setEnableReceiveItem(False)
                if self.checkBox_timer.isChecked():
                    sec = self.spinBox_timer_hour.value() * 60 * 60 + self.spinBox_timer_minute.value() * 60
                    self.timer_measure.start(sec * 1000)
                self.timer.start(50)
            else:
                # 调用函数来停止数据接收
                self.stopMeasurment_event()
        except:
            import traceback
            traceback.print_exc()

    #事件：停止数据接收（由定时器触发）
    @pyqtSlot()
    def stopMeasurment_event(self):
        self.dataChn.orderPipe(True).send(0)
        self.orderQueue.put(0)
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

    # 事件：添加触发展示
    @pyqtSlot()
    def plotTriggerCondition_event(self):
        plot = subPlotWin_eventTrackShow()
        self.updateSingal.connect(plot.dataUpdate)
        plot.dataUpdate()
        self.addPlot(plot)

    #事件：添加xy触发展示
    @pyqtSlot()
    def plotXYTrtggerCondition_event(self):
        plot = subPlotWin_eventXYTrackShow()
        self.updateSingal.connect(plot.dataUpdate)
        plot.dataUpdate()
        self.addPlot(plot)

    #事件：显示3D成像
    @pyqtSlot()
    def plot3D_event(self):
        plot = GL3DWidget()
        self.updateSingal.connect(plot.dataUpdate)
        self.addPlot(plot)

    # 菜单事件：设置配置参数
    @pyqtSlot()
    def action_configuration_event(self):
        setConfigurationDailog_basic().dialogShow()
        self.init_loadConfigIndex()

    # 菜单事件：离线数据显示
    @pyqtSlot()
    def action_offlineDataShow_event(self):
        # if self.pushButton_dataReceive.isChecked():
        #     QMessageBox.warning(self,'警告','不能在测量时进行离线数据显示')
        # else:
        path = QFileDialog.getOpenFileName(self,'选择离线数据','./data','dataFile (*.h5)')[0]
        dataStorage.clearAllData()
        dataStorage.setH5Path(path)
        dataStorage.update()
        self.updateSingal.emit(1)

    # 菜单事件：数据回放
    @pyqtSlot()
    def action_dataPlayBack_event(self):
        if self.pushButton_dataReceive.isChecked():
            QMessageBox.warning(self,'警告','不能在测量时进行数据回放')
        else:
            print('file')
            filePath = QFileDialog.getOpenFileName(self, '选择回放数据' ,'./data',"数据文件 (*.h5)")[0]
            t = threading.Thread(target=self.dataPlayBack_thread, args=(filePath,))
            t.start()

    # 线程函数：数据回放
    def dataPlayBack_thread(self,h5dataPath: str):
        dataStorage.initPlayBackModule()
        print('init')
        h5 = h5Data(h5dataPath,'r')
        print(h5.index.shape)
        for i in range(h5.index.shape[0]):
            tmpData = h5.getData(i)
            k = 0
            u,idx = np.unique(tmpData[_Index[-2]].values,True)
            while k + 300 < idx.shape[0]:
                dataStorage.playBackAddData(tmpData.loc[idx[k]:idx[k+300]].values)
                self.updateSingal.emit(0)
                k += 300
            dataStorage.playBackAddData(tmpData[idx[k]:].values)
            self.updateSingal.emit(0)
            dataStorage.playBackNewSet()
        dataStorage.EndPlayBackModule()

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



if __name__ == '__main__':
    import pyqtgraph.examples
    pyqtgraph.examples.run()