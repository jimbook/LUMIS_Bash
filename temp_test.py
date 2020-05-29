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
#
# import time
# def USB_wait(flag : dict):
#     i = 0
#     point = ""
#     while not flag["checkUSB"]:
#         if i <=6:
#             point += "·"
#             i += 1
#         else:
#             point = ""
#             i = 0
#         print("\rWaiting for equipment to come online {0}".format(point),end='')
#         time.sleep(0.4)
#
# def HV_wait(flag : dict):
#     i = 0
#     j = 0
#     point_1 = ["▁","▂","▃","▄","▅","▆","▇","█"]
#     point_0 = ["▏","▎","▍","▌","▋","▊","▉","█"]
#     while not flag["HVmove"]:
#         print("\rWaiting for regulating voltag {0} {1}%".format("█"*j+point_0[i],j*len(point_0)+i),end='')
#         if i < len(point_0)-1:
#             i += 1
#         else:
#             i = 0
#             j += 1
#         time.sleep(0.4)
# def SC_wait(flag : dict):
#     '''
#
#     :param flag: flgg["SC"] True表示未处于等待状态，Flase表示处于等待状态
#     :return:
#     '''
#     i = 0
#     point = ["░", "▒", "▓", "█", "▓", "▒", "░", " "]
#     while not flag["SC"]:
#         print("\rWaiting for setting slow control {0}".format(point[i]),end='')
#         if i < len(point)-1:
#             i += 1
#         else:
#             i = 0
#         time.sleep(0.2)


# # 导入socket库:
# import socket
#
# # 创建一个socket:
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # 建立连接:
# s.connect(('www.sina.com.cn', 80))
# # 发送数据:
# s.send(b'GET / HTTP/1.1\r\nHost: www.sina.com.cn\r\nConnection: close\r\n\r\n')
# # 接收数据:
# buffer = []
# while True:
#     # 每次最多接收1k字节:
#     d = s.recv(1024)
#     if d:
#         buffer.append(d)
#     else:
#         break
# data = b''.join(buffer)
# # 关闭连接:
# s.close()
# header, html = data.split(b'\r\n\r\n', 1)
# print(header.decode('utf-8'))
# from xml.parsers.expat import ParserCreate
#
# class DefaultSaxHandler(object):
#     def start_element(self, name, attrs):
#         print('sax:start_element: %s, attrs: %s' % (name, str(attrs)))
#
#     def end_element(self, name):
#         print('sax:end_element: %s' % name)
#
#     def char_data(self, text):
#         print('sax:char_data: %s' % text)
#
# xml = r'''<?xml version="1.0"?>
# <ol>
#     <li><a href="/python">Python</a></li>
#     <li><a href="/ruby">Ruby</a></li>
# </ol>
# '''
#
# handler = DefaultSaxHandler()
# parser = ParserCreate()
# parser.StartElementHandler = handler.start_element
# parser.EndElementHandler = handler.end_element
# parser.CharacterDataHandler = handler.char_data
# parser.Parse(xml)
# import xml.etree.ElementTree as ET
# a = ET.Element('a') #新建元素
# b = ET.SubElement(a, 'b')#创建子元素
# b.text = "lol"
# c = ET.SubElement(a, 'c')
# d = ET.SubElement(c, 'd')
# print(ET.tostring(b,encoding="unicode"))
# try:
#     import  socket,time
#     s = socket.socket(type=socket.SOCK_DGRAM)
#
#     host = '127.0.0.1'
#     port = 2000
#     address = (host,port)
#     s.bind((host,port+1))
#     for i in range(10):
#         s.sendto('Good luck!'.encode("utf-8"),address)
#         time.sleep(1)
#         print(s.recvfrom(1024))
#
#     #print(s.recvfrom(1024))
#     s.close()
# except BaseException as e:
#     print(e)
import numpy as np
i = np.array(range(10))
print(i)
print(i[0:5])
for j in range(10)[0:5]:
    print(j)