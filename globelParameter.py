'''
    需要共享的几个对象：
    1.dataStorage--dataStorage():数据解析和存储
    2.threadTag--Event():关闭线程的事件
    3.processTag--Event():关闭进程的事件
    4.messageQueue--SimpleQueue():消息队列
'''
import gc
import os
import time
import socket
import numpy as np
import pandas as pd
from datetime import datetime
from multiprocessing.managers import BaseManager
from multiprocessing import SimpleQueue,Process,Queue
from threading import Lock,Event
from dataAnalyse import _hit,_gain,_value
_address = ("127.0.0.1",50000)
_authkey = b'jimbook'
_chnList = []
_typeList = []
def _initIndex():
    for i in range(0, 36, 1):
        for j in ["time/LowGain", "charge/HighGain"]:
            _chnList.append("chn_" + str(i))
            _chnList.append("chn_" + str(i))
            _chnList.append("chn_" + str(i))
            _typeList.append(j + "_gain")
            _typeList.append(j + "_hit")
            _typeList.append(j)
    _chnList.append("SCAinfo")
    _typeList.append("bounchCrossingID")
    _chnList.append("SCAinfo")
    _typeList.append("triggerID")
    _chnList.append("SCAinfo")
    _typeList.append("BoardID")
_initIndex()

# 一个包含保护数据线程锁的共享数据对象
class dataStorage(object):
    def __init__(self):
        self.dataLock = Lock()
        self.memoryData = []
        self.diskData = []

    def addMeoryData(self,inpute: list):
        with self.dataLock:
            self.memoryData.append(inpute)

    def resetMeoryData(self,filePath: str):
        with self.dataLock:
            self.memoryData.clear()
            self.diskData.append(filePath)

    def clear(self):
        with self.dataLock:
            self.memoryData.clear()
            self.diskData.clear()

    def get_memoryData(self):
        with self.dataLock:
            return self.memoryData

    def get_diskData(self):
        with self.dataLock:
            return self.diskData

    def get_both(self):
        with self.dataLock:
            return self.memoryData,self.diskData

