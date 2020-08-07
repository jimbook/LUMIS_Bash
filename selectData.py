import os

import pandas as pd
import numpy as np
from collections import Counter
from dataAnalyse import chnList,typeList,SCAinfoList
# 将元数据中被触发的数据筛选出来
def selectHit(data: pd.DataFrame) -> pd.DataFrame:
    d1 = data.T
    d2 = d1.swaplevel()
    d3 = d2.sort_index(level=0)
    data_values = d3.loc[typeList[2]]
    data_hit = d3.loc[typeList[1]]
    data_info = d1.loc[chnList[-1]]
    d4 = data_values.mul(data_hit).append(data_info)
    return d4.T#.set_index("triggerID")
data = pd.read_csv(".\\data\\2020_08_06\\lead.txt",index_col=0,header=[0,1])

# 将数据按每一组triggerID进行切片
def slice_triggerID(data: pd.DataFrame,DirPath: str):
    t1 = data[chnList[-1]]["triggerID"].values[:-1]
    t2 = data[chnList[-1]]["triggerID"].values[1:]
    t3 = np.append(False,t1-t2 >= 1000)
    index = data.index.values[t3]
    print(index)
    i = 0
    start = 0
    for end in index:
        d1 = data.loc[start:end-1].reset_index()
        start = end
        d1.to_csv(os.path.join(DirPath,"lead_{}.txt".format(i)))
        i += 1
        print(d1)
    d1 = data.loc[start:]
    d1.to_csv(os.path.join(DirPath, "lead_{}.txt".format(i)))
    return True
# slice_triggerID(data,DirPath=".\\data\\tempStorage")
# 获取各个通道的基线
# def get_baseLine(data: pd.DataFrame0):
#     pass

out = []
for i in chnList[:32]:
    l = data[i][typeList[-1]]
    index = (data[i][typeList[-2]] == 0)&(data[chnList[-1]][SCAinfoList[-1]] == 2)
    c = l.values[index]
    print(c)