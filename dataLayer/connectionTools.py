'''
包含与设备通讯的类
'''

import numpy as np
import os
import math
import socket
import asyncio
import threading
from datetime import datetime
from multiprocessing import Queue, Event, SimpleQueue
from dataLayer.shareMemory import getShare
from dataLayer.baseCore import shareStorage, h5Data
from dataLayer.constantParameter import sizeUnit_binary
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

# 为数据接收服务所编写的解析二进制数据类
class Lumis_Decode(object):
    def __init__(self):
        # ---- 配置量 ----
        self._readSize = 1024 * 1024  # 每次读取数据的大小
        # ---- 统计量 ----
        # 坏包（扔掉的包）计数
        self._empty = 0  # 空包数
        self._interrupt = 0  # 遭受中断的包数
        self._unknow = 0  # 未知情况的包数
        # 数据计数
        self._count = 0  # 接收的包的总数目/当前数据的行数
        self._eventCount = 0 # 接收到的事件数
        self._temTID = 1  # 当前包的triggerID
        # ---- 缓存量 ----
        self._binaryBuff = SimpleQueue()   # 存储二进制数据流的缓存队列
        self._eventBuff = []    # 存储单个事件中各个板数据的缓冲列表
        self._statusBuff = {}   # 存储当前下位机状态的元组对象

    # 重新初始化统计量和缓存量
    def reInitialize(self):
        # ---- 统计量 ----
        # 坏包（扔掉的包）计数
        self._empty = 0  # 空包数
        self._interrupt = 0  # 遭受中断的包数
        self._unknow = 0  # 未知情况的包数
        # 数据计数
        self._count = 0  # 接收的包的总数目/当前数据的行数
        self._eventCount = 0  # 接收到的事件数
        self._temTID = 1  # 当前包的triggerID
        # ---- 缓存量 ----
        # 清空的数据缓存区数据
        self._binaryBuff = SimpleQueue()
        self._eventBuff.clear()
        self._statusBuff.clear()

    # 设置每次读取数据最大值的大小
    def setReadSize(self, size: int, unit: sizeUnit_binary = sizeUnit_binary.B):
        self._readSize = size * unit.value

    #=======返回内部信息量函数===========
    def badPackage(self) -> tuple:
        '''
        返回坏包的数量
        :return: tuple(空包数,中断次数,无法识别包数)
        '''
        return self._empty, self._interrupt, self._unknow

    def eventCount(self) -> tuple:
        '''
        返回采集到的事件数
        :return: tuple(采集到的数据包个数, 采集到的有效事件数)
        '''
        return self._count, self._eventCount

    def readSize(self) -> int:
        '''
        :return: 每次读取数据的大小
        '''
        return self._readSize

    def devStatus(self) -> dict:
        '''
        返回设备配置状态
        :return: key: boardID; value: tuple(threshold, bias voltage, trigger mode)
        '''
        return self._statusBuff

    # ===============解析二进制数据==============
    def _decodingData(self,source: bytes) -> np.array:
        '''
        解析一个SSP2E数据包
        THE FOEMAT OF SOURCE:
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
        *********DECODED DATA*********
        NAME            LENGTH
        CHARGE          36
        TrigID          1
        TOTAL LENGTH:   37
        ===============================
        :param source:  156Bytes-Just data part
        :return: np.array-shape=(38,1),but there are only 37 valid data points.
        '''
        # check the header and the tail bytes
        if not source[0:2] == b'\xfa\x5a':
            raise ValueError("Packet header does not match.")
        elif not source[152:] == b'\xfe\xee\xfe\xee':
            raise ValueError("Packet tails do not match.")
        charge = np.empty(38, dtype='uint16')  # 存储解析后数据的位置
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

    def _decodingStatus(self,source: bytes) -> list:
        '''
        解析状态信息
        THE FOEMAT OF SOURCE:
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
        :param source: 8Bytes.Just status part.
        :return:    list
        '''
        status = []
        TrigDAC = int.from_bytes(source[:2], byteorder='big', signed=True)
        status.append(TrigDAC)
        INDAC = int.from_bytes(source[2:4], byteorder='big', signed=True)
        status.append(INDAC)
        trigMode = int.from_bytes(source[4:6], byteorder='big', signed=True)
        status.append(trigMode)
        boardID = int(math.log(source[7], 2))
        status.append(boardID)
        return status

    def decodingOneEventData(self) -> np.array:
        '''
        解析一个事件的数据,当数据不足时会阻塞
        当解析到终止信息None时会抛出异常
        ======THE FORMAT OF SOURCE=====
        ---------DATA PART-------------
        NAME    ROW     SIZE    LOCAL
        HAED    1ROW    2Bytes  0-1
        HGain   36ROW   72Bytes 2-73
        LGain   36ROW   72Bytes 74-145
        BCID    1ROW    2Bytes  146-147
        ChipID  1ROW    2Bytes  148-149
        Trigger 1ROW    2Bytes  150-151
        TAIL    1ROW    4Bytes  152-155
        ---------STATUS PART-----------
        TrigDAC 1ROW    2Bytes  156-157 0-1
        INDAC   1ROW    2Bytes  158-159 2-3
        TrigMode1ROW    2Bytes  160-161 4-5
        BoardID 1ROW    2Bytes  162-163 6-7
        TOTAL SIZE: 164

        ======RETURN DATA FORMAT=====
        shape   (n, 38)
        ---------AXIS 0----------
        board   0~n
        ---------AXIS 1-----------
        NAME            LENGTH
        CHARGE          36
        TrigID          1
        BOARDID         1
        TOTAL LENGTH:   38
        ---------------------------
        DATA TYPE:  np.array
        dtype:      uint16
        :return: np.array:all the valid board data in one event,shape(n,38)
        '''
        while True:
            buff = self._binaryBuff.get()
            # 接收到终止信号
            if buff == -1:
                print(buff == -1)
                raise asyncio.CancelledError
            check = self._checkPackageLength(buff)
            # 如果接收到的是中断
            if check == 0:
                self._interrupt += 1
                newHead = buff.index(b'\xfa\x5a')
                buff = buff[newHead:]
                self._eventBuff.clear()
                check = self._checkPackageLength(buff)
            # 接收到的是正常的包
            if check == 1:
                self._count += 1
                chargeData = self._decodingData(buff[:-8])
                statusData = self._decodingStatus(buff[-8:])
                # 将boardID载入
                chargeData[-1] = statusData[-1]
                # 将设备状态信息更新
                self._statusBuff[statusData[-1]] = tuple(statusData[:-1])
                # 如果在同一个事件中，则将数据存储在事件缓存区中,同时将triggerID改为软件计数器的计数
                if self._temTID == chargeData[-2]:
                    chargeData[-2] = self._eventCount
                    self._eventBuff.append(chargeData)
                # 接收到的是新的事件
                else:
                    event = np.array(self._eventBuff)
                    self._eventBuff.clear()
                    # 更新当前事件ID和软件计数
                    self._temTID = chargeData[-2]
                    self._eventCount += 1
                    #将triggerID改为软件计数器的计数
                    chargeData[-2] = self._eventCount
                    self._eventBuff.append(chargeData)
                    return event
            # 接收到的是空包
            elif check == 2:
                self._empty += 1
                triggerID = int.from_bytes(buff[2:4],byteorder='big',signed=False)
                # 如果接收到的是新事件
                if self._temTID != triggerID:
                    # 更新状态信息
                    statusData = self._decodingStatus(buff[-8:])
                    self._statusBuff[statusData[-1]] = tuple(statusData[:-1])
                    # 获取上一个事件的数据
                    event = np.array(self._eventBuff)
                    self._eventBuff.clear()
                    # 更新当前事件ID和软件计数
                    self._temTID = triggerID
                    self._eventCount += 1
                    return event
            # 遇到未知情况
            else:
                self._unknow += 1

    # ==============辅助函数=============
    def _checkPackageLength(self,source: bytes) -> int:
        '''
        检查二进制数据(SSP2E包+status information)的长度
        :param source: one board binary package
        :return: 1 normal package
                 2 empty package
                 3 interrupt package
                 -1 unknown package
        '''
        length = len(source)
        if length == 164:
            return 1
        elif length == 16:
            return 2
        elif length > 164:
            try:
                idx = source.index(b'\xfa\x5a', 2)
                if len(source[idx:]):
                    return 0
            except ValueError:
                print(source.hex('-'))
                return -1
        else:
            return -1

    # =============搜寻在二进制数据中搜寻SSP2E数据包和状态信息包===========
    def findSSP2EIndex(self,source: bytes):
        '''
        搜寻二进制数据包头和包尾
        :param source: raw binary data
        :return: tuple() :list of head index;list of tail index; remained data
        '''
        tail = 0
        headList = []
        tailList = []
        while True:
            try:
                head = source.index(b'\xfa\x5a', tail)
                tail = source.index(b'\xfe\xee\xfe\xee',head)
            except:
                break
            if len(source) < tail+12:
                try:
                    tail = tailList[-1]
                except IndexError:
                    tail = 0
                finally:
                    break
            headList.append(head)
            tailList.append(tail)
        return headList,tailList,source[tail:]

    def loadBinaryData(self,source: bytes) -> bytes:
        '''
        将二进制数据根据SSP2E包切分后放入缓存队列中
        :param source: raw binary data
        :return: remained data
        '''
        tail = 0
        while True:
            try:
                head = source.index(b'\xfa\x5a', tail)
                tail = source.index(b'\xfe\xee\xfe\xee',head)
            except:
                return source[tail+12:]
            if len(source) < tail + 12:
                return source[head:]
            buff = source[head:tail+12]
            self._binaryBuff.put(buff)

    def putStopOrder(self):
        '''
        在数据队列_binaryBuff中添加一个停止信息None,当解析到None时,会抛出异常
        :return:
        '''
        self._binaryBuff.put(-1)

