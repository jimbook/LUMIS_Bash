'''
    共享内存部分
'''
from multiprocessing.managers import BaseManager
from multiprocessing import Queue, Event, Pipe
from dataLayer.baseCore import shareStorage,filePath
from dataLayer import _address,_authkey

# ==========共享内存相关===========
class myManager(BaseManager):   # 共享内存管理器
    pass
myManager.register('get', shareStorage)
e_data = Event()
e_process = Event()
q = Queue()
pipe = Pipe(True)
print(pipe)
path = filePath()
myManager.register('dataTag',callable=lambda:e_data)
myManager.register('processTag', callable=lambda :e_process)
myManager.register('messageQueue', callable=lambda :q)
myManager.register('filePath', callable=lambda :path)
myManager.register('orderPipe_r', callable=lambda :pipe[0])
myManager.register('orderPipe_s', callable=lambda :pipe[1])

def getShare(server: bool) -> shareStorage:
    if server:
        m = myManager(address=_address, authkey=_authkey)
        s = m.get_server()
        s.serve_forever()
    else:
        m = myManager(address=_address, authkey=_authkey)
        m.connect()
        s = shareStorage(dataTag=m.dataTag(), processTag=m.processTag(), messageQueue=m.messageQueue(), filePath=m.filePath(), orderPipe=(m.orderPipe_r(),m.orderPipe_s()))
        return s

if __name__ == '__main__':
    import time
    from multiprocessing import Process
    p1 = Process(target=getShare, args=(True,))
    p1.start()
    print('server is start.')
    time.sleep(1)
    Share = getShare(False)
    Share.orderPipe(True).send('6')
    Share.messageQueue().put('12')
    print(Share.messageQueue().get())
    print(Share.processTag().is_set())
    print(Share.getFilePath(),type(Share.getFilePath()))
    Share.setFilePath('link')
    print(Share.getFilePath(),type(Share.getFilePath()))




