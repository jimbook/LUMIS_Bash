import time
import datetime

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