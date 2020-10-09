import time
import asyncio
from socket import socketpair, socket
from threading import Thread,Event ,Barrier
from dataLayer.baseCore import shareStorage
from dataLayer.connectionTools import Lumis_Decode, dataReceiveThread

#==============线程函数:辅助测试函数==================
def sendThread(_s: socket, path: str,_b: Barrier, sleep: float = 0.1):
    '''
    --线程--
    模拟socket发送数据线程，从测试数据文件中获取二进制数据
    :param _s: 发送端的socket
    :param _b: 结束等待栅栏对象
    :param sleep: 发送间隔
    :return:
    '''
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
    _b.wait()
    print('sendThread:', "end")
    _s.close()

def receiveThread(_s: socket, _b: Barrier, tool: Lumis_Decode):
    '''
    --线程--
    测试接收数据线程
    :param _s: 接收数据的socket
    :param _b: 结束等待栅栏对象
    :param tool: 解析二进制数据工具
    :return:
    '''
    _s.settimeout(1)
    buff = _s.recv(1024)
    print('receiveThread:', 'start')
    while True:
        rbuff = tool.loadBinaryData(buff)
        try:
            buff = rbuff + _s.recv(1024)
        except Exception as e:
            print('receiveThread:', e.__str__())
            tool.putStopOrder()
            break
    _b.wait()
    _s.close()
    print('receiveThread:', 'end')

def decodeThread(_b: Barrier, tool: Lumis_Decode):
    '''
    --线程--
    测试解码类解码(解码数据不保存)数据线程
    :param _b: 结束等待栅栏对象
    :param tool: 解码数据类
    :return:
    '''
    print('decodeThread:', 'start')
    while True:
        try:
            event = tool.decodingOneEventData()
        except asyncio.CancelledError:
            break
        badPack = tool.badPackage()
        count = tool.eventCount()
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
        print(info)
    _b.wait()
    print('decodeThread:', 'end')

def orderSimulate(dc: shareStorage, _b: Barrier):
    '''
    --线程--
    模拟GUI向数据接收进程发送指令,然后打印消息队列中的消息
    :param dc: 获取共享数据类
    :param _b: 结束等待栅栏对象
    :return:
    '''
    # order = int(input("orderSimulate:"))
    # if order == 0 or order == -1 or order == 1:
    #     print("input:", order)
    #     dc.orderPipe(True).send(order)
    print('order start')
    dc.orderPipe(True).send(2)
    message = None #
    n = 0
    while True:
        time.sleep(0.2)
        result, _message = dc.messageQueue().get()
        print(_message)
        if message == _message:#or n == 60
            print("orderSimulate:", 'send end order')
            dc.orderPipe(True).send(-1)
        else:
            message = _message
            n += 1
        if result == -1:
            print("orderSimulate:", 'receive end return')
            break
    _b.wait()
    print("orderSimulate:", "end")

def connectThread(dc: shareStorage, s: socket):
    '''
    --线程--
    模拟接收数据进程
    :param dc: 共享数据类
    :param s: 接收数据的socket
    :return:
    '''
    asyncio.run(dataReceiveThread(share=dc, _s=s))
    dc.messageQueue().put((-1, 'the connection process has exited.'))
    print('connectThread:','end')

#===================测试函数==================
def LumisDecode_Test():
    '''
    测试dataLayer.connectionTools中Lumis_Decode对象的功能
    ===========测试逻辑========
    测试模块分为三个线程：
    1.模拟socket发送数据线程
        载入二进制文件中的二进制数据，通过建立了连接的两个socket中的一个向另一个发送数据，以模拟设备通过网络协议向软件发送数据
    2.载入数据线程：
        模拟载入数据协程的功能，将二进制数据按每个板子分开存储到队列中区
    3.解析数据线程：
        模拟解析数据线程
    :return:
    '''
    socket1, socket2 = socketpair()
    tool = Lumis_Decode()
    b = Barrier(3)
    s = Thread(target=sendThread,args=(socket1, 'testData/binaryData/DAC360_0902_2249-0903_1102.dat', b, 0))
    r = Thread(target=receiveThread, args=(socket2, b, tool))
    d = Thread(target=decodeThread,args=(b, tool))
    s.start()
    r.start()
    d.start()
    r.join()

def receivingProcess_Test(binaryPath: str):
    '''
    测试读取数据进程功能
    :return:
    '''
    _dataChannel = shareStorage()
    s_socket, r_socket = socketpair()
    b = Barrier(2)
    s_thread = Thread(name='send binary thread', target=sendThread, args=(s_socket, binaryPath, b,0))
    i_thread = Thread(name='send order and print message thread', target=orderSimulate, args=(_dataChannel, b))
    r_thread = Thread(name='data receive thread', target=connectThread, args=(_dataChannel, r_socket))
    s_thread.start()
    i_thread.start()
    r_thread.start()
    s_thread.join()
    r_thread.join()
    print('receivingProcess_Test:', 'end')

def h5fileCanculate():
    pass

if __name__ == '__main__':
    receivingProcess_Test('testData/binaryData/nowData/20200930_1140-2109.dat')



