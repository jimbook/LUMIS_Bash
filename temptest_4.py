from multiprocessing import Pool,Manager
import pandas as pd
from io import StringIO
import functools
from dataLayer.baseCore import h5Data
# DataFrame迭代器
def fileGenerator(dataSource,size: int = 5000) -> pd.DataFrame:
    if isinstance(dataSource,str):
        with open(dataSource,'r') as file:
            index = file.readline()
            buff = []
            buff.append(index)
            while True:
                line = file.readline()
                if line == '':
                    data = ''.join(buff)
                    yield pd.read_csv(StringIO(data))
                    break
                buff.append(line)
                if len(buff) > size:
                    data = ''.join(buff)
                    yield pd.read_csv(StringIO(data))
                    del data
                    buff.clear()
                    buff.append(index)
    elif isinstance(dataSource, pd.DataFrame):
        index = 0
        while True:
            if index+size < dataSource.shape[0]:
                yield dataSource.iloc[index:index+5000]
                index += size
            else:
                yield dataSource.iloc[index:]
                break
    elif isinstance(dataSource,h5Data):
        for i in range(dataSource.index.shape[0]):
            yield dataSource.getData(i)

# 用于计算大文件的计算函数，主要对外调用此函数来计算
def caculation(func1,func2,dataPath:str):
    '''
    :param func1: 一个函数，允许输入一个DataFrame参数，返回一个计算结果为类型A
    :param func2:一个函数，对计算结果进行合并，输入两个参数，类型均为A
    :param dataPath:大文件CSV路径
    :return:对大文件的计算结果
    '''
    _pool = Pool(4)
    sourceData = fileGenerator(dataPath)
    _queue = Manager().Queue()
    def _merge(result):
        _r = functools.reduce(func2,result)
        _queue.put(_r)
    _pool.map_async(func1,sourceData,1,_merge)
    _pool.close()
    _pool.join()
    _r = _queue.get()
    return _r

# 模块测试用，请不要随意调用
# func1 实例
def getSpecturm(data: pd.DataFrame):
    _l = data.iloc[:,2].values
    return _l.sum()

# func2 示例
def merge(x,y):
    return x+y

if __name__ == '__main__':
    # 示例：会将csv中第三行的数据全部加起来，返回和
    print(caculation(getSpecturm,merge,'161202_tempData.txt'))
