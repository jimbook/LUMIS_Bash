from multiprocessing import Process
import os,threading
import multiprocessing as mp
import time
import logging,collections,re

#等待USB连接
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
    print("\rWaiting for equipment to come online {0}".format(point))

#等待高压调节
def HV_wait(flag : dict):
    i = 0
    point_0 = ["▁","▂","▃","▄","▅","▆","▇","█"]
    while not flag["HVmove"]:
        print("\rWaiting for regulating voltag {0}".format(point_0[i]),end='')
        if i < len(point_0)-1:
            i += 1
        else:
            i = 0
        time.sleep(0.4)
    print("\rWaiting for regulating voltag {0}".format(point_0[-1]))

#等待slowControl设置
def SC_wait(flag : dict):
    '''

    :param flag: flgg["SC"] True表示未处于等待状态，Flase表示处于等待状态
    :return:
    '''
    i = 0
    point = ["░","▒","▓","█","▓","▒","░"," "]
    while not flag["SC"]:
        print("\rWaiting for setting slow control {0}".format(point[i]),end='')
        if i < len(point)-1:
            i += 1
        else:
            i = 0
        time.sleep(0.2)

#等待自动调节
def Auto_wait(flag : dict):
    '''
    :param flag: flag["Auto"] -1表示未处于等待状态，0~3表示处于自动配置的步骤数
    :return:
    '''
    i = 0
    j = 0
    point_0 = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    taskName = ["<set slow control configuration>","<set probe configuration>","<turn on high voltag module>","<receive data>",]
    while flag["Auto"] >= 0:
        if flag["Auto"] !=4:
            print("\rTask:{0} is in progress. {1} {2}%".format(taskName[flag["Auto"]],"█" * j + point_0[i], j * len(point_0) + i), end='')
        else:
            print("\rWaiting for the automatic configuration process to end. {0} {1}% {2}".format("█" * j + point_0[i], j * len(point_0) + i,flag["Auto"]), end='')
        if i < len(point_0) - 1:
            i += 1
        else:
            i = 0
            j += 1
        while (flag["Auto"] == 0 and j*len(point_0)+i == 40) | (flag["Auto"] == 1 and j*len(point_0)+i == 80) | \
                (flag["Auto"] == 2 and j*len(point_0)+i == 90) | (flag["Auto"] == 3 and j*len(point_0)+i == 99):
            time.sleep(0.5)
        if (flag["Auto"] == 1 and j*len(point_0)+i <= 40) | (flag["Auto"] == 2 and j*len(point_0)+i <= 80) | \
                (flag["Auto"] == 3 and j*len(point_0)+i <= 90) | (flag["Auto"] == 4 and j*len(point_0)+i <= 100):
            time.sleep(0.1)
        else:
            time.sleep(0.4)
        if j*len(point_0)+i == 100:
            flag["Auto"] = -1
        elif flag["Auto"] == 4 and j*len(point_0)+i == 99:
            flag["Auto"] = -1
    print("\rWaiting for the automatic configuration process to end. {0} {1}%".format("█" * (j + 1),100), end='')

