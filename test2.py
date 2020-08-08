from multiprocessing import Process, Value, Lock
from multiprocessing.managers import BaseManager
import pandas as pd


class Employee(object):

    def __init__(self, name, salary):
        self.name = name
        self.salary = Value('i', salary)
        self.data = []
        self.Frame = {"A": 1, "B": 2}

    def increase(self):
        self.salary.value += 100
        self.data.append([self.salary.value])
        print(self.data)
        print(self.Frame)

    def getPay(self):
        return self.name + ':' + str(self.salary.value)


def func1(em, lock):
    with lock:
        em.increase()



# @snoop()
def main():
    manager = BaseManager()
    manager.register('Employee', Employee)
    manager.start()
    em = manager.Employee('zhangsan', 1000)
    lock = Lock()
    proces = [Process(target=func1, args=(em, lock)) for i in range(10)]
    for p in proces:
        p.start()
    for p in proces:
        p.join()
    print((em.getPay()))


if __name__ == '__main__':
    main()