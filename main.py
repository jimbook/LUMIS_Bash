import sys
import clr
sys.path.append(r'A:\工作\实验室\LUMIS\DAQ_IO\DAQ_IO\bin\Debug')
clr.AddReference('DAQ_IO')
from DAQ_IO_DLL import function_test
# f = function_test()
# b = f.getcmd()
# print(type(b),"\n",b[1])
# print(bytes([b[0],b[1]]))
# f.setcmd(0xF866,2)
# c = f.getcmd()
# print(bytes([c[0],c[1]]),c[0])
# print(f.check_USB(0x1006,0x258a))
