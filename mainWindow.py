import pyqtgraph as pg
import pandas as pd
import numpy as np
import os,sys,socket,time,gc,datetime
import threading
from dataAnalyse import *
from linkGBT import linkGBT,dataStorage
from myWidget import subPlotWin_singal
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow
#
class window(QMainWindow,Ui_MainWindow):
    updata = 0
    recvdata = 0
    _recvLen = 1024*512
    def __init__(self,*args):
        super(window, self).__init__(*args)
        self.setupUi(self)
        self.retranslateUi(self)
        self.setMore()
        self.setEvent()

    def setMore(self):
        self.init_loadConfigIndex()
        self.TCPLink = linkGBT()
        self.log = ""
        self.timer = QTimer()
        self.time = QTime()
        # 单通道能谱
        self.comboBox_singal_tier.addItems(["1","2"])
        self.comboBox_singal_channel.addItems(chnList)


    def setEvent(self):
        #communication event
        self.pushButton_config.clicked.connect(self.sendConfigFile_event)
        self.pushButton_dataReceive.clicked.connect(self.switchReceiveDataThread_event)
        #plot event
        self.pushButton_singal_addPlot.clicked.connect(self.plotSingalEnergySpectum)
        #auxiliary event
        self.timer.timeout.connect(self.timeOut_event) #
        self.TCPLink.errorSingal.connect(self.receiveError_event)
        dataStorage.receiveSignal.connect(self.receiveData_event)

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
    # 事件：开启/结束数据接收线程，同时会显示测量时间
    def switchReceiveDataThread_event(self,switch: bool):
        if switch:
            self.time.setHMS(0,0,0,0)
            try:
                self.TCPLink.startReceive()
                self.timer.start(10)
            except Exception as e:
                self.addMessage("无法启动接收数据")
                self.addMessage(e.__str__())
            self.addMessage("开始接收数据")
            self.pushButton_dataReceive.setText("停止接收数据")
        else:
            self.TCPLink.stopReceive()
            self.timer.stop()
            self.addMessage("结束数据接收")
            self.pushButton_dataReceive.setText("开始接收数据")

    # event: when data receive thread raise Exception,this function will catch it and print it in message queue.
    # 事件：当数据接收线程抛出异常时，将异常信息打印到消息队列中
    def receiveError_event(self,message: str):
        self.addMessage("接收数据时遇到意外：")
        self.addMessage(message)
        self.timer.stop()
        self.pushButton_dataReceive.setChecked(False)
        self.pushButton_dataReceive.setText("开始接收数据")

    # evet: when read 0.5MB data,this function will print a message
    # 事件：每当接收0.5MB数据将会打印一次数据状态
    def receiveData_event(self):
        t = datetime.datetime.now()
        self.addMessage("==={}===\n{}\tevent count{}".format(
            t.strftime("%H:%M:%S"),dataStorage.badPackage(),dataStorage.eventCount()))

    # 事件：添加单通道能谱
    def plotSingalEnergySpectum(self):
        subWin = QMdiSubWindow()
        subWin.setAttribute(Qt.WA_DeleteOnClose)
        singalEnergryPlot = subPlotWin_singal()
        singalEnergryPlot.setData(dataStorage.to_dataFrame(),
                                  int(self.comboBox_singal_tier.currentText()),self.comboBox_singal_channel.currentText(),
                                  self.checkBox_singal.isChecked())
        dataStorage.receiveSignal.connect(singalEnergryPlot.dataUpdate)
        subWin.setWidget(singalEnergryPlot)
        self.mdiArea.addSubWindow(subWin)
        subWin.show()

    #auxiliary: erver interval will call this function to refresh clock widget
    #辅助函数：每过一个时间间隔将会调用一次，来刷新时间显示控件显示的时间
    def timeOut_event(self):
        self.time = self.time.addMSecs(self.timer.interval())
        self.lcdNumber_s_ms.display(self.time.toString("ss.zzz")[:-1])
        self.lcdNumber_h_m.display(self.time.toString("HH:mm"))

    # auxiliary: add message to text Browser
    # 辅助函数：向消息队列中添加消息
    def addMessage(self,inputMessage: str):
        self.log += inputMessage+'\n'
        self.textBrowser_messageQueue.setText(self.log)
        self.textBrowser_messageQueue.moveCursor(QTextCursor.End) # 设置自动滚动到底部




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = window()
    # dataStorage._loadfile(".\\data\\mydata.txt",source=False)
    ex.show()
    sys.exit(app.exec_())