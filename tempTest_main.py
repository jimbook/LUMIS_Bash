from _test_receiveProcess import sendThread, connectThread
import sys
import time
from multiprocessing import Process, Barrier
from socket import socketpair,socket
from dataLayer.baseCore import shareStorage
from dataLayer.shareMemory import getShare
from GuiLayer.mainWindow import window
from PyQt5.Qt import QApplication

def sendThread(_s: socket, path: str, sleep: float = 0.1):
    '''
    --线程--
    模拟socket发送数据线程，从测试数据文件中获取二进制数据
    :param _s: 发送端的socket
    :param _b: 结束等待栅栏对象
    :param sleep: 发送间隔
    :return:
    '''
    time.sleep(sleep*15)
    with open(path, 'rb') as binaryFile:
        print('sendThread:', 'start')
        while True:
            buff = binaryFile.read(1024)
            if buff == b'':
                print('sendThread:', 'send all')
                break
            try:
                _s.send(buff)
                time.sleep(sleep)
            except Exception as e:
                print('sendThread:', e.__str__())
                break
    print('sendThread:', "end")
    time.sleep(100)
    _s.close()

binaryPath =  './testData/binaryData/20201025_1315.dat'#'testData/binaryData/nowData/20200930_1140-2109.dat'
if __name__ == '__main__':
    m_thread = Process(name='share data manager', target=getShare, args=(True,))
    m_thread.start()
    time.sleep(3)
    dataChannel = getShare(False)
    s_socket, r_socket = socketpair()
    s_thread = Process(name='send binary thread', target=sendThread, args=(s_socket, binaryPath))
    r_thread = Process(name='data receive thread', target=connectThread, args=(dataChannel, r_socket))
    s_thread.start()
    r_thread.start()
    # 开启GUI进程
    app = QApplication(sys.argv)
    try:
        ex = window(shareChannel=dataChannel)
        ex.show()
    except:
        import traceback
        traceback.print_exc()
    app.exec_()

