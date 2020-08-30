'''
包含与设备通讯的类
'''
import numpy as np
import socket
import os
import time
from multiprocessing import SimpleQueue
from datetime import datetime
import math
from PyQt5.QtCore import pyqtSignal
from dataLayer.baseCore import dataStorage,h5Data
from threading import Event
import gc
import threading
# ----------仪器通讯地址
_devIP = '192.168.10.16'
_TCPport = 24
_UDPport = 4660
# ----------辅助解包------------
_gain = int.from_bytes(b'\x20\x00',byteorder='big',signed=True) # 8192
_hit = int.from_bytes(b'\x10\x00',byteorder='big',signed=True) # 4096
_value = int.from_bytes(b'\x0f\xff',byteorder='big',signed=True) # 4095

# 集合连接通讯操作的函数
class linkGBT(object):
    errorSingal = pyqtSignal(str)

    # send a short binary command
    # 发送一个较短的二进制命令，一般为两个byte
    @staticmethod
    def sendCommand(command: bytes):
        global _devIP,_TCPport
        try:
            link = socket.socket()
            link.connect((_devIP,_TCPport))
            link.send(command)
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
        global _devIP,_TCPport
        with open(input,mode="rb") as file:
            data = file.read()
        try:
            link = socket.socket()
            link.connect((_devIP,_TCPport))
            link.send(data)
            link.close()
            return True,None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False,e.__str__()

# 数据接收进程
def dataReceiveServer(d: dataStorage,tag: Event,dataTag: Event,processTag: Event,messageQueue: SimpleQueue):
    data_unpack = unpack(message_queue=messageQueue,tag=tag,data_storage=d)
    while processTag.is_set():
        tag.wait()  # 等待开启数据接收线程
        print("开启数据接收")
        if not processTag.is_set():
            break
        dataTag.clear() # 表示数据接收线程正在运行
        messageQueue.put("data receive start")
        data_unpack.load() # 开始接收和解析数据，会阻塞直到数据接收结束
        dataTag.set() # 表示数据接收已经停止
        messageQueue.put("data receive stop")
        print("数据接收停止")
        tag.clear()
    messageQueue.put("data server end")
    print("数据服务进程已退出")

