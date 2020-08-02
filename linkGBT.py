import numpy as np
import pandas as pd
import socket
import os
from datetime import datetime
from threading import Thread
from dataAnalyse import dataAnalyse
from PyQt5.QtCore import QObject,pyqtSignal
class linkGBT(QObject):
    _devIP = '192.168.10.16'
    _TCPport = 24
    _UDPport = 4660
    errorSingal = pyqtSignal(str)
    def __init__(self,*args):
        super(linkGBT, self).__init__(*args)
        self.TCPLink = socket.socket()
        self.threadTag = False
        self.dataStorage = dataAnalyse()
        self.dataStorage.receiveSignal.connect(self.showDital)

    # start receive data threading
    # 开启数据接收线程
    def startReceive(self):
        self.recvThread = Thread(target=self._receiveThread)
        self.recvThread.start()
        print("start receive data.")

    def _receiveThread(self):
        try:
            self.TCPLink.connect((self._devIP,self._TCPport))
            self.TCPLink.send(b'\xff\x00')
            dateToday = datetime.now().strftime("%Y_%m_%d")
            timeNow = datetime.now().strftime("%H%M%S")
            if not os.path.exists(os.path.join(".\\data",dateToday)):
                os.makedirs(os.path.join(".\\data",dateToday))
            filePath = os.path.join(".\\data",dateToday,timeNow+"_tempData.txt")
            self.dataStorage.setReadSize(1024*100) # 设置每次接收100KB的数据
            self.dataStorage.load(self.TCPLink,filePath=filePath)
            print("recevie all data,now end recevie.")
            self.TCPLink.close()
        except Exception as e:
            self.errorSingal.emit(e.__str__())


    # stop data receive threading
    # 停止接收数据
    def stopReceive(self):
        self.TCPLink.send(b'\xff\x01')
        self.dataStorage._threadTag = False
        self.recvThread.join(timeout=30)
    # ever count will show it
    def showDital(self,tag: int):
        print("="*5,datetime.now(),"="*5)
        if tag == 1:
            print("dataSize:{0},bad package:{1}".format(self.dataStorage.to_dataFrame().shape[0],self.dataStorage.badPackage()))
        elif tag == 0:
            print("end")

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