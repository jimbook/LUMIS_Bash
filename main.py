import sys
from PyQt5.QtWidgets import QApplication
from mainWindow import window
from multiprocessing import Process
from globelParameter import DataManager,_address,_authkey,dataReceiveServer
#
def main():
    manager = DataManager(address=_address, authkey=_authkey)
    try:
        manager.connect()
        print("检测到数据服务已存在。")
    except ConnectionRefusedError:
        print("正在开启新的数据服务，请稍后")
        manager.start()
        dataServer = Process(target=process_DataServer)
        dataServer.start()
        # 开启GUI进程
    GUI = Process(target=process_GUI)
    GUI.start()
    # 开启GUI进程
    GUI.start()
    GUI.join()



def process_GUI():
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_())

def process_DataServer():
    DM = DataManager(address=_address,authkey=_authkey)
    DM.connect()
    _shareData = DM.get_shareData()
    _threadTag = DM.get_threadTag()
    _dataTag = DM.get_dataTag()
    _processTag = DM.get_processTag()
    _messageQueue = DM.get_messageQueue()
    _threadTag.clear()
    _processTag.set()
    _dataTag.set()
    print("开始计数")
    dataReceiveServer(_shareData,_threadTag,_dataTag,_processTag,_messageQueue)