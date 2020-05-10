from multiprocessing import Process
import os,threading
import multiprocessing as mp
import time
import logging,collections,re
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
                    OUT.put({"return":True,"tag":["step"],"step":"slow control"})
                    equipment.probe_config()
                    OUT.put({"return":True,"tag":["step"],"step":"probe config"})
                    equipment.hv_switch(True)
                    OUT.put({"return":True,"tag":["step"],"step":"high voltag turn on"})
                    dataPath = equipment.DataAcceptThread()
                    OUT.put({"return":True,"tag":["step","dataPath"],"step":"accept data","dataPath":dataPath})
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
                    for i in range.get("change",None):
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
        elif signal.get("cmd",None) == "exit":
            break
    OUT.put({"return":True})
#测试用通讯函数
def communication_test(IN : mp.Queue,OUT : mp.Queue):
    while True:
        command = IN.get()
        if command == "checkUSB":
            time.sleep(6)
            OUT.put({"checkUSB":True})
        elif command == "USBstatus":
            OUT.put({"USBstatus":True})
        elif command == "exit":
            OUT.put({"exit":True})
            break
        elif command.get("cmd") == "ChangeSlowControl":
            for i in command.get("change"):
                print(i.index,i.value)

parameter = collections.namedtuple('parameter',['index','value'])
#终端输入和分发命令
def terminal(IN : mp.Queue,OUT : mp.Queue):
    # 操作：连接USB在开启程序时进行搜索；
    # terminal：显示正在搜索；直到成功连接到usb接口terminal显示
    flag = {"checkUSB":False,"HVmove":True,"Auto":-1}#等待标志，checkUSB是等待设备上线标志，HVmove是等待电压调节标志,Auto是自动调节步骤标志，True表示未在等待,
    OUT.put({"cmd":"checkUSB","timeout":300})#send command oder to communication proess.
    t1 = threading.Thread(target=USB_wait,args=(flag,))#this thread aims for printing waiting information.
    t1.start()
    time.sleep(2)
    reply = IN.get()#获取通讯进程返回的信息，未返回时阻塞
    flag["checkUSB"] = True#结束打印等待信息
    t1.join()
    if reply["return"]:#如果搜索成功
        print("\nDevice ready。")
    else:
        print("\ntimeout:Device not found,please check the USB port.")
    while True:
        time.sleep(0.5)
        command = input(">>>").strip().split()
        if command[0] == "quit" or command == "exit":#退出程序
            OUT.put({"cmd":"exit"})
            reply = IN.get()
            if reply.get("return",False):
                break
            else:
                print("DAQ communication server refuses to stop")
        elif command[0] == "reconnect":     #重新连接USB
            flag["checkUSB"] = False
            OUT.put({"cmd": "checkUSB", "timeout": 300})  # send command oder to communication proess.
            t1 = threading.Thread(target=USB_wait, args=(flag,))  # this thread aims for printing waiting information.
            t1.start()
            time.sleep(2)
            reply = IN.get()  # 获取通讯进程返回的信息，未返回时阻塞
            flag["checkUSB"] = True  # 结束打印等待信息
            t1.join()
            if reply["return"]:  # 如果搜索成功
                print("\nDevice ready.")
            else:
                if "timeout" in reply.get("tag",None):
                    print("\ntimeout:Device not found,please check the USB port.")
                elif "Error" in reply.get("tag",None):
                    print("Error :",reply.get("Error"))
        elif command[0] == "auto":
            OUT.put({"cmd":"AutoAll"})
            flag["Auto"] = 0
            t1 = threading.Thread(target=Auto_wait, args=(flag,))  # this thread aims for printing waiting information.
            t1.start()
            while flag["Auto"] >=0:
                reply = IN.get()
                if reply["return"]:
                    flag["Auto"] = reply["step"]
                    if reply["step"] == 4:
                        dataPath = reply["dataPath"]
                else:
                    break
            t1.join()
            print("Data is stored to {0}".format(dataPath))
        elif command[0] == "HV":
            if len(command) == 2:
                if command[1].lower() == "-o" or command[1].lower() == "-open":
                    OUT.put({"cmd":"switchHV","turnOn":True})
                elif command[1].lower() == "-c" or command[1].lower() == "-close":
                    OUT.put({"cmd":"switchHV","turnOn":False})
                elif command[1].lower() == "-s" or command[1].lower() == "-set":
                    x = ""
                    for i in command:
                        x += i
                    print("Oder \'{0}\' need more arguments".format(x))
                    del x
                    continue
                else:
                    x = ""
                    for i in command:
                        x += i
                    print("There is no such order: \'{0}\'".format(x))
                    del x
                    continue
            if len(command) == 3:
                if command[1].lower() == "-s" or command[1].lower() == "-set":
                    if re.match("^\d*$",command[2]):
                        OUT.put({"cmd":"setHV","voltag": int(command[2])})
                    else:
                        print("target voltag must be an integer.")
                        continue
                else:
                    x = ""
                    for i in command:
                        x += i
                    print("There is no such order: \'{0}\'".format(x))
                    del x
                    continue
            flag["HVmove"] = False
            t1 = threading.Thread(target=HV_wait, args=(flag,))  # this thread aims for printing waiting information.
            t1.start()
            reply = IN.get()
            flag["HVmove"] = True
            t1.join()
            if reply.get("return"):
                for i in reply.get("tag",[]):
                    print(reply.get(i))
                if not reply.get("tag"):
                    print("The high voltag setting if finished.")
            else:
                for i in reply.get("tag",[]):
                    print(reply.get(i))
        elif command[0] == "SC" or command[0] == "slowControl":
            if len(command) == 2:
                if command[1] == "-d" or command[1] == "-defualt":
                    OUT.put({"cmd":"setSlowControl"})
                elif command[1] == "-s" or  command[1] ==  "-set":
                    change = []
                    msg = [""]
                    print("Please enter the item and value you want to change and end with q or cancel with c.")
                    while True:
                        msg = input(">>>").strip().split()
                        if len(msg) == 1:
                            if msg[0] == "q" or msg[0] == "c":
                                break
                            else:
                                print("unable to identify your enter.")
                                continue
                        elif len(msg) == 2:
                            if re.match("^\d$",msg[1]):
                                change.append({msg[0]:int(msg[1])})
                            else:
                                print("value must be an intager.")
                                continue
                        else:
                            print("unable to identify your enter.")
                            continue
                    if msg[0] == "c":
                        del msg
                        del change
                        continue
                    OUT.put({"cmd":"setSlowControl","change":change})
                    t1 = threading.Thread(target=SC_wait,args=(flag,))
                    t1.start()
                    reply = IN.get()
                    flag["SC"] = True
                    t1.join()
                    if reply.get("return"):
                        for i in reply.get("ExceptDescription",[]):
                            print(i)
                        if len(reply.get("ExceptDescription",[])) == 0:
                            print("Slow Control was successfully configured.")
                        else:
                            for i in reply.get("ExceptDescription", []):
                                print(i)
                    else:
                        for i in reply.get("tag"):
                            print(i)
                else:
                    x = ""
                    for i in command:
                        x += i
                    print("There is no such order: \'{0}\'".format(x))
                    del x
                    continue
        elif command[0] == "receive":
            if len(command) == 2:
                if command[1] == "-i" or command[1] == "-initiate" or command[1] == "-start":
                    OUT.put({"cmd":"startAcceptData"})
                    print("Starting the dtaa receving process.")
                    reply = IN.get()
                    if reply.get("return"):
                        print("Data receiving proess has alread started,data is stored in {0}".format(
                            reply.get("dataPath")))
                    else:
                        for i in reply.get("tag",[]):
                            print(i)
                    continue
                elif command[1] == "-c" or command[1] == "-cease" or command[1] == "-stop":
                    OUT.put({"cmd": "startAcceptData"})
                    print("Stopping the dtaa receving process.")
                    reply = IN.get()
                    if reply.get("return"):
                        print("Data receiving proess has alread stopped,data is stored in {0}".format(
                            reply.get("dataPath")))
                    else:
                        for i in reply.get("tag",[]):
                            print(i)
                    continue
                x = ""
                for i in command:
                    x += i
                print("There is no such order: \'{0}\'".format(x))
                del x
                continue
        else:
            x = ""
            for i in command:
                x += i
            print("There is no such order: \'{0}\'".format(x))
            del x
            continue






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
    taskName = ["<set slow control configuration>","<set probe configuration>","<turn on high voltag module>","<receive data>"]
    while flag["Auto"] >= 0:
        print("\rTask:{0} is in progress. {1} {2}%".format(taskName[flag["Auto"]],"█" * j + point_0[i], j * len(point_0) + i), end='')
        if i < len(point_0) - 1:
            i += 1
        else:
            i = 0
            j += 1
        while (flag["Auto"] == 0 and j*len(point_0)+i == 40) | (flag["Auto"] == 1 and j*len(point_0)+i == 80) | \
                (flag["Auto"] == 2 and j*len(point_0)+i == 90) | (flag["Auto"] == 3 and j*len(point_0)+i == 99):
            time.sleep(0.5)
        if (flag["Auto"] == 1 and j*len(point_0)+i <= 40) | (flag["Auto"] == 2 and j*len(point_0)+i <= 80) | \
                (flag["Auto"] == 3 and j*len(point_0)+i <= 90) | (flag["Auto"] == 4 and j*len(point_0)+i <= 99):
            time.sleep(0.05)
        elif j*len(point_0)+i == 100:
            flag["Auto"] = -1
        else:
            time.sleep(0.4)


if __name__ == '__main__':
    mp.set_start_method('spawn')
    print("DAQ Start!")
    toControl = mp.Queue()
    toTerminal = mp.Queue()
    p_IO = mp.Process(target=communication_test, args=(toControl,toTerminal))
    p_IO.start()
    terminal(toTerminal,toControl)
    print("all server has stopped")
    # threading.Thread
    # USBwait(False)