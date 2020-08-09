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
    import pyqtgraph.examples
    pyqtgraph.examples.run()