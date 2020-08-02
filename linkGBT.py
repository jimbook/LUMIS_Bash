import numpy as np
import pandas as pd
import socket
import os
from threading import Thread
from datetime import datetime
from globelParameter import dataLock
from dataAnalyse import dataAnalyse
from PyQt5.QtCore import QObject,pyqtSignal

# dataAnalyse-数据对象
dataStorage = dataAnalyse()

# 集合连接通讯操作的函数
class linkGBT(QObject):
    _devIP = '192.168.10.16'
    _TCPport = 24
    _UDPport = 4660
    errorSingal = pyqtSignal(str)
    def __init__(self,*args):
        super(linkGBT, self).__init__(*args)
        global dataStorage
        self.TCPLink = socket.socket()
        self._threadTag = False

    # start receive data threading
    # 开启数据接收线程
    def startReceive(self):
        self.recvThread = Thread(target=self._receiveThread)
        self.recvThread.start()
        print("start receive data.")

    # receive data thread
    def _receiveThread(self):
        try:
            self.TCPLink.connect((self._devIP,self._TCPport))
            self.TCPLink.send(b'\xff\x00')
            dateToday = datetime.now().strftime("%Y_%m_%d")
            timeNow = datetime.now().strftime("%H%M%S")
            if not os.path.exists(os.path.join(".\\data",dateToday)):
                os.makedirs(os.path.join(".\\data",dateToday))
            filePath = os.path.join(".\\data",dateToday,timeNow+"_tempData.txt")
            dataStorage.__init__()
            dataStorage.setReadSize(1024*100) # 设置每次接收100KB的数据
            dataStorage.load(self.TCPLink,filePath=filePath) # 这里会阻塞，直到调用结束读取socket的函数
            print("recevie all data,now end recevie.")
            self.TCPLink.close()
        except Exception as e:
            self.errorSingal.emit(e.__str__())


    # stop data receive threading
    # 停止接收数据
    def stopReceive(self):
        self.TCPLink.send(b'\xff\x01')
        dataStorage.stopSocketRead()


    # send a short binary command
    # 发送一个较短的二进制命令，一般为两个byte
    @staticmethod
    def sendCommand(command: bytes):
        try:
            link = socket.socket()
            link.connect((linkGBT._devIP,linkGBT._TCPport))
            link.send(bytes)
            link.close()
            return True,None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False,e.__str__()

    # send a configuration file as binary data
    # 将文件转换成二进制数据发送
    @staticmethod
    def sendConfigFile(input: str):
        with open(input,mode="rb") as file:
            data = file.read()
        try:
            link = socket.socket()
            link.connect((linkGBT._devIP,linkGBT._TCPport))
            link.send(data)
            link.close()
            return True,None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False,e.__str__()

if __name__ == "__main__":
    import pyqtgraph.examples
    pyqtgraph.examples.run()