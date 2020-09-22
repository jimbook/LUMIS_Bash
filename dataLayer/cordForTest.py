import asyncio
from dataLayer.connectionTools import Lumis_Decode
from multiprocessing import Event
from socket import socket
from dataLayer.connectionTools import loadDataFromSocket,dataDecode,sendStatusMessage
import threading
from dataLayer.baseCore import shareStorage
async def dataReceiveThread_Test(share: shareStorage, s: socket):
    pipe_r = share.orderPipe(False)
    decodeTool = Lumis_Decode()
    messageQueue = share.messageQueue()
    tag_receive = Event()
    tag_message = Event()
    while True:
        await asyncio.sleep(0.5)
        if pipe_r.poll():
            order = pipe_r.recv()
            if isinstance(order,str) or order == 1:
                if share.dataTag().is_set():
                    messageQueue.put((2, 'the receiving data module is running.'))
                    continue
                share.dataTag().set()
                decodeTool.reInitialize()
                # 添加数据接收协程
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
import numpy as np
import pandas as pd
import time
from datetime import datetime
import h5py
from dataLayer.constantParameter import _Index



