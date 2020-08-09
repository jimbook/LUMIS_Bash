import sys
from PyQt5.QtWidgets import QApplication
from mainWindow import window
from multiprocessing import Process
from globelParameter import DataManager,_address,_authkey,dataReceiveServer
import profile
import cProfile
# 已弃用，开GUI进程
def process_GUI():
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_())
    print("end")

# 开启数据接收进程
def process_DataServer():
    # 连接共享数据服务
    DM = DataManager(address=_address,authkey=_authkey)
    DM.connect()
    # 从共享数据服务中获取共享对象
    _shareData = DM.get_shareData()
    _threadTag = DM.get_threadTag()
    _dataTag = DM.get_dataTag()
    _processTag = DM.get_processTag()
    _messageQueue = DM.get_messageQueue()
    # 对标志变量进行初始化
    _threadTag.clear()
    _processTag.set()
    _dataTag.set()
    print("数据接收进程初始化成功{}".format(_processTag.is_set()))
    dataReceiveServer(_shareData,_threadTag,_dataTag,_processTag,_messageQueue)

if __name__ == "__main__":
    import cProfile, pstats, io
    from pstats import SortKey
    pr = cProfile.Profile()
    pr.enable()
    # ... do something ...

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
    app = QApplication(sys.argv)
    try:
        ex = window(manager=manager)
        ex.show()
    except:
        import traceback
        traceback.print_exc()
    app.exec_()
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())