import pandas as pd
import os
_data = pd.read_csv('bl.csv', index_col=0, header=0)
for bid in range(8):
    if bid == 0:
        _data.iloc[bid, 9] = _data.iloc[bid, 32]
    elif bid == 1:
        _data.iloc[bid, 21] = _data.iloc[bid, 32]
    elif bid == 2:
        _data.iloc[bid, 11] = _data.iloc[bid, 32]
_data.to_csv('bl.csv')
_data = pd.read_csv('tr.csv', index_col=0, header=0)
for bid in range(8):
    if bid == 0:
        _data.iloc[bid, 9] = _data.iloc[bid, 32]
    elif bid == 1:
        _data.iloc[bid, 21] = _data.iloc[bid, 32]
    elif bid == 2:
        _data.iloc[bid, 11] = _data.iloc[bid, 32]
_data.to_csv('tr.csv')
_data = pd.read_csv('mean_scale.csv', index_col=0, header=0)
for bid in range(8):
    if bid == 0:
        _data.iloc[bid, 9] = _data.iloc[bid, 32]
    elif bid == 1:
        _data.iloc[bid, 21] = _data.iloc[bid, 32]
    elif bid == 2:
        _data.iloc[bid, 11] = _data.iloc[bid, 32]
_data.to_csv('mean_scale.csv')
_data = pd.read_csv('geometrySystem.csv', index_col=0, header=0)
offset = [-2.02264937
        ,-0.789919915
        ,1.223523393
        ,1.296914005
        ,0.556464601
        ,-0.417131352
        ,0.242661376
        ,-0.089862738]
for bid in range(8):
    _data.iloc[bid,bid%2] += offset[bid]
_data.to_csv('geometrySystem.csv')
