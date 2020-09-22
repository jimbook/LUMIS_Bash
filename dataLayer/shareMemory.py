'''
    共享内存部分
'''
from multiprocessing.managers import BaseManager
from dataLayer.baseCore import shareStorage
from dataLayer.constantParameter import _address,_authkey

# ==========共享内存相关===========
class _Manager(BaseManager):   # 共享内存管理器
    pass

_Manager.register('get', shareStorage)

def getShare(server: bool) -> shareStorage:
    m = _Manager(address=_address, authkey=_authkey)
    if server:
        s = m.get_server()
        s.serve_forever()
    else:
        m.connect()
    return _Manager.get()




