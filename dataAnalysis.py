

import numpy as np
import pandas as pd
import socket
_gain = int.from_bytes(b'\x20\x00',byteorder='big', signed=True) #8192
_trigger = int.from_bytes(b'\x10\x00',byteorder='big', signed=True) #4096
_value = int.from_bytes(b'\x0f\xff',byteorder='big', signed=True) #4095
class charge_message(object):
    gain = None
    trigger =None
    value = None
    def __init__(self,gain : bool,trigger : bool,value : int):
        self.gain = gain
        self.trigger = trigger
        self.value = value

class time_message(object):
    gain = None
    trigger = None
    value = None
    def __init__(self, gain: bool, trigger: bool, value: int):
        self.gain = gain
        self.trigger = trigger
        self.value = value

class SCA(object):
    ChargeChannel = []
    TimeChannel = []
    BC_ID = None
    def __init__(self):
        pass

class SSP2E_package(object):
    SCA_list = []
    BC_ID = []
    ChipID = None
    SCA_num = 0
    def __init__(self,source : bytes):
        #check the header and the tails bytes
        if not source[0:2] == b'\xfa\x5a':
            raise ValueError("Packet header does not match.")
        elif not source[-2:] == b'\xfe\xee':
            raise ValueError("Packet tails do not match.")
        SCA_num = int((len(source)/2-3)/73)
        print("SCA number = {0}".format(SCA_num))
        for i in range(SCA_num):
            self.SCA_list.append(SCA())
            for j in range(36):
                index = i*72+j+1
                temp = int.from_bytes(source[index*2:(index+1)*2],byteorder='big', signed=True)
                #print(temp)
                self.SCA_list[-1].ChargeChannel.append(
                    charge_message(gain=bool(temp&_gain),trigger=bool(temp&_trigger),value=temp&_value)
                )
            for j in range(36):
                index = i*72+j+1+36
                temp = int.from_bytes(source[index*2:(index+1)*2],byteorder='big', signed=True)
                #print(temp)
                self.SCA_list[-1].TimeChannel.append(
                    time_message(gain=bool(temp&_gain),trigger=bool(temp&_trigger),value=temp&_value)
                )
        for i in range(SCA_num):
            index = i+72*SCA_num+1
            temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big', signed=True)
            #print(temp)
            self.BC_ID.append(temp)
        self.ChipID = int.from_bytes(source[(73*SCA_num+1)*2:-2], byteorder='big', signed=True)

#unpackage data from file or socket,and store it.
class SSP2E_Data(object):
    _SCAlist = []
    _dataFrame = pd.DataFrame()
    _badPacket = 0 #record the number of bad packet,Chip ID of which is not matched.
    def __len__(self):
        return len(self._SCAlist)

    def __getitem__(self, item):
        return self._SCAlist[item]

    def __init__(self,**kwargs):
        pass

    def load(self,input):
        if isinstance(input,str):
            self._loadfile(input)
        elif isinstance(input,socket.socket):
            pass

    def _loadfile(self,path : str):
        #load binary data from target path and store it as readable format.
        f = open(path,'rb')
        buff = f.read(1024)
        while buff != 0:
            try:
                header = buff.index(b'\xfa\x5a')
                tails = buff.index(b'\xfe\xee',header)
            except ValueError:
                b = f.read(1024)
                if len(b) == 0:
                    break
                buff = buff + b
                continue
            self._unpackage(buff[header:tails+2])
            buff = buff[tails+3:]

    def _unpackage(self,source):
        # Unpackage a SSP2E packet.
        # Translate it into class SCA and push the SCA to _SCAlist.
        SCA_list = []
        # check the header and the tails bytes
        if not source[0:2] == b'\xfa\x5a':
            raise ValueError("Packet header does not match.")
        elif not source[-2:] == b'\xfe\xee':
            raise ValueError("Packet tails do not match.")
        SCA_num = int((len(source) / 2 - 3) / 73)
        #print("SCA number = {0}".format(SCA_num))
        for i in range(SCA_num):
            SCA_list.append(SCA())
            for j in range(36):
                index = i * 72 + j + 1
                temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big', signed=True)
                SCA_list[-1].ChargeChannel.append(
                    charge_message(gain=bool(temp & _gain), trigger=bool(temp & _trigger), value=temp & _value)
                )
            for j in range(36):
                index = i * 72 + j + 1 + 36
                temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big', signed=True)
                SCA_list[-1].TimeChannel.append(
                    time_message(gain=bool(temp & _gain), trigger=bool(temp & _trigger), value=temp & _value)
                )
        for i in range(SCA_num):
            index = i + 72 * SCA_num + 1
            temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big', signed=True)
            SCA_list[i].BC_ID = temp
        ChipID = int.from_bytes(source[(73 * SCA_num + 1) * 2:-2], byteorder='big', signed=True)
        if ChipID & int.from_bytes(b'\x00\x01',byteorder='big',signed=True):
            while len(SCA_list) != 0:
                self._SCAlist.append(SCA_list.pop())
            return True
        else:
            self._badPacket = self._badPacket + 1
            return False

    def to_dataFrame(self):
        pass



if __name__ == "__main__":
    ssp = SSP2E_Data()
    ssp.load("C:\\Users\\MACHENIKE\\Desktop\\tempData_20200518_212846.dat")
    print("final:",len(ssp))
    # f = open("C:\\Users\\MACHENIKE\\Desktop\\tempData_20200518_212846.dat",'rb')
    # b = f.read(1024)
    # print(len(b))
    # x = b'\xfa'
    # i = b.index(x)
    # print(i,b[i])
    # header = b.index(b'\xfa\x5a')
    # tails = b.index(b'\xfe\xee')
    # packet = b[header:tails+2]
    # print(packet[2:4] == b'\x24\x4f')
    # temp_bytes = packet[2:4]
    # print("&gain:",int.from_bytes(b'\x20\x00',byteorder='big', signed=True))
    # print("&trigger",int.from_bytes(b'\x10\x00',byteorder='big', signed=True))
    # print("&value",int.from_bytes(b'\x0f\xff',byteorder='big', signed=True))
    # ssp = SSP2E_package(packet)
    # print(len(packet))
    # print(ssp.SCA_list[0].ChargeChannel[0].value)
    # print(len(ssp.SCA_list))
    # print('test')
    # x = open("A:\工作\实验室\LUMIS\op.xml",'rb')
    # b = x.read(1024)
    # while len(b) != 0:
    #     print(len(b))
    #     b = b + b'\xff'
    #     print(hex(b[-1]))
    #     header = b.index(b'\xff')
    #     print(header)
    #     b = x.read(1024)
    # print(len(b))

