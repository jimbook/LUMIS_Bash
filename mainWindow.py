import pyqtgraph as pg
import pandas as pd
import numpy as np
import os,sys,socket,time,gc,datetime
import threading
from dataAnalyse import dataAnalyse
from linkGBT import linkGBT
from myWidget import subPlotWin_singal,subPlotWin_coincidence
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from UI.mainWindow import Ui_MainWindow
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

        self.comboBox_singal_tier.addItems(["1","2"])
        self.comboBox_singal_channel.addItems(self.TCPLink.dataStorage.chnList)

        self.comboBox_coin1_tier.addItems(["1", "2"])
        self.comboBox_coin2_tier.addItems(["1", "2"])
        self.comboBox_coin1_channel.addItems(self.TCPLink.dataStorage.chnList)
        self.comboBox_coin2_channel.addItems(self.TCPLink.dataStorage.chnList)


    def setEvent(self):
        #communication event
        self.pushButton_config.clicked.connect(self.sendConfigFile_event)
        self.pushButton_dataReceive.clicked.connect(self.switchReceiveDataThread_event)
        #plot event
        self.pushButton_singal_addPlot.clicked.connect(self.plotSingalEnergySpectum)
        # self.pushButton_coin_addPlot.clicked.connect(self.plotCoincidenceEnergySpectum)
        #auxiliary event
        self.timer.timeout.connect(self.timeOut_event)
        self.TCPLink.errorSingal.connect(self.receiveError_event)
        self.TCPLink.dataStorage.receiveSignal.connect(self.receiveData_event)

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
        self.addMessage("bad package:{0}-----length error:{1};ChipID error:{2};\nevent:{3}".format(
            self.TCPLink.dataStorage._badPackage, self.TCPLink.dataStorage.lenError,
            self.TCPLink.dataStorage.ChipIDError,
            self.TCPLink.dataStorage._temTID + self.TCPLink.dataStorage._tCount * 65535))

    #
    def plotSingalEnergySpectum(self):
        subWin = QMdiSubWindow()
        subWin.setAttribute(Qt.WA_DeleteOnClose)
        singalEnergryPlot = subPlotWin_singal()
        singalEnergryPlot.setData(self.TCPLink.dataStorage.to_dataFrame(),
                                  int(self.comboBox_singal_tier.currentText()),self.comboBox_singal_channel.currentText(),
                                  self.checkBox_singal.isChecked())
        self.TCPLink.dataStorage.receiveSignal.connect(singalEnergryPlot.dataUpdate)
        subWin.setWidget(singalEnergryPlot)
        self.mdiArea.addSubWindow(subWin)
        subWin.show()

    #
    def plotCoincidenceEnergySpectum(self):
        subWin = QMdiSubWindow()
        subWin.setAttribute(Qt.WA_DeleteOnClose)
        coinEnergyPlot = subPlotWin_coincidence()
        coinEnergyPlot.setData(self.TCPLink.dataStorage.to_dataFrame(),int(self.comboBox_coin1_tier.currentText()),
                               self.comboBox_coin1_channel.currentText(),int(self.comboBox_coin2_tier.currentText()),
                               self.comboBox_coin2_channel.currentText(),self.checkBox_coin.isChecked())
        subWin.setWidget(coinEnergyPlot)
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




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = window()
    ex.TCPLink.dataStorage._loadfile(".\\data\\mydata.txt",source=False)
    ex.show()
    sys.exit(app.exec_())