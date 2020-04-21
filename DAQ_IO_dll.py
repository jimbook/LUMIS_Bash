import usb.core
import usb.util
import time, threading

class _USB_Manager(object):
    def __init__(self):
        super(_USB_Manager,self).__init__()
        self.dev = None #匹配的USB设备
        self._findUSBStopflag = False #搜索USB接口线程标志

    #搜索USB接口线程函数逻辑
    def _findUSBThreading(self, idVendor=0x258A, idProduct=0x1006):
        print("USB Searcher:Looking for a matching USB device.\n")
        while (not self.dev) and self._findUSBStopflag:
            self.dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
            time.sleep(0.5)
        if self.dev:
            self.dev.set_configuration()
            self._findUSBStopflag = False
            print("USB Searcher:USB Successfully found the USB device.\n")
        elif not self._findUSBStopflag:
            print("USB Searcher:Search for USB devices has been stopped.\n")

    #开启搜索USB接口线程
    def StartSearchUSB(self):
        self._findUSBStopflag = True
        t = threading.Thread(target=self._findUSBThreading,name="looking for a matching USB device")
        t.start()

    #停止USB搜索
    def stopSearchUSB(self):
        if self._findUSBStopflag:
            self._findUSBStopflag = False
        elif self.dev:
            print("Manger:USB device is ready,no need to search.\n")
        else:
            print("Manger:Currently not searching for USB devices.\n")

    #打印USB接口数据
    def printUSBdescription(self,**kwargs):
        if self.dev:
            print(self.dev)
        else:
            print("Manger:USB device is not ready.\n")

import sys
import clr
sys.path.append(r'A:\工作\实验室\LUMIS\DAQ_IO\DAQ_IO\bin\Debug')
clr.AddReference('DAQ_IO')
from DAQ_IO_DLL import DAQ_IO
from System import byte,Array
class USB_Manager(object):
    def __init__(self):
        super(USB_Manager,self).__init__()
        self.DAQ = DAQ_IO()# c#库，对接DAQ
        self._findUSBStopflag = False  # 搜索USB接口线程标志
        self._USBstatus = False
        self.StartSearchUSB()

    #搜索USB接口线程函数逻辑
    def _findUSBThreading(self, idVendor=0x258A, idProduct=0x1006):
        print("USB Searcher:Looking for a matching USB device.\n")
        while (not self._USBstatus) and self._findUSBStopflag:
            self._USBstatus = self.DAQ.check_USB()
            time.sleep(0.5)
        if self._USBstatus:
            self._findUSBStopflag = False
            print("USB Searcher:USB Successfully found the USB device.\n")
        elif not self._findUSBStopflag:
            print("USB Searcher:Search for USB devices has been stopped.\n")

    #开启搜索USB接口线程
    def StartSearchUSB(self):
        self._findUSBStopflag = True
        t = threading.Thread(target=self._findUSBThreading,name="looking for a matching USB device")
        t.start()

    #停止USB搜索
    def stopSearchUSB(self):
        if self._findUSBStopflag:
            self._findUSBStopflag = False
        elif self.dev:
            print("Manger:USB device is ready,no need to search.\n")
        else:
            print("Manger:Currently not searching for USB devices.\n")

    def CommandSend(self,OutData : int):
        if OutData <= 0xFFFF and OutData >= 0x000:
            return self.DAQ.CommandSend(OutData,2)
        else:
            print("Manger:ValueError!")
            return False

    def DataRecieve(self):
        InData = Array[byte](0x00,0x00)
        return self.DAQ.DataRecieve(InData,2),InData




if __name__ == "__main__":
    myUSBMG = USB_Manager()
    myUSBMG.StartSearchUSB()
    time.sleep(2)
    myUSBMG.printUSBdescription()
    myUSBMG.dev.set_configuration()
    print(myUSBMG.dev.configurations())
    cfg = myUSBMG.dev[0]
    print(cfg.interfaces())




