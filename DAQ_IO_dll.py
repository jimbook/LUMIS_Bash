import usb.core
import usb.util
import time, threading
import math
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
        self._USBstatus = False #  USB标志
        self._HVstatus = False # HV标志
        self._currentHV = 50 #记录当前电压
        self.StartSearchUSB()
        self.slowControlDict = {"TRIG_DAC":10,
                                "DISCRIMINATOR_MASK1":18,
                                "DISCRIMINATOR_MASK2":18,
                                "PROBE_OTA":1,
                                "EN_OR36":1,
                                "AUTO_GAIN":1,
                                "GAIN_SELECT":1,
                                "ADC_EXT_INPUT":1,
                                "SWITCH_TDC_ON":1
                                }



    #搜索USB接口线程函数逻辑
    def _findUSBThreading(self, idVendor=0x258A, idProduct=0x1006):
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
########################################会默认USB配置好
    #发送二进制命令
    def CommandSend(self,OutData : int):
        if OutData <= 0xFFFF and OutData >= 0x000:
            return self.DAQ.CommandSend(OutData,2)
        else:
            print("Manger:ValueError!")
            return False

    #接收二进制命令
    def DataRecieve(self):
        InData = Array[byte](0x00,0x00)
        return self.DAQ.DataRecieve(InData,2),InData
##########################################################
    #更改slowControl配置
    def slowControl_set(self,index : str,value : int):
        if value in self.slowControlDict.keys():
            if value >=0 and value < 2**self.slowControlDict.get(index):
                self.DAQ.slowConfig.set_property(self.DAQ.slowConfig.settings["TRIG_DAC"], value)

    #配置slow_control
    def slowControl_config(self):
        if self._USBstatus:
            self.DAQ.sc_config_onc()

    #配置probe_control
    def probe_config(self):
        if self._USBstatus:
            self.DAQ.probe_config_once()

###########################################################
    #开启/关闭高压
    def hv_switch(self,turnOn : bool):
        if self._USBstatus:
            self.DAQ.hv_switch(turnOn)
            self._HVstatus  =  turnOn

    #设置高压电压
    def hv_set(self,voltage : float):
        if self._USBstatus:
            self.DAQ.hv_set(voltage)
            self._currentHV = voltage
##########################################################
    def hv_smoothTurnOn(self,target_voltag: float  = 50 ):
        tmp_hv = self._currentHV
        if not self._currentHV:
            self.hv_switch(True)
        while (math.fabs(tmp_hv-target_voltag)>0.2):
            if tmp_hv < 68:
                if target_voltag > tmp_hv:
                    tmp_hv += 1
                else:
                    tmp_hv -= 1
            else:
                if target_voltag > tmp_hv:
                    tmp_hv += 0.1
                else:
                    tmp_hv -= 0.1
            self.hv_set(tmp_hv)
            self._currentHV = tmp_hv
            time.sleep(0.5)








if __name__ == "__main__":
    myUSBMG = USB_Manager()
    myUSBMG.StartSearchUSB()
    time.sleep(2)
    myUSBMG.printUSBdescription()
    myUSBMG.dev.set_configuration()
    print(myUSBMG.dev.configurations())
    cfg = myUSBMG.dev[0]
    print(cfg.interfaces())




