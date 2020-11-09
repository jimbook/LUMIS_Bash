import numpy as np
import pandas as pd
import dataLayer
from dataLayer.baseCore import *
import os

# 处理缪子事件的类
class Moun_(object):
    '''
    缪子事件处理流：
        1.检查是否有八层数据——是：继续；否：丢弃
        替换坏道
        2.用平均值法均一化，卡阈值，减去基线（低于基线的置零）
        3.检查每层的触发情况（要求1~2个bar触发，两个bar触发时必须相邻）--是：继续；否：丢弃
        4.计算各层的触发位置
        5.通过触发位置计算poca点
        6.讲poca点数据输出到tmpStorage中
        7.当数据量足够时，通过比例算法计数
    '''

    def __init__(self):
        '''
        导入阈值、基线、均一化数据
        '''
        self.baseline = pd.read_csv("./tmpStorage/bl.csv",index_col=0, header=0)
        self.threshold = pd.read_csv("./tmpStorage/tr.csv",index_col=0, header=0)

    @staticmethod
    def checkEvent(event: pd.DataFrame) -> bool:
        '''
        判断事件是否可用
        判断标准：1.有八层的数据
                2.每层
     :param event:
        :return:
        '''

