'''
用于存储数据：
    接收数据逻辑：根据产品名进行堆叠
    存储数据变量
    输出数据逻辑
'''
from .dataItem import production,goodsShelf

class dataStorage(object):
    def __init__(self):
        self._storage = {}

    def newGoodsShelf(self,name: str, mergeFunc):
        if name in self._storage:
            raise ValueError("name({}) has already existed!".format(name))
        _g = goodsShelf(name=name,mergeFunc=mergeFunc)
        self._storage[name] = _g

    def pushProduction(self, _p: production):
        if _p.name in self._storage:
            if self._storage[_p.name].contect is not None:
                pass