'''
    需要载入的对象：├│└
dataChannel
    ├shareStorage
    │   ├setH5Path()
    │   ├addMemoryData()
    │   ├setStatus()
    │   └clear()
    ├dataTag
    ├processTag
    ├messageQueue
    └orderPipe
'''

async def loadDataFromSocket(_s: socket.socket, _q: Queue, tag: Event, decodeTool: Lumis_Decode):
    '''
    协程函数：从socket中获取原始数据
    :param _s: 获取数据的socket
    :param tag: 消息队列
    :param _e: 运行状态标志
    :param decodeTool: 解码工具
    :return:
    '''
    tag.clear()
    try:
        reader, writer = await asyncio.open_connection(sock=_s)
        writer.write(b'\xff\x00')
        buff = b''
        while True:
            buff += await reader.read(decodeTool.readSize())
            buff = decodeTool.loadBinaryData(buff)
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        _q.put((-1, 'an excaption has occurred in load data thread:{}',e.__str__()))
    finally:
        _s.close()
        tag.set()
        # 当解码进程解析到结束信号时会结束循环
        decodeTool.putStopOrder()
        print('loadDataFromSocket:', 'end')

async def sendStatusMessage(_q: Queue, tag: Event, decodeTool: Lumis_Decode):
    '''
    协程函数：定时发送当前接收状态
    :param _q:消息队列
    :param decodeTool:解码工具
    :param share: 共享数据
    :return:
    '''
    tag.clear()
    try:
        while True:
            await asyncio.sleep(5)
            badPack = decodeTool.badPackage()
            count = decodeTool.eventCount()
            info = "-----BAD PACKAGE-----\n" \
                   "empty package:{}\n" \
                   "interrupt count:{}\n" \
                   "unknown package:{}\n" \
                   "total bad package:{}\n" \
                   "-----EVENT COUNT-----\n" \
                   "received package:{}\n" \
                   "valid event:{}\n" \
                   "---------------------".format(
                *badPack,
                badPack[0] + badPack[1] + badPack[2],
                *count
            )
            _q.put((0,info))
    except asyncio.CancelledError:
        pass
    finally:
        tag.set()
        print("sendStatusMessage:", 'end')

