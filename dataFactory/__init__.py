'''

'''
# todo: 建立一个数据仓库

def newMouthOfMaterial():
    # 新建一个入料口
    pass

def newGoodsShelf():
    # 新建一个货架
    pass

def pushRawMaterial(rm):
    # 将rawMaterial放入对应的入料口
    pass

def pushProduction(pd):
    # 将production放入仓库中
    pass

'''
    数据封装：
    rawMaterial 原始数据
    production 计算结果
    数据入口：
    mouthOfMaterial 放入原始数据
        --include:productionLine 处理原始数据，输出production
    dataStorage 放入计算结果production
        --include:goodsShelf 将放入的production堆叠合并
    数据处理/存储：
        productionLine
        goodsShelf
    
'''