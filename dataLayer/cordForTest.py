'''
暂时没什么用
'''
# 测试时数据时用于替换socket对象
class dataIO(object):
    def __init__(self):
        BinaryPath = ''
        self.file = open(BinaryPath,'r+')

    def settimeout(self,time):
        pass

    def connect(self,*args):
        pass

    def send(self,*args):
        pass

    def recv(self,maxSize: int):
        return self.file.read(maxSize)

    def close(self):
        self.file.close()


