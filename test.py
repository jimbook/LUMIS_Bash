from multiprocessing import Process, Value, Lock,Event
from multiprocessing.managers import BaseManager
import pandas as pd
class Employee(object):
    data = []
    def __init__(self, name, salary):
        self.name = name
        self.salary = Value('i', salary)
        self.Frame = {"A":1,"B":2}

    def increase(self):
        self.salary.value += 100
        self.data.append([self.salary.value])
        print(self.data)
        print(self.Frame)

    def getPay(self):
        return self.name + ':' + str(self.salary.value)

class EM(BaseManager):
    pass
e = Employee('zhangsan', 1000)
l = Event()
def get_e():
    return e
EM.register("Employee",callable=get_e)
EM.register("Event",callable=lambda :l)
def func1(em, lock):
    with lock:
        em.increase()

def func2(lock):
    print("func")
    with lock:
        m = EM(address=("127.0.0.1",50000),authkey=b'abcd')
        m.connect()
        em = m.Employee()
        em.increase()



#@snoop()
def main():
    manager = EM(address=("127.0.0.1",50000),authkey=b'abcd')
    manager.start()
    #e = manager.Employee('zhangsan', 1000)
    lock = Lock()
    proces = [Process(target=func2, args=(lock,)) for i in range(10)]
    for p in proces:
        p.start()
    for p in proces:
        p.join()

if __name__ == '__main__':
    import os
    for root,dirs,files in os.walk("C:\\Users\\jimbook\\Desktop\\configuration"):
        for f in files:
            with open(os.path.join(root,f),'rb') as bf:
                binary = bf.read()
            with open(os.path.join(root,f.split(".")[0]+"_4boards.dat"),"wb") as wf:
                wf.write(b'\xff\xe4')
                wf.write(binary[2:])
