from threading import Lock
# 当使用数据的时候调用线程锁来保证数据的完整性
dataLock = Lock()