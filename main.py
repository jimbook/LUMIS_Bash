import sys
from PyQt5.QtWidgets import QApplication
from mainWindow import window
from multiprocessing import Process
from globelParameter import DataManager,_address,_authkey,dataReceiveServer
#
def process_GUI():
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_())
    print("end")

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
    print("开始计数,process:{}".format(_processTag.is_set()))
    dataReceiveServer(_shareData,_threadTag,_dataTag,_processTag,_messageQueue)

if __name__ == "__main__":
    try:
        manager = DataManager(address=_address, authkey=_authkey)
        manager.connect()
        print("检测到数据服务已存在。")
    except ConnectionRefusedError:
        print("正在开启新的数据服务，请稍后")
        manager = DataManager(address=_address, authkey=_authkey)
        manager.start()
        dataServer = Process(target=process_DataServer)
        # dataServer.daemon = True
        dataServer.start()
        # 开启GUI进程
    # GUI = Process(target=process_GUI)
    # GUI.daemon = True
    # # 开启GUI进程
    # GUI.start()
    # GUI.join()
    # print("out")
    app = QApplication(sys.argv)
    try:
        ex = window(manager=manager)
        ex.show()
    except:
        import traceback
        traceback.print_exc()
    app.exec_()
    print("end")
    #dataServer.terminate()