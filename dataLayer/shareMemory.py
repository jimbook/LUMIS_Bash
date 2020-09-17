'''
    共享内存部分
    需要共享的几个对象：
    1.dataStorage--dataStorage():数据解析和存储
    2.messageQueue--SimpleQueue():消息队列
    3.事件/状态标志：
        todo:将操作数据接收进程的功能分离到指令管道中去，事件/状态标志简化为：
        (1)processTag--Event():标志数据接收进程是否存活
        (2)dataTag--Event():标志是否处于数据接收状态
    4.orderPipe--Pipe():指令管道
'''
from multiprocessing.managers import BaseManager
from multiprocessing import SimpleQueue, Pipe
from multiprocessing.connection import PipeConnection
from threading import Event
from dataLayer.baseCore import shareStorage
# ---------共享数据地址---------
_address = ("127.0.0.1", 50000)
_authkey = b'jimbook'

# ==========共享内存相关===========
class DataManager(BaseManager):   # 共享内存管理器
    pass

ds = shareStorage()  # 带有线程锁的共享数据
dataTag = Event()   # 数据接收状态标志
processTag = Event()    # 数据服务进程退出标志
messageQueue = SimpleQueue() # 消息队列
orderPipe_send, orderPipe_recv = Pipe(False) # 指令管道
def get_shareData():    # 返回共享数据的函数
    return ds
def get_processTag():
    return processTag
def get_orderPipe(send):
    if send:
        return orderPipe_send
    else:
        return orderPipe_recv
def get_dataTag():
    return dataTag
def get_messageQueue():
    return messageQueue
# 将共享的对象注册到DataManage上
DataManager.register("get_shareData",callable=get_shareData)
DataManager.register("get_messageQueue",callable=get_messageQueue)
DataManager.register("get_dataTag",callable=get_dataTag)
DataManager.register("get_processTag",callable=get_processTag)
DataManager.register("get_orderPipe",callable=get_orderPipe)

#从共享数据服务中获取数据
class dataChannel(object):
    def __init__(self,manager: BaseManager = None):
        if manager is None:
            self.m = DataManager(address=_address,authkey=_authkey)
            self.m.connect()
        else:
            self.m = manager

    # 获取共享数据
    def shareStorage(self) -> shareStorage:
        return self.m.get_shareData()

    # 获取状态标志
    def dataTag(self) -> Event:
        return self.m.get_dataTag()

    def processTag(self) -> Event:
        return self.m.get_processTag()

    # 获取发送消息的管道
    def orderPipe(self,send: bool) -> PipeConnection:
        return self.m.get_orderPipe(send)

    # 获取消息队列
    def messageQueue(self) -> SimpleQueue:
        return self.m.get_messageQueue()