# 为数据接收服务进程所编写的解析二进制数据类
class unpack(object):
    _devIP = '192.168.10.16'
    _TCPport = 24

    def __init__(self, *args, message_queue: SimpleQueue, tag: Event, data_storage: dataStorage):
        super(unpack, self).__init__(*args)
        # 坏包（扔掉的包）计数
        self._lenError = 0  # 长度不合适的包
        self._ChipIDError = 0  # chipID 错误的包
        # 数据计数
        self._count = 0  # 接收的包的总数目/当前数据的行数
        self._tCount = 0  # triggerID重置的次数
        self._temTID = 0  # 当前包的triggerID
        # 辅助参数
        self._readSize = 1024 * 256  # 每次读取数据的大小
        self._threadTag = tag  # 标志线程是否应该结束
        self._messageQueue = message_queue  # 用于向GUI发送消息
        self._sock = socket.socket()  # 连接
        self._sock.settimeout(5)
        self._fileDir = None  # 数据存储路径
        # 数据相关
        self._dataStorage = data_storage  # 用于将数据放入数据服务

    def __len__(self):
        return self._count

    # ==================返回内部信息的函数=======================
    # 返回以字符串形式的坏包信息，或返回int形式的总坏包数
    def badPackage(self, ToString: bool = True):
        if ToString:
            return "bad package:{}; length error:{},chipID error:{}".format(self._lenError + self._ChipIDError,
                                                                            self._lenError, self._ChipIDError)
        else:
            return self._lenError + self._ChipIDError

    # 清空当前坏包统计
    def clearBadPackage(self):
        self._lenError = 0
        self.ChipIDError = 0

    # 返回当前采集到的事件数
    def eventCount(self):
        #return self._temTID + self._tCount * 65535
        return self._count

    # --------------------------------------------------------

    # 设置每次读取数据的大小
    def setReadSize(self, size: int):
        self._readSize = size

    # 接收数据,如果发生错误，会将线程标志置False
    def load(self):
        self._dataStorage.clear()
        # 连接TCP连接，并发送开始数据传输命令，如果报错(无法连接)则直接返回False
        try:
            self._sock.connect((self._devIP, self._TCPport))
            self._sock.send(b'\xff\x00')  # 发送命令，开始接收数据
        except Exception as e:
            self._threadTag.clear()
            self._messageQueue.put("an exception occurred while receiving data:\n" + e.__str__())
            return False
        # 成功连接后，创建数据存储文件夹，向info文件中添加开始接收数据的时间戳，然后开始接收数据，结束时向info添加结束时间戳
        try:
            self._messageQueue.put("TCP connect successfuly")
            print("成功连接到设备")
            today = datetime.now().strftime("%Y_%m_%d")
            nowTime = datetime.now().strftime("%H%M%S")
            start_time = time.time()
            if not os.path.exists(os.path.join(".\\data", today)):
                os.makedirs(os.path.join(".\\data", today))
            self._fileDir = os.path.join(".\\data", today, nowTime + "_data")
            os.makedirs(self._fileDir)  # 创建数据存储文件夹
            self._addInfoToDisk("start time:{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))  # 记录开始时间
            print("新建文件夹")
            self._loadsocket()
            self._sock.send(b'\xff\x01')  # 发送停止接收数据的指令
            self._sock.close()
            self._messageQueue.put("stop command has sent,waiting for the cached data to be processed.")
        except socket.timeout:
            self._sock.send(b'\xff\x01')  # 发送停止接收数据的指令
            self._sock.close()
            self._messageQueue.put("stop command has sent,waiting for the cached data to be processed.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._threadTag.clear()
            self._messageQueue.put("an exception occurred while receiving data:\n" + e.__str__())
        finally:
            end_time = time.time()
            self._addInfoToDisk("stop time:{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self._addInfoToDisk("total time: {} sec".format(start_time - end_time))
            self._messageQueue.put("the total time consuming:{}".format(start_time - end_time))

    # auxiliary : search every SS2E packet and invoking the decode function from socket
    # 辅助函数：从socket连接中找到每一个符合规则的SSP2E数据包，然后调用_unpackage函数将这个包解析，将数据载入内存/写入硬盘
    def _loadsocket(self):
        # 添加硬盘文件的路径
        filePath = os.path.join(self._fileDir, "tempData_{}.txt".format(len(self._dataStorage.get_diskData())))
        self._dataStorage.resetMeoryData(filePath)
        file = open(filePath, "w")
        file.write(',' + ','.join(_chnList) + '\n')
        file.write(',' + ','.join(_typeList) + '\n')
        print("开始读取数据")
        # 开始读取数据
        buff = self._sock.recv(self._readSize)
        tails = 0
        print(self._threadTag.is_set())
        while buff != 0 and self._threadTag.is_set():
            print("===={}====\nevent count:{}\n{}".format(
                        datetime.now().strftime("%H:%M:%S"), self.eventCount(), self.badPackage()))
            try:
                header = buff.index(b'\xfa\x5a', tails)
                tails = buff.index(b'\xfe\xee', header)
            except ValueError:  # 如果找不到一个完整的包，则继续读入一部分数据
                b = self._sock.recv(self._readSize)
                self._messageQueue.put(
                    "===={}====\nevent count:{}\n{}".format(
                        datetime.now().strftime("%H:%M:%S"), self.eventCount(), self.badPackage()))
                # 如果没有数据可读，则退出循环
                if len(b) == 0:
                    break
                # 如果文件数据大于32MB，则开启一个新的文件，并清除共享内存中的数据
                if os.path.getsize(filePath) >= 1024 * 1024 * 32:
                    file.close()
                    filePath = os.path.join(self._fileDir,
                                            "tempData_{}.txt".format(len(self._dataStorage.get_diskData())))
                    self._dataStorage.resetMeoryData(filePath)
                    file = open(filePath, "w")
                    file.write(',' + ','.join(_chnList) + '\n')
                    file.write(',' + ','.join(_typeList) + '\n')
                # 将新读入的数据添加到缓存区，并把之前已读的数据清除，同时将包尾的索引清零
                buff = buff[tails + 3:] + b
                tails = 0
                gc.collect()
                continue
            # check the length of package is correct
            # 检查包长是否合适
            if len(buff[header:tails + 4]) == 156:
                self._unpackage(buff[header:tails + 4], file=file)
            else:
                self._lenError += 1
        # 如果是通过threadTag停止循环，将读入剩下的数据
        # if not self._threadTag.is_set():
        #     self._sock.send(b'\xff\x01')  # 发送停止接收数据的指令
        #     self._messageQueue.put("stop command has sent,waiting for the cached data to be processed.")
        #     b = self._sock.recv(1024 * 1024 * 128)  # 读入剩余数据
        #     self._messageQueue.put(
        #         "===={}====\nevent count:{}\n{}".format(
        #             datetime.now().strftime("%H:%M:%S"), self.eventCount(), self.badPackage()))  # 每载入一次数据将会发送一次信号
        #     buff = buff[tails + 3:] + b
        #     tails = 0
        #     while buff != 0:
        #         try:
        #             header = buff.index(b'\xfa\x5a', tails)
        #             tails = buff.index(b'\xfe\xee', header)
        #         except ValueError:
        #             break
        #         # check the length of package is correct
        #         if len(buff[header:tails + 4]) == 156:
        #             self._unpackage(buff[header:tails + 4], file=file)
        #         else:
        #             self._ChipIDError += 1
        file.close()
        gc.collect()

    # auxiliary : decode a SSP2E packet into pd.DataFrame
    # 辅助函数：解析一个SSP2E数据包
    def _unpackage(self, source: bytes, file: open):
        '''
        THE FOEMAT OF DATA PACKAGE:
        HAED    1ROW    2Byte   0-1
        HGain   36ROW   72Byte  2-73
        LGain   36ROW   72Byte  74-145
        BCID    1ROW    2Byte   146-147
        ChipID  1ROW    2Byte   148-149
        Trigger 1ROW    2Byte   150-151
        TAIL    1ROW    2Byte   152-153
        BoardID 1ROW    2Byte   154-155
        -------------------------------
        the length of final data: 219
        ===============================
        :param source:  156Byte
        :param file: if assign a file to this parameter,this function will output the data to the file
        :return: bool,when decord successfully will return True,
                else when chipID is wrong will return False meanwhile chipIDError add one.
        '''
        # check the header and the tail bytes
        if not source[0:2] == b'\xfa\x5a':
            raise ValueError("Packet header does not match.")
        elif not source[152:154] == b'\xfe\xee':
            raise ValueError("Packet tails do not match.")
        charge = [[], [], []]  # 暂时存储解析后数据的位置
        # Charge/HighGain information and time/LowGain information
        for j in range(36):
            index = j + 1
            temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big')
            charge[0].append(bool(temp & _gain))
            charge[1].append(bool(temp & _hit))
            charge[2].append(temp & _value)
            index = j + 37
            temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big')
            charge[0].append(bool(temp & _gain))
            charge[1].append(bool(temp & _hit))
            charge[2].append(temp & _value)
        data = np.array(np.flip(np.array(charge), axis=1)).transpose((1, 0)).reshape((1, -1))
        # Bunch Crossing ID(I don't known what information Bunch Crossing ID wants to show us)
        index = 73
        temp = int.from_bytes(source[index * 2:(index + 1) * 2], byteorder='big')
        data = np.append(data, temp)
        # ChipID ,to make sure the package is not correct.
        ChipID = int.from_bytes(source[148:150], byteorder='big')
        # triggerID,the same triggerID marks the same event,triggerID will add one every times it trigger,
        # when triggerID adds up to 0xffff,the next triggerID will be 0x0000
        triggerID = int.from_bytes(source[150:152], byteorder='big')
        if self._temTID > triggerID:
            self._tCount += 1  # 当triggerID置零时，tCount加一(置零时triggerID并不变成0，而是变成一个较小值400~1500左右)
        self._temTID = triggerID
        data = np.append(data, triggerID + self._tCount * 65, 535)
        # Verify that the data is correct
        if ChipID & int.from_bytes(b'\x00\x01', byteorder='big', signed=True):
            boradID = source[-1]
            data = np.append(data, boradID).reshape((-1, 219))
            # ===================
            string = str(self._count) + "," + ','.join(data.astype('str').tolist()[0])
            file.write(string)
            file.write('\n')
            # ===============
            self._dataStorage.addMeoryData(data.tolist())
            self._count += 1
            return True
        else:
            self.ChipIDError += 1
            return False

    # auiliary :
    # 辅助函数：将一些信息写入日志/信息存档文件
    def _addInfoToDisk(self, info: str):
        with open(os.path.join(self._fileDir, "info.txt"), "a") as file:
            file.write(info)
            file.write('\n')

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
    messageQueue.put("data server end")
    print("数据服务进程已退出")

# ==========共享内存相关===========
class DataManager(BaseManager): # 共享内存管理器
    pass
ds = dataStorage() # 带有线程锁的共享数据
threadTag = Event() # 开始/停止接收数据标志
dataTag = Event()
processTag = Event()    # 数据服务进程退出标志
messageQueue = SimpleQueue() # 消息队列
def get_shareData():    # 返回共享数据的函数
    return ds
def get_threadTag():
    return threadTag
def get_processTag():
    return processTag
def get_dataTag():
    return dataTag
def get_messageQueue():
    return messageQueue
# 将共享的对象注册到DataManage上
DataManager.register("get_shareData",callable=get_shareData)
DataManager.register("get_threadTag",callable=get_threadTag)
DataManager.register("get_dataTag",callable=get_dataTag)
DataManager.register("get_processTag",callable=get_processTag)
DataManager.register("get_messageQueue",callable=get_messageQueue)

#从共享数据服务中获取数据
class dataChannel(object):
    def __init__(self,manager: BaseManager = None):
        if manager is None:
            m = DataManager(address=_address,authkey=_authkey)
            m.connect()
        else:
            m = manager
        # 获取共享数据
        self.dataStorage = m.get_shareData()
        self.threadTag = m.get_threadTag()
        self.dataTag = m.get_dataTag()
        self.processTag = m.get_processTag()
        self.mq = m.get_messageQueue()
        # 数据索引
        self._chnList = []  # chn_0~35,SCAinfo
        self._typeList = []  # low/time:gain,hit,values;high/charge:gain,hit,values;SCAinfo:bcID,triggerID,BoardID
        self._initIndex()  # 初始化上述两个索引列表

    #初始化列索引列表(_chnList和_typeList)
    def _initIndex(self):
        for i in range(0, 36, 1):
            for j in ["time/LowGain", "charge/HighGain"]:
                self._chnList.append("chn_" + str(i))
                self._chnList.append("chn_" + str(i))
                self._chnList.append("chn_" + str(i))
                self._typeList.append(j + "_gain")
                self._typeList.append(j + "_hit")
                self._typeList.append(j)
        self._chnList.append("SCAinfo")
        self._typeList.append("bounchCrossingID")
        self._chnList.append("SCAinfo")
        self._typeList.append("triggerID")
        self._chnList.append("SCAinfo")
        self._typeList.append("BoardID")

    def startReceiveData(self):
        self.threadTag.set()

    def stopReceiveData(self):
        self.threadTag.clear()

    def getMessage(self):
        msg = self.mq.get()
        return msg

# 测试用函数，将消息队列中的消息打印出来
def reM():
    drm = DataManager(address=_address,authkey=_authkey)
    drm.connect()
    mq = drm.get_messageQueue()
    while True:
        print(mq.get())

# 测试用函数，数据服务进程
def DR():
    drm = DataManager(address=_address,authkey=_authkey)
    drm.connect()
    _d = drm.get_shareData()
    _tag = drm.get_threadTag()
    _dTag = drm.get_dataTag()
    _pTag = drm.get_processTag()
    _mq = drm.get_messageQueue()
    _tag.clear()
    _pTag.set()
    _dTag.set()
    print("开始计数",)
    dataReceiveServer(_d,_tag,_dTag,_pTag,_mq)


if __name__ is "__main__":
    import time
    m = DataManager(address=_address,authkey=_authkey)
    m.start()
    p1 = Process(target=DR)
    p2 = Process(target=reM)
    p1.start()
    p2.start()
    print("sleep")
    time.sleep(30)
    th = m.get_threadTag()
    th.set()
    print("start:")
    p1.join()
    p2.join()
    time.sleep(30)

