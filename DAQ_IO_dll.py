import time, threading
import math,os
import sys
import clr
sys.path.append(r'.\dependent\DAQ_IO\DAQ_IO\bin\Debug')
clr.AddReference('DAQ_IO')
from DAQ_IO_DLL import DAQ_IO
from System import *
class USB_Manager(object):
    def __init__(self):
        super(USB_Manager,self).__init__()
        self.DAQ = DAQ_IO()# c#库，对接DAQ
        self.findUSBStopflag = False  # 搜索USB接口线程标志
        self.dataAcceptflag = False # 数据接收线程
        self.USBstatus = False # USB标志
        self.HVstatus = False # HV标志
        self.DataAcceptStatus = False #数据接收读取进程
        self.currentHV = 40 #记录当前电压，高压电源一打开就是50伏特，最低只能调节到40伏特
        self.slowControlLengthDict = {
            "TRIG_DAC":10,
            "DISCRIMINATOR_MASK1":18,
            "DISCRIMINATOR_MASK2":18,
            "PROBE_OTA":1,
            "EN_OR36":1,
            "AUTO_GAIN":1,
            "GAIN_SELECT":1,
            "ADC_EXT_INPUT":1,
            "SWITCH_TDC_ON":1
        }
        self.slowControlContentDict = {
            "TRIG_DAC":0x0fa,
            "DISCRIMINATOR_MASK1":0,
            "DISCRIMINATOR_MASK2":0,
            "PROBE_OTA":0,
            "EN_OR36":0,
            "AUTO_GAIN":0,
            "GAIN_SELECT":0,
            "ADC_EXT_INPUT":0,
            "SWITCH_TDC_ON":1
        }


    #搜索USB设备
    def searchUSB(self,timeout : int = -1):
        i = 0
        while not self.USBstatus:
            self.USBstatus = self.DAQ.check_USB()
            if timeout == 0:
                return False
            time.sleep(0.2)
            if i<5:
                i = i+1
            else:
                i = 0
                timeout -= 1
        return True


    #搜索USB接口线程函数逻辑
    def _findUSBThreading(self, idVendor=0x258A, idProduct=0x1006):
        while (not self.USBstatus) and self.findUSBStopflag:
            self.USBstatus = self.DAQ.check_USB()
            time.sleep(0.5)
        if self.USBstatus:
            self.findUSBStopflag = False
            print("USB Searcher:USB Successfully found the USB device.\n")
        elif not self.findUSBStopflag:
            print("USB Searcher:Search for USB devices has been stopped.\n")

    #开启搜索USB接口线程
    def StartSearchUSB(self):
        self._findUSBStopflag = True
        t = threading.Thread(target=self._findUSBThreading,name="looking for a matching USB device")
        t.start()

    #停止USB搜索
    def stopSearchUSB(self):
        if self.findUSBStopflag:
            self.findUSBStopflag = False
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
        return self.DAQ.DataRecieve_toPython(2)
##########################################################
    #更改slowControl配置
    def slowControl_set(self,index : str,value : int):
        if index in self.slowControlLengthDict.keys():
            if value >=0 and value < 2**self.slowControlLengthDict.get(index):
                self.DAQ.slowConfig.set_property(self.DAQ.slowConfig.settings[index], value)
                self.slowControlContentDict[index] = value
                return True
        return False

    #配置slow_control
    def slowControl_config(self):
        if self.USBstatus:
            self.DAQ.sc_config_onc()
        else:
            raise ConnectException

    #配置probe_control
    def probe_config(self):
        if self.USBstatus:
            self.DAQ.probeConfig.init()
            self.DAQ.probe_config_once()
        else:
            raise ConnectException

###########################################################
    #开启/关闭高压
    def hv_switch(self,turnOn : bool):
        '''
        :param turnOn: True-turn on hv model ；False-turn off hv model
        :return:void
        开启高压时，电压为50V，关闭高压模块时，电压降到40V
        调用库时，先检索程序内高压标志，如果已经是目标，则不发送命令
        '''
        if self.USBstatus:
            if self.HVstatus != turnOn:
                self.DAQ.hv_switch(turnOn)
                self.HVstatus  =  turnOn
                if turnOn:
                    self.currentHV = 50
                else:
                    self.currentHV = 40
        else:
            raise ConnectException

    #设置高压电压
    def hv_set(self,voltage : float):
        '''
        :param voltage: target voltag
        :return:void
        首先检查输入目标电压是否合理，小于40V则抛出异常
        检查USB设备连接标志，未连接则抛出异常
        检查高压模块状态，未开启则开启高压模块
        '''
        if voltage < 40:
            raise VoltagValueError
        if self.USBstatus:
            if not self.HVstatus:
                self.hv_switch(True)
            self.DAQ.hv_set(voltage)
            self.currentHV = voltage
        else:
            raise ConnectException
##########################################################
    #平滑调节高压
    def hv_smoothTurnOn(self,target_voltag: float  = 50 ):
        if target_voltag < 40 or target_voltag > 200:
            raise ValueError("target voltag must between 40 and 200.")
        if not self.HVstatus:
            self.hv_switch(True)
        tmp_hv = self.currentHV
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
            self.currentHV = tmp_hv
            time.sleep(0.5)

    #半自动电子学刻度（将阻塞1min）
    def elecCalib2E(self,path = ".\\data\\temporary"):
        filePath = os.path.join(path,self.DAQ.elecCalib2E(path))
        return filePath

##########################################################
    #接收数据线程
    def DataAcceptThread(self,path = ".\\data\\temporary"):
        if not self.DataAcceptStatus:
            filePath = os.path.join(path,self.DAQ.start_acq(path))
            self.DataAcceptStatus = True
            return filePath
        else:
            raise RepeatAcceptException
    #停止数据接收
    def StopDataAccept(self):
        if self.DataAcceptStatus:
            self.DAQ.stop_acq()
            self.DataAcceptStatus = False
##########################################################
    #辅助函数



#---------------------------------------------------------------------
#错误信息：设备未连接
class ConnectException(Exception):
    def __init__(self):
        super(self).__init__()
    def __str__(self):
        return "The device is not connected properly."
#错误信息：电压值设置不合理
class VoltagValueError(ValueError):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "Voltag should be greater than 40V"
#错误信息：重复开启数据读取线程
class RepeatAcceptException(Exception):
    def __init__(self):
        super().__init__()
    def __str__(self):
        return "Don't receive data repeatedly.Please stop the DataAcceptThread first."

if __name__ == "__main__":
    myUSBMG = USB_Manager()
    myUSBMG.StartSearchUSB()
    time.sleep(2)
    input(">>>")





