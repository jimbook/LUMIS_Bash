import sys
import time
from PyQt5.QtWidgets import QApplication
from GuiLayer.mainWindow import window
from multiprocessing import Process,Event
from dataLayer.shareMemory import getShare,_address,_authkey
from dataLayer.connectionTools import ConnectProcess

if __name__ == "__main__":
    try:
        shareStorge = getShare(False)
        print("检测到数据服务已存在。")
    except ConnectionRefusedError:
        print("正在开启新的数据服务，请稍后")
        e = Event()
        shareManage = Process(target=getShare,args=(True,))
        shareManage.start()
        time.sleep(1)
        p = Process(target=ConnectProcess)
        p.start()
        shareStorge = getShare(False)
    # 开启GUI进程
    app = QApplication(sys.argv)
    try:
        ex = window(shareChannel = shareStorge)
        ex.show()
    except:
        import traceback
        traceback.print_exc()
    app.exec_()
    # pr.disable()
    # s = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # print(s.getvalue())