# 为数据接收服务进程所编写的解析二进制数据类
class unpack(object):
    _devIP = '192.168.10.16'
    _TCPport = 24

    def __init__(self, *args, message_queue: SimpleQueue, tag: Event, data_storage: dataStorage):
        super(unpack, self).__init__(*args)
        # 辅助参数
        self._readSize = 1024 * 1024  # 每次读取数据的大小
        self._threadTag = tag  # 标志线程是否应该结束
        self._messageQueue = message_queue  # 用于向GUI发送消息
        #self._fileH5 = None  # 数据存储路径
        # 数据相关
        self._dataStorage = data_storage  # 用于将数据放入数据服务
        self._eventBuff = []

    # 初始化各个参数
    def Init(self):
        # 初始化socket套接字
        self._sock = socket.socket()
        self._sock.settimeout(60)
        # 坏包（扔掉的包）计数
        self._empty = 0  # 空包数
        self._interrupt = 0 # 遭受中断的包数
        self._unknow = 0  # 未知情况的包数
        # 数据计数
        self._count = 0  # 接收的包的总数目/当前数据的行数
        self._temTID = 0  # 当前包的triggerID
        # 清空共享内存中的数据和事件缓存区数据
        self._dataStorage.clear()
        self._eventBuff.clear()

    # 清空当前坏包统计
    def clearBadPackage(self):
        self._empty = 0  # 空包数
        self._interrupt = 0  # 遭受中断的包数
        self._unknow = 0  # 未知情况的包数

    # 设置每次读取数据的大小
    def setReadSize(self, size: int):
        self._readSize = size
    # ==================返回内部信息的函数=======================
    # 返回以字符串形式的坏包信息，或返回int形式的总坏包数
    def badPackage(self, ToString: bool = True):
        if ToString:
            return "bad package:{}; empty:{},interrupt:{},unknow:{}".format(
                self._empty+self._interrupt+self._unknow,self._empty,self._interrupt,self._unknow)
        else:
            return self._empty+self._interrupt+self._unknow

    # 返回当前采集到的事件数
    def eventCount(self):
        return self._count

    # --------------------------------------------------------

    # 接收数据,如果发生错误，会将线程标志置False
    def load(self) -> None:
        # 初始化各个参数
        self.Init()
        # 连接TCP连接，并发送开始数据传输命令，如果报错(无法连接)则直接返回False
        try:
            self._sock.connect((self._devIP, self._TCPport))
            self._sock.send(b'\xff\x00')  # 发送命令，开始接收数据
        except Exception as e:
            self._threadTag.clear()
            self._messageQueue.put("an exception occurred while receiving data:\n" + e.__str__())
            return None
        # 成功连接后，创建数据存储文件夹和h5文件，向h5文件中添加开始接收数据的时间戳
        self._messageQueue.put("TCP connect successfuly")
        t = threading.Thread(target=self.sendMessage)
        t.start()
        print("成功连接到设备")
        today = datetime.now().strftime("%Y_%m_%d")
        nowTime = datetime.now().strftime("%H%M%S")
        if not os.path.exists(os.path.join("./data", today)):
            os.makedirs(os.path.join("./data", today))
        _filePath = os.path.join("./data", today, nowTime + "_data.h5")
        self._fileH5 = h5Data(_filePath, 'w')
        self._fileH5.startTime()
        self._dataStorage.setH5Path(_filePath)
        # 开始接收数据，结束时向h5文件添加结束时间戳
        try:
            self._loadsocket() # 从socket接收数据，会阻塞直到数据接收结束
            self._sock.send(b'\xff\x01')  # 发送停止接收数据的指令
            self._messageQueue.put("stop command has sent,waiting for the cached data to be processed.")
        except socket.timeout:
            self._sock.send(b'\xff\x01')  # 发送停止接收数据的指令
            self._messageQueue.put("stop command has sent,waiting for the cached data to be processed.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._threadTag.clear()
            self._messageQueue.put("an exception occurred while receiving data:\n" + e.__str__())
        finally:
            self._sock.close()
            self._fileH5.stopTime()
            t = self._fileH5.totalTime()
            self._messageQueue.put("the total time consuming:{}".format(t))

    # auxiliary : search every SS2E packet and invoking the decode function from socket
    # 辅助函数：从socket连接中找到每一个符合规则的SSP2E数据包，然后调用_unpackage函数将这个包解析，将数据载入内存/写入硬盘
    def _loadsocket(self):
        print("开始读取数据")
        # 开始读取数据
        buff = self._sock.recv(self._readSize)
        tails = 0
        print(self._threadTag.is_set())
        while buff != 0 and self._threadTag.is_set():
            try:
                header = buff.index(b'\xfa\x5a', tails)
                tails = buff.index(b'\xfe\xee\xfe\xee', header)
            except ValueError:  # 如果找不到一个完整的包，则继续读入一部分数据
                b = self._sock.recv(self._readSize)
                # 如果没有数据可读，则退出循环
                if len(b) == 0:
                    break
                # 将新读入的数据添加到缓存区，并把之前已读的数据清除，同时将包尾的索引清零
                buff = buff[tails + 4:] + b
                tails = 0
                gc.collect()
                continue
            # 如果数据刚好包尾之后，状态数据前结束，则再读取较少数据补全状态数据
            if len(buff) < tails+12:
                print(len(buff),tails+12)
                b = self._sock.recv(self._readSize)
                buff += b
            dataBuff = buff[header:tails+4]
            statusBuff = buff[tails+4:tails+12]
            # check the length of package is correct
            # 检查包长是否合适
            check = self._checkPackageLength(source=dataBuff)
            # 有中断，则丢弃eventBuff中的数据，重新寻找包头
            if check == 0:
                newHead = dataBuff.index(b'\xfa\x5a', 2)
                dataBuff = dataBuff[newHead:]
                self._eventBuff.clear()
                self._interrupt += 0
                check = self._checkPackageLength(source=dataBuff)
            # 包长合适
            if check == 1:
                chargeData = self._unpackage(dataBuff)
                statusData = self._unpackStatus(statusBuff)
                chargeData[-1] = statusData[-1]
                self._dataStorage.setStatus(statusData)
                # 如果在同一个事件中，则将数据存储在事件缓存区中，等待一个事件数据完整后再向DISK和SHARE MEMORY中输出
                if self._temTID == chargeData[-2]:
                    self._eventBuff.append(chargeData)
                # 接收到的是新的事件
                # 若triggerID重置过，则将eventBuff中的数据输出到DISK和SHARE MEMORY中，
                # H5建立新的DataSets,清空共享内存中的数据,清空eventBuff后将新数据放到缓存区
                elif self._temTID > chargeData[-2]:
                    _d = np.array(self._eventBuff)
                    if _d.shape[0] > 0:
                        self._fileH5.addToDataSet(_d, NewSets=True)
                        self._dataStorage.addMeoryData(_d.tolist())
                        self._dataStorage.resetMeoryData()
                        self._eventBuff.clear()
                    self._eventBuff.append(chargeData)
                    self._temTID = chargeData[-2]
                    self._count += 1
                # 如果接收到的是新的事件，则将事件缓存区的数据输出到DISK和SHARE MEMORY中，然后清空缓存区，再将新数据加入缓存区
                else:
                    _d = np.array(self._eventBuff)
                    if _d.shape[0] > 0:
                        self._fileH5.addToDataSet(_d)
                        self._dataStorage.addMeoryData(_d.tolist())
                        self._eventBuff.clear()
                    self._eventBuff.append(chargeData)
                    self._temTID = chargeData[-2]
                    self._count += 1
            # 接收到的是空包，只输出状态信息
            elif check == 2:
                statusData = self._unpackStatus(statusBuff)
                self._dataStorage.setStatus(statusData)
                self._empty += 1
            # 遇到未知情况
            else:
                self._unknow += 1

    # auxiliary : decode a SSP2E packet into pd.DataFrame
    # 辅助函数：解析一个SSP2E数据包
    def _unpackage(self, source: bytes):
        '''
        THE FOEMAT OF DATA PACKAGE:
        ---------DATA PART-------------
        NAME    ROW     SIZE    LOCAL
        HAED    1ROW    2Bytes  0-1
        HGain   36ROW   72Bytes 2-73
        LGain   36ROW   72Bytes 74-145
        BCID    1ROW    2Bytes  146-147
        ChipID  1ROW    2Bytes  148-149
        Trigger 1ROW    2Bytes  150-151
        TAIL    1ROW    4Bytes  152-155
        TOTAL SIZE: 156
        ---------STATUS PART-----------
        TrigDAC 1ROW    2Bytes  156-157
        INDAC   1ROW    2Bytes  158-159
        TrigMode1ROW    2Bytes  160-161
        BoardID 1ROW    2Bytes  162-163
        TOTAL SIZE: 8
        *********UNPACKED DATA*********
        NAME            LENGTH
        CHARGE          36
        TrigID          1
        TOTAL LENGTH:   37
        ===============================
        :param source:  156Bytes-Just data part
        :return: np.array-shape=(38,1),but there are only 37 valid data points.
                None-if chipID is unequal \x00\x01
        '''
        # check the header and the tail bytes
        if not source[0:2] == b'\xfa\x5a':
            raise ValueError("Packet header does not match.")
        elif not source[152:] == b'\xfe\xee\xfe\xee':
            raise ValueError("Packet tails do not match.")
        charge = np.empty(38,dtype='uint16')  # 存储解析后数据的位置
        # time/LowGain information
        for j in range(36):
            index = j + 37
            temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big')
            charge[j] = (temp & _value) if bool(temp & _hit) else 0
        # we will no longer check ChipID
        # triggerID,the same triggerID marks the same event,triggerID will add one every times it trigger,
        # when triggerID adds up to 0xffff,the next triggerID will be 0x0000
        triggerID = int.from_bytes(source[150:152], byteorder='big')
        charge[36] = triggerID
        return charge

    # 辅助函数：解析状态信息
    def _unpackStatus(self,source: bytes) -> list:
        '''
        THE FOEMAT OF DATA PACKAGE:
        ---------STATUS PART-----------
        TrigDAC 1ROW    2Bytes  156-157 0-1
        INDAC   1ROW    2Bytes  158-159 2-3
        TrigMode1ROW    2Bytes  160-161 4-5
        BoardID 1ROW    2Bytes  162-163 6-7
        TOTAL SIZE: 8
        *********UNPACKED DATA*********
        NAME        LENGTH
        TrigDAC     1
        INDAC       1
        TrigMode    1
        BoardID     1
        TOTAL LENGTH: 4
        ===============================
        :param source: 8Bytes-Just status part.
        :return:    list-len=4
        '''
        # 解析状态信息
        status = []
        TrigDAC = int.from_bytes(source[:2],byteorder='big',signed=True)
        status.append(TrigDAC)
        INDAC = int.from_bytes(source[2:4],byteorder='big',signed=True)
        status.append(INDAC)
        trigMode = int.from_bytes(source[4:6],byteorder='big',signed=True)
        status.append(trigMode)
        boardID = int(math.log(source[7], 2))
        status.append(boardID)
        return status

    # 辅助函数：检查包长情况
    def _checkPackageLength(self,source: bytes) -> int:
        length = len(source)
        if length == 156:
            return 1
        elif length == 8:
            return 2
        elif length > 156:
            try:
                idx = source.index(b'\xfa\x5a',2)
                if len(source[idx:]):
                    return 0
            except ValueError:
                return -1
        else:
            return -1

    # 发送消息线程
    def sendMessage(self):
        while self._threadTag.is_set():
            self._messageQueue.put(
                "===={}====\nevent count:{}\n{}".format(
                    datetime.now().strftime("%H:%M:%S"), self.eventCount(), self.badPackage()))
            print("===={}====\nevent count:{}\n{}".format(
                datetime.now().strftime("%H:%M:%S"), self.eventCount(), self.badPackage()))
            time.sleep(5)

if __name__ == "__main__":
    import pyqtgraph.examples
    pyqtgraph.examples.run()