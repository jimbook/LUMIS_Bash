import re
import os
# for root,dirs,files in os.walk('C:\\Users\\jimbook\\Desktop\\缪子\\test_SP2E_USTC'):
#     for file in files:
#         r = re.match(r'^Test_SP2E_BGA_FRA 703-\d+.data$',file)
#         if r is not None:
#             with open(os.path.join(root,file),'r') as f:
#                 readBuff = f.read()
#             with open(os.path.join('dependence/chipAbout/CalibrationData', file), 'w') as f:
#                 f.write(readBuff)
#             print(file)
# def
# with open('dependence/chipAbout/chipID_ex.txt') as file:
#     buff = file.readlines(63)
#     print(buff)
#     s = buff[0]
#     s = s.strip()
#     print(s)
#     s = s.split()
#     print(s)
# import pandas as pd
# import numpy as np
# from io import StringIO
# from scipy.optimize import curve_fit
# def voltageFunc(x,a,b):
#     return a * x + b
# with open('dependence/chipAbout/CalibrationData/Test_SP2E_BGA_FRA 703-1290.data') as file:
#     _lines = file.readlines()
#     t = _lines[52]
#     print(t)
#     _i = [' ']
#     _i.extend(np.arange(36).astype(np.str).tolist())
#     indexLine = '\t'.join(_i)
#     indexLine += '\n'
#     dataLines = [indexLine]
#     dataLines.extend(_lines[53:63])
#     source = ''.join(dataLines).replace(',','.')
#     print(source)
#     with StringIO(source) as f:
#         dataFrame = pd.read_csv(f, header=0,sep='\t',index_col=0)
#     print(dataFrame)
#     y = dataFrame.index.values
#     x = dataFrame.iloc[:,0].values
#     popt, pcov = curve_fit(voltageFunc,x,y)
#     print(popt)
#     import matplotlib.pyplot as mpl
# mpl.plot(x,y,'bo',label='source')
# mpl.plot(x,voltageFunc(x,*popt),'r--',label='fit')
# mpl.legend()
# mpl.grid()
# mpl.show()
import asyncio
async def getData():
    with open(r'C:\Users\jimbook\Desktop\LUMIS_Bash-GUI_ON_NET-separation\data\mydata.txt') as file:
        buff = file.read()
        return buff[:5]


async def factorial(name, number):
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({i})...")
        m = await asyncio.sleep(1)
        print(m)
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")

async def main():
    # Schedule three calls *concurrently*:
    await asyncio.gather(
        factorial("A", 2),
        factorial("B", 3),
        factorial("C", 4),
    )

asyncio.run(main())


