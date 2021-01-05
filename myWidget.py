#实现文件树
from PyQt5.QtWidgets import QTreeView,QFileSystemModel
class NewTreeView(QTreeView):
    def __init__(self,parent= None,workPath = ''):
        super().__init__()
        self.myModel = QFileSystemModel()
        self.setTree(self.myModel)
        self.setWorkPath(workPath)
    #设置树控件大小等
    def setTree(self,model):
        self.setModel(self.myModel)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)
        self.header().hide()
        self.setAnimated(False)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setWindowTitle("Dir View")
        self.resize(640, 480)
    #设置工作目录
    def setWorkPath(self,workPath):
        self.myModel.setRootPath(workPath)
        self.setRootIndex(self.myModel.index(workPath))