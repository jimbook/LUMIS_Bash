#__all__ = ['rawMaterial','production','goodsShelf']

class dataItem(object):
    '''
    是数据对象的基类
    '''
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

class dataEncapsulation(dataItem):
    '''
    数据封装类
    '''
    def __init__(self, name: str, content):
        super(dataEncapsulation, self).__init__(name)
        self._content = content

    @property
    def content(self):
        return self._content

class rawMaterial(dataEncapsulation):
    '''
    原始数据材料
    '''
    def __init__(self,name: str, content):
        super(rawMaterial, self).__init__(name=name ,content=content)

class production(dataEncapsulation):
    '''
    生产线输出的数据
    '''
    def __init__(self,name: str, content, mergeFunc = None):
        super(production, self).__init__(name=name, content=content)
        if (mergeFunc is not None) and (not callable(mergeFunc)):
            raise ValueError("argument(mergeFunc) should have __call__.")
        else:
            self._mergeFunc = mergeFunc

    def setMergeFunc(self,mergeFunc):
        if callable(mergeFunc):
            self._mergeFunc = mergeFunc
        else:
            raise ValueError("argument(mergeFunc) should have __call__.")

class dataMachine(dataItem):
    '''
    处理和保存数据的基类
    '''
    def __init__(self, name: str, handFunc):
        super(dataMachine, self).__init__(name)
        if callable(handFunc):
            self._handFunc = handFunc
        else:
            raise ValueError("argument(handFunc) should have __call__.")

    def handFunc(self, *args):
        return self._handFunc( *args)

class goodsShelf(dataMachine):
    '''
    存储和堆叠数据
    '''
    def __init__(self, name: str,handFunc, **kwargs):
        '''

        :param name:
        :param handFunc:
        :param kwargs:outputFunc
        '''
        super(goodsShelf, self).__init__(name,handFunc)
        self._content = None
        self._outputFunc = kwargs.get('outputFunc', lambda x: x)
        if not callable(self._outputFunc):
            raise ValueError("argument(outputFunc) should have __call__.")

    @property
    def content(self):
        return self._outputFunc(self._content)


    def putInTo(self, p: production):
        '''
        向货架中添加一个产品，对其进行堆叠
        :param p:
        :return:
        '''
        if self._content is None:
            self._content = p.content
        else:
            self._content = self.handFunc(self._content, p.content)

class productionLine(dataMachine):
    '''
    要处理输入的rawMaterial
    '''
    def __init__(self, name: str, ):

