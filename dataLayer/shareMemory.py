'''
    共享内存部分
    需要共享的几个对象：
    1.dataStorage--dataStorage():数据解析和存储
    2.threadTag--Event():关闭线程的事件
    3.processTag--Event():关闭进程的事件
    4.messageQueue--SimpleQueue():消息队列
'''
from multiprocessing.managers import BaseManager
from multiprocessing import SimpleQueue
from threading import Event
from dataLayer.baseCore import dataStorage
# ---------共享数据地址---------
_address = ("127.0.0.1",50000)
_authkey = b'jimbook'

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

    def startReceiveData(self):
        self.threadTag.set()

    def stopReceiveData(self):
        self.threadTag.clear()

    def getMessage(self):
        msg = self.mq.get()
        return msg

