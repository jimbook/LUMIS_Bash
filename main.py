from multiprocessing import Process
import os
import multiprocessing as mp
import time
from terminal  import terminal,communication
cmdDict = {
""
}
from DAQ_IO_dll import USB_Manager
def communication(IN : mp.Queue,OUT : mp.Queue):
    equipment = USB_Manager()#重构库类，用于与设备通讯
    while True:
        signal = IN.get()
        if signal.get("cmd",None) == "checkUSB":
            '''
            搜索USB端口。
            接收：
            cmd是命令名，可选参数timeout等待时间，
            timeout默认为-1，表示没有超时限制。
            操作：
            调用重构库中的搜索USB函数，搜索时阻塞
            返回：
            连接成功则返回true，
            超时则返回False，同时返回超时标签
            搜索出错返回False，同时返回错误标签,错误标签包含错误信息
            '''
            try:
                reply = equipment.searchUSB(signal.get("timeout",signal.get("timeout",-1)))
                if reply:
                    OUT.put({"return": True})
                else:
                    OUT.put({"return": False, "tag": ["timeout"], "timeout": True})
            except BaseException as e:
                OUT.put({"return":False,"tag":["Error"],"Error":e})
        elif signal.get("cmd",None) == "AutoAll":
            '''
            自动配置+开启高压+开启数据读取
            接收：
            cmd是命令名，没有可选参数
            操作：
            配置slowControl默认配置
            配置probe默认配置
            打开高压，电压为默认值50V
            打开数据读取线程
            最后返回
            返回：
            每一步返回一次数据，返回Turn和当前操作标签，开启数据接收操作会增加文件路径标签
            出错返回False，同时返回错误标签,错误标签包含错误信息
            '''
            try:
                if equipment.USBstatus:
                    equipment.slowControl_config()
                    OUT.put({"return":True,"tag":["step"],"step":1})
                    equipment.probe_config()
                    OUT.put({"return":True,"tag":["step"],"step":2})
                    equipment.hv_switch(True)
                    OUT.put({"return":True,"tag":["step"],"step":3})
                    dataPath = equipment.DataAcceptThread()
                    OUT.put({"return":True,"tag":["step","dataPath"],"step":4,"dataPath":dataPath})
                else:
                    OUT.put({"return":False,"tag":["INFO"],"INFO":"USB is not connected!Please connect USB device again."})
            except BaseException as e:
                OUT.put({"return":False,"tag":["Error"],"Error":e})
        elif signal.get("cmd",None) == "setSlowControl":
            '''
            更改配置到仪器中
            接收：
            cmd是命令名
            额外参数是：change-一个parameter(namedtuple)的list，parameter包含index（更改的参数名称）和value（值）
            操作：
            首先检查设备连接，未连接返回False和INFO标签
            依次更改软件中的配置，
            然后将配置命令发送给仪器
            返回：
            返回True，和意外描述标签，描述未配置成功的参数情况
            出现异常则返回False，返回异常信息。
            '''
            try:
                if equipment.USBstatus:
                    accident = []
                    for i in range.get("change",[]):
                        a = equipment.slowControl_set(i.index,i.value)
                        if not a:
                            if i.index in equipment.slowControlLengthDict.keys():
                                if i.value >= 0 and i.value < 2 ** equipment.slowControlLengthDict.get(i.index):
                                    accident.append("{0} : the parameter configuration failed for unknown reason.".format(i.index))
                                else:
                                    accident.append("{0} : the parameter configuration failed for improper value.".format(i.index))
                            else:
                                accident.append("{0} : the parameter configuration failed for wrong parameter name.".format(i.index))
                    equipment.slowControl_config()
                    OUT.put({"return":True,"tag":["ExceptDescription"],"ExceptDescription":accident})
                    del a
                    del accident
                else:
                    OUT.put({"return":False,"tag":["INFO"],"INFO":"USB is not connected!Please connect USB device again."})
            except BaseException as e:
                OUT.put({"return": False, "tag": ["Error"], "Error": e})
        elif signal.get("cmd",None) == "setHV":
            '''
            设置高压，平滑改变电压
            接收：
            cmd命令名称
            voltag目标电压
            操作：
            调用重构函数平滑调节电压，未开启高压模块会自动开启高压模块
            返回：
            返回True
            出现异常则返回False，返回异常信息。
            '''
            try:
                equipment.hv_smoothTurnOn(signal.get("voltag"))
                OUT.put({"return":True})
            except BaseException as e:
                OUT.put({"return": False, "tag": ["Error"], "Error": e})
        elif signal.get("cmd",None) == "switchHV":
            '''
            接收：
            cmd是命令名
            turnOn是开启/关闭高压模块
            操作+返回：
            开启高压模块-检查高压模块开启标志，开启则直接返回True，同时返回INFO标签
            未开启则发送开启高压模块命令，返回True
            关闭高压模块-检查高压模块标志，已经关闭则直接返回True，同时返回INFO标签
            未关闭，检查当前电压，通过平滑调节高压将电压降到合适值再发送关闭高压模块命令，返回True
            '''
            try:
                if signal.get("turnOn"):
                    if equipment.HVstatus:
                        OUT.put({"return":True,"tag":["INFO"],"INFO":"High Voltag module has turned on."})
                    else:
                        equipment.hv_switch(True)
                        OUT.put({"return":True})
                else:
                    if equipment.HVstatus:
                        if equipment.currentHV >= 41:
                            equipment.hv_smoothTurnOn(41)
                        equipment.hv_switch(False)
                        OUT.put({"return":True})
                    else:
                        OUT.put({"return": True, "tag": ["INFO"], "INFO": "High Voltag module has turned off."})
            except BaseException as e:
                OUT.put({"return": False, "tag": ["Error"], "Error": e})
        elif signal.get("cmd",None) == "startAcceptData":
            try:
                dataPath = equipment.DataAcceptThread()
                OUT.put({"return":True,"tag":["dataPath"],"dataPath":dataPath})
            except BaseException as e:
                OUT.put({"return": False, "tag": ["Error"], "Error": e})
            OUT.put({"return": True, "tag": ["step", "dataPath"], "step": "accept data", "dataPath": dataPath})
        elif signal.get("cmd") == "stopAcceptData":
            try:
                if equipment.DataAcceptStatus:
                    equipment.StopDataAccept()
                    OUT.put({"return":True})
                else:
                    OUT.put({"return":True,"tag":["INFO"],"INFO":"Data reception thread was not opened."})
            except BaseException as e:
                OUT.put({"return":False,"tag":["Error"],"Error":e})
        elif signal.get("cmd",None) == "exit":
            try:
                if equipment.DataAcceptStatus:
                    equipment.StopDataAccept()
                break
            except BaseException as e:
                OUT.put({"return": False, "tag": ["Error"], "Error": e})
    OUT.put({"return":True})



if __name__ == '__main__':
    mp.set_start_method('spawn')
    print("")
    q = mp.Queue()
    p_IO = mp.Process(target=communication, args=(q,))
    p_IO.start()
    terminal(q)