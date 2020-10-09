from dataLayer import _Index
from dataLayer.baseCore import h5Data
import dataLayer
from dataLayer.calculationTools import *
import pandas as pd
import numpy as np
def markOneEvent(event: pd.DataFrame) -> int:
    '''
    对一个事件的数据打分
    :param event:
    ===========EVENT STRUCTURE======
    COLUMN include: chn00~chn35
    shape: (0~8, 36+)
    :return: score
    '''
    event = event[_Index[:36]]
    score = 100
    temp = np.arange(36)
    countIndex = (event != 0)
    for i in range(event.shape[0]):
        validIndex = temp[countIndex.iloc[i][:36]]
        count = validIndex.shape[0]
        if count == 1:
            score -= 3
            continue
        elif count == 0:
            score -= 5
            continue
        if validIndex[-1] - validIndex[0] + 1 == count:
            _unc = False
        else:
            _unc = True
        if count == 2:
            if _unc:
                score -= 4
        elif count == 3:
            score -= 3
            if _unc:
                score -= 3
        elif count == 4:
            score -= 5
            if _unc:
                score -= 4
        elif count > 4 and count < 9:
            score -= 10
        else:
            score -= 12
    return score

def workpiece(data_triggerIndex: pd.DataFrame):
    missOnly = np.zeros(8, dtype='int64')
    missMore = 0
    AllCatch = 0
    index = np.unique(data_triggerIndex.index.values)
    count = index.shape[0]
    step = 1
    for i in index:
        event = data_triggerIndex.loc[i]
        if event.shape[0] == 8:
            AllCatch += 1
        elif event.shape[0] == 7:
            for j in range(8):
                if j not in event[_Index[-1]].values:
                    missOnly[j] += 1
        else:
            missMore += 1
        print('\rrate of workpiece: {}/{}\t{}%'.format(step,count,step/count * 100), end='')
        step += 1
    print('')
    return missOnly, missMore, AllCatch

h = h5Data('data/2020_10_06/temp_0.h5', 'r')
d = h.getData(index=-2)
e = d.set_index(_Index[-2])
allCount = np.unique(e.index.values).shape[0]
print(allCount)
result = workpiece(e)
print('board\t\t{}'.format('\t'.join([str(x) for x in list(range(8))])))
print("missOnly\t{}".format('\t'.join([str(x) for x in list(result[0])])))
print('missMore:{}\nAllCatch:{}\n'.format(*result[1:]))
#d.to_csv('temp_csv_all.txt')






