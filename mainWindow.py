import pyqtgraph as pg
import pandas as pd
import numpy as np
import os,sys,socket,time,gc,datetime
import threading
import copy
from globelParameter import dataChannel
from dataAnalyse import chnList
from linkGBT import linkGBT
from myWidget import subPlotWin_singal
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow
#
class window(QMainWindow,Ui_MainWindow):
    updateSingal = pyqtSignal(list,list)
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
        self.timer = QTimer()
        self.time = QTime()
        #从数据服务端获取共享对象
        self.dataChn = dataChannel(manager)
        # 单通道能谱
        self.comboBox_singal_tier.addItems(["1","2"])
        self.comboBox_singal_channel.addItems(chnList)
        # 开启从数据服务进程接收数据的服务
        t = threading.Thread(target=self.getMessge)
        t.start()
        # 数据项
        self.dataInMemory = [] # 内存中的数据
        self.dataInDisk = [] # 硬盘中数据的路径

    def setEvent(self):
        #communication event
        self.pushButton_config.clicked.connect(self.sendConfigFile_event)
        self.pushButton_dataReceive.clicked.connect(self.switchReceiveDataThread_event)
        #plot event
        self.pushButton_singal_addPlot.clicked.connect(self.plotSingalEnergySpectum)
        #auxiliary event
        self.messageSingal.connect(self.addMessage) # 将消息队列中的消息打印到消息栏
        # synchronizeData
        self.timer.timeout.connect(self.synchronizeData)


    # init: load config file index
    # 初始化：读入配置文件列表
    def init_loadConfigIndex(self):
        for _r,_d,files in os.walk(".\\configurationFile"):
            configList = [os.path.splitext(x)[0] for x in files if os.path.splitext(x)[-1] == ".dat"]
        self.comboBox_configFile.addItems(configList)

    # event Function:send configuration file to device
    # 事件：发送配置文件
    def sendConfigFile_event(self):
        filePath = os.path.join(".\\configurationFile", self.comboBox_configFile.currentText() + ".dat")
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
    def sendShortCommand_evet(self):
        text = self.lineEdit_sendCommand.text()
        if len(text) == 4:
            cmd = bytes.fromhex(text)
            try:
                linkGBT.sendCommand(cmd)
                self.addMessage("成功发送命令：{}".format(cmd))
            except Exception as e:
                self.addMessage("发送命令失败\n{}".format(e.__str__()))
        else:
            self.addMessage("只能发送2bytes的命令！")

    # event: start or stop data receive thread.Meanwhile,it will show the measuring time.
    # 事件：通过更改标志来开启/结束数据接收线程
    def switchReceiveDataThread_event(self,switch: bool):
        try:
            if switch:
                self.dataChn.threadTag.set()
                self.pushButton_dataReceive.setText("停止接收数据")
                self.pushButton_config.setDisabled(True)    # 采集时禁止其他通讯方式使用TCP连接，
                self.pushButton_sendCommand.setDisabled(True)
                self.timer.start(5000)
            else:
                self.dataChn.threadTag.clear()
                self.timer.stop()
                self.pushButton_dataReceive.setText("开始接收数据")
                self.pushButton_dataReceive.setDisabled(True)
                self.addMessage("等待数据服务进程停止接收数据")
                self.timer.stop()
        except:
            import traceback
            traceback.print_exc()

    #辅助函数：获取从数据服务中获取的消息，同时根据数据服务进程的状态使按钮可用
    def getMessge(self):
        while True:
            # 从消息队列中获取消息
            msg = self.dataChn.mq.get()
            self.messageSingal.emit(msg)
            # 如果此时数据接收已经结束，让配置/开始接收数据按钮可用
            if self.dataChn.dataTag.is_set():
                self.pushButton_sendCommand.setEnabled(True)
                self.pushButton_config.setEnabled(True)
                self.pushButton_dataReceive.setEnabled(True)
            # else:       # 如果此时在接收数据，发送更新数据的指令
            #     self.dataInMemory = copy.copy(self.dataChn.dataStorage.get_memoryData())
            #     self.dataInDisk = copy.copy(self.dataChn.dataStorage.get_diskData())
            #     self.updateSingal.emit(self.dataInMemory,self.dataInDisk)
            #     gc.collect()

    def synchronizeData(self):
        self.dataInMemory = copy.copy(self.dataChn.dataStorage.get_memoryData())
        self.dataInDisk = copy.copy(self.dataChn.dataStorage.get_diskData())
        self.updateSingal.emit(self.dataInMemory,self.dataInDisk)

    # 事件：添加单通道能谱
    def plotSingalEnergySpectum(self):
        subWin = QMdiSubWindow()
        subWin.setAttribute(Qt.WA_DeleteOnClose)
        singalEnergryPlot = subPlotWin_singal()
        singalEnergryPlot.setData(self.dataInMemory,self.dataInDisk,
                                  int(self.comboBox_singal_tier.currentText()),self.comboBox_singal_channel.currentText(),
                                  self.checkBox_singal.isChecked())
        self.updateSingal.connect(singalEnergryPlot.dataUpdate)
        singalEnergryPlot.changeBaseLine(self.spinBox_baseLine.value())
        subWin.setWidget(singalEnergryPlot)
        self.mdiArea.addSubWindow(subWin)
        subWin.show()

    #auxiliary: erver interval will call this function to refresh clock widget
    #辅助函数：每过一个时间间隔将会调用一次，来刷新时间显示控件显示的时间(已弃用)
    def timeOut_event(self):
        self.time = self.time.addMSecs(self.timer.interval())
        self.lcdNumber_s_ms.display(self.time.toString("ss.zzz")[:-1])
        self.lcdNumber_h_m.display(self.time.toString("HH:mm"))

    # auxiliary: add message to text Browser
    # 辅助函数：向消息队列中添加消息
    def addMessage(self,inputMessage: str):
        try:
            self.log += inputMessage+'\n'
            self.textBrowser_messageQueue.setPlainText(self.log)
            self.textBrowser_messageQueue.moveCursor(QTextCursor.End) # 设置自动滚动到底部
        except:
            import traceback
            traceback.print_exc()

    # 重载函数：关闭界面-会弹出提示框，同时结束数据接收服务
    def close(self) -> bool:
        if not self.dataChn.dataTag.is_set():
            if QMessageBox.information(self,"关闭界面","数据接收仍在进行，是否确认关闭？确认后将等待数据接收服务结束后关闭。",
                                       QMessageBox.Yes|QMessageBox.No):
                self.dataChn.processTag.clear()
                self.dataChn.threadTag.clear()
                self.dataChn.dataTag.wait()
                super(window, self).close()
                return True
            else:
                return False
        else:
            if QMessageBox.information(self,"关闭界面","是否确认关闭？确认后将等待数据接收服务结束后关闭。",
                                       QMessageBox.Yes|QMessageBox.No):
                self.dataChn.processTag.clear()
                self.dataChn.threadTag.set()
                super(window, self).close()
                return True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_())