import time
import datetime
import pandas as pd
import dataLayer
from dataLayer.baseCore import h5Data
import h5py

__all__ = ["idxCount","timeCount"]
# 辅助函数：打印loop
class idxCount(object):
    def __init__(self,allCount: int):
        self.allCount = allCount
        self.nowCount = 0

    def printNowCount(self):
        if self.nowCount == 0:
            self.start = time.time()
            usedTime = 0
            progress = self.nowCount / self.allCount
            print("\r{}/{}--{:.2%}--used time:{}--estimate using time:{}".format(
                self.nowCount, self.allCount, progress, datetime.timedelta(seconds=usedTime),
                "??:??:??"), end=''
            )
        else:
            usedTime = time.time() - self.start
            progress = self.nowCount/self.allCount
            print("\r{}/{}--{:.2%}--used time:{}--estimate using time:{}".format(
                self.nowCount,self.allCount,progress,datetime.timedelta(seconds=usedTime),
                datetime.timedelta(seconds=usedTime/progress)),end=''
                )
        self.nowCount += 1

    def __del__(self):
        print('')

# 辅助函数：打印函数运行时间
def timeCount(function):
   def wrapper(*args, **kwargs):
        time_start = time.time()
        res = function(*args, **kwargs)
        cost_time = time.time() - time_start
        print("function:{},running time:{}".format(function.__name__,datetime.timedelta(seconds=cost_time)))
        return res
   return wrapper

# 辅助函数：修正dataSet未正确划分的错误
def getCorrectedIndex(data: pd.DataFrame):
    index = data[dataLayer._Index[-2]]
    index_0 = index[:-1].reset_index()
    index_1 = index[1:].reset_index()
    index_diff = index_0 - index_1
    result = index_diff.loc[index_diff["triggerID"].values > 0].loc[:, "triggerID"]
    return result.index.values + 1


def correctDataSetSlice(h5Path: str):
    data = h5Data(h5Path, 'r')
    corrected = getCorrectedIndex(data.getData(-1))
    print(corrected)
    data.close()
    file = h5py.File(h5Path, mode="r+")
    dataGroup = file['dataGroup']
    index = dataGroup['index']
    index.resize(corrected.shape[0] + 1, axis=0)
    index[1:] = corrected
    file.close()
