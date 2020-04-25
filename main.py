import sys
import clr
sys.path.append(r'A:\工作\实验室\LUMIS\DAQ_IO\DAQ_IO\bin\Debug')
clr.AddReference('DAQ_IO')



#indata = None
#while True:
#    indata = input(">>>").split()
#
#    if indata[0] == "exit":
#        break
#print("DAQ exited now.")

from multiprocessing import Process
import os

import multiprocessing as mp

def communication(q : mp.Queue):
    while True:
        command = q.get()
        print(command[0])

def terminal(q : mp.Queue):
    while True:
        import time
        time.sleep(1)
        command = input(">>>")
        if command.split()[0] == "turnOnHV":
            q.put(["OpenHV"])


if __name__ == '__main__':
    mp.set_start_method('spawn')
    q = mp.Queue()
    p_IO = mp.Process(target=communication, args=(q,))
    p_IO.start()
    terminal(q)