def dataDecode(share: shareStorage, decodeTool: Lumis_Decode, fileName: str = None):
    '''
    a thread function to decode binary data.
    负责解码数据，将数据写入h5文件，开始时将写入设备配置状态。
    为h5文件的全部可执行域。
    :param stopTag: a flag/tag to stop this thread
    :param share: share data storage
    :param decodeTool: to decode binary data
    :param fileName: h5 file name
    :return:
    '''
    # 初始化h5文件
    today = datetime.now().strftime('%Y_%m_%d')
    dirPath = os.path.join('.','data',today)
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
    if fileName is None:
        nowTime = datetime.now().strftime('%H_%M_%S')
        h5Path = os.path.join(dirPath,'tempData_'+nowTime+'.h5')
    else:
        h5Path = os.path.join(dirPath, fileName.split('.')[0])
    h5 = h5Data(h5Path)
    # 将文件路径添加到共享内存中去
    share.setFilePath(h5Path)
    h5.startTime()
    # 开始解码数据
    try:
        event = decodeTool.decodingOneEventData()
        # 对于第一组数据，除将数据导入h5文件中，还会将状态信息导入h5文件
        if event.shape[0] != 0:
            h5.addToDataSet(event)
        h5.putDeviceStatus(decodeTool.devStatus())
        while True:
            event = decodeTool.decodingOneEventData()
            # 将数据导入h5文件中（需要检查当前事件是否全为空包）
            if event.shape[0] != 0:
                h5.addToDataSet(event)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print('dataDecode:',e.__str__())
        import traceback
        traceback.print_exc()
    finally:
        h5.stopTime()
        h5.close()
    print('dataDecode:','end')

async def dataReceiveThread(share: shareStorage):
    pipe_r = share.orderPipe(False)
    decodeTool = Lumis_Decode()
    messageQueue = share.messageQueue()
    # 两个协程的运行标志
    tag_receive = Event()
    tag_message = Event()
    while True:
        await asyncio.sleep(0.5)
        if pipe_r.poll():
            order = pipe_r.recv()
            # 接收到开始接收数的指令
            if isinstance(order,str) or order == 1:
                if share.dataTag().is_set():
                    messageQueue.put((2, 'the receiving data module is running.'))
                    continue
                # 检查是否能连接到下位机
                s = socket.socket()
                try:
                    s.connect((_devIP,_TCPport))
                except ConnectionRefusedError as e:
                    messageQueue.put((-2,e.__str__()))
                    continue
                except Exception as e:
                    messageQueue.put((-1,e.__str__()))
                    continue
                share.dataTag().set()
                decodeTool.reInitialize()
                # 添加数据接收协程和发送消息协程
                task_receive = asyncio.create_task(
                    loadDataFromSocket(s, messageQueue, tag_receive, decodeTool=decodeTool))
                task_message = asyncio.create_task(
                    sendStatusMessage(messageQueue, tag_message, decodeTool=decodeTool))
                # 开启数据解码线程
                thread_decoding = threading.Thread(target=dataDecode,
                                                   args=(share, decodeTool, order if isinstance(order, str) else None))
                thread_decoding.setDaemon(True)
                thread_decoding.start()
                messageQueue.put((1, 'successfully started receiving data.'))
            elif order == 0:
                if share.dataTag().is_set():
                    #停止接收数据
                    task_receive.cancel()
                    task_message.cancel()
                    await asyncio.sleep(0.1)
                    thread_decoding.join()
                    share.dataTag().clear()
                    messageQueue.put((1, 'successfully stopped receiving data.'))
                else:
                    messageQueue.put((2, 'the receiving data module is not running.'))
            elif order == -1:
                if share.dataTag().is_set():
                    # 如果正在接收数据
                    task_receive.cancel()
                    task_message.cancel()
                    await asyncio.sleep(0.1)
                    thread_decoding.join()
                    share.dataTag().clear()
                #结束进程
                break

def ConnectProcess():
    myShare = getShare(False)
    asyncio.run(dataReceiveThread(myShare))
    myShare.messageQueue().put((1, 'the connection process has exited.'))


if __name__ == "__main__":
    import pyqtgraph.examples
    pyqtgraph.examples.run()