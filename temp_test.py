# import time, threading
# import math
# import sys
# import clr
# sys.path.append(r'A:\工作\实验室\LUMIS\DAQ_IO\DAQ_IO\bin\Debug')
# clr.AddReference('DAQ_IO')
# clr.AddReference('System')
# from DAQ_IO_DLL import DAQ_IO,function_test
# from System import Decimal
# #file = open(".\\data\\temporary\\tem","w")
# #print("文件名：",file.name)
# #InData = Array[byte](0x00,0x00)
# #print(bytes([0x01,0x02]))
# #file.write()
# def equal(b1 : bytes,b2 : bytes):
#     if int.from_bytes(b1,byteorder='big',signed=False) == int.from_bytes(b1,byteorder='big',signed=False):
#         pass
# f = function_test()
# l = f.getfloat()
# print(type(f.getString()),f.getString())
# print(f.cmdstatus)
# # print(Decimal(0.2))
# # print(bytes(f.getcmd()))
# # print(str(b'\x02'))
# # print(bytes(f.getcmd()))
# # print(int.from_bytes(b'\x02',byteorder='big',signed=False))
# # if f.getcmd()[0] == b'\x19':
# #     print("-----------")
# # f = open(".\\data\\temporary\\cosmic_ray_test.dat", "rb")
# # b = f.read(14)
# # for i in b:
# #     print(i.to_bytes(length=1,byteorder='big',signed=False))

#######
'''作业'''
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
# def R_theta(theta,R,A_2,A_4):
#     P_2 = A_2*(1/2*(3*np.cos(theta)**2-1))
#     P_4 = A_4*(1/8*(35*np.cos(theta)**8-30*np.cos(theta)**2)+3)
#     return R*(1+P_2+P_4)
# def AngleToPi(angle):
#     return angle/180*np.pi
# Angle_number = np.array([90,116.6,129.2,135.0,140.8,153.4,180.0])
# Angle_PI = AngleToPi(Angle_number)
# CorrectedCoinRate = np.array([1.255,1.238,1.317,1.320,1.302,1.337,1.411])
# popt,pcov = curve_fit(R_theta,Angle_PI,CorrectedCoinRate)
# popt_1,pcov_1 = curve_fit(R_theta,Angle_PI,CorrectedCoinRate,bounds=([0,0.1,0.009],[5.,0.1020,0.0091]))
# plt.plot(Angle_number,CorrectedCoinRate,'r-',label="source data")
# plt.plot(Angle_number,R_theta(Angle_PI,*popt),'b--',label='fit: R=%5.3f,A2=%5.3f,A4=%5.3f' % tuple(popt))
# plt.plot(Angle_number,R_theta(Angle_PI,1.25,0.1020,0.0091),'g--',
#          label='just fit R: R=%5.3f,A2=%5.3f,A4=%5.3f' % tuple([1.25,0.1020,0.0091]))
# plt.xlabel("θ")
# plt.ylabel("R(θ)")
# plt.legend()
# plt.show()

import time
def USB_wait(flag : dict):
    i = 0
    point = ""
    while not flag["checkUSB"]:
        if i <=6:
            point += "·"
            i += 1
        else:
            point = ""
            i = 0
        print("\rWaiting for equipment to come online {0}".format(point),end='')
        time.sleep(0.4)

def HV_wait(flag : dict):
    i = 0
    j = 0
    point_1 = ["▁","▂","▃","▄","▅","▆","▇","█"]
    point_0 = ["▏","▎","▍","▌","▋","▊","▉","█"]
    while not flag["HVmove"]:
        print("\rWaiting for regulating voltag {0} {1}%".format("█"*j+point_0[i],j*len(point_0)+i),end='')
        if i < len(point_0)-1:
            i += 1
        else:
            i = 0
            j += 1
        time.sleep(0.4)
def SC_wait(flag : dict):
    '''

    :param flag: flgg["SC"] True表示未处于等待状态，Flase表示处于等待状态
    :return:
    '''
    i = 0
    point = ["░", "▒", "▓", "█", "▓", "▒", "░", " "]
    while not flag["SC"]:
        print("\rWaiting for setting slow control {0}".format(point[i]),end='')
        if i < len(point)-1:
            i += 1
        else:
            i = 0
        time.sleep(0.2)

SC_wait({"SC":False})





