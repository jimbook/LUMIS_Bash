from dataLayer.calculateForNumba import *
if __name__ == '__main__':
    d = pd.read_csv("./tmpStorage/channelReplace.csv")
    hd = h5Data("./testData/h5Data/tempData_22_59_16.h5","r")
    data = hd.getData(-2)
    fd = pretreatment_forNumba(data)
    print(fd.shape)
    msData = meanScale_forNumba(fd,meanScaleInfo.values[:,:32],threshold.values[:, :32],baseline.values[:,:32])
    cData = checkTriggerAvailable_forNumba(msData)
    geo = pd.read_csv("./tmpStorage/geometrySystem.csv",header=0,index_col = 0)
    dParameter = pd.read_csv("./tmpStorage/detectorGeometryParameter.csv",header=0,index_col=0)
    triggerSite = fastCalculateTriggerPositions_forNumba(cData,geo.values,dParameter.values[0])
    pos = fastCalculateParticleTrack(triggerSite,geo.values,dParameter.values[0])
    poca = calculatePocaPostions_forNumba(pos)
    start = time.time()
    points_ratio = ratio_main(poca,pd.read_csv("./tmpStorage/detectPlace.csv",header=0,index_col=0).values)
    print("poca event:{},ratio running time:{}s".format(poca.shape[0],time.time()-start))
    print(points_ratio.shape)

