import math
import numba
import numpy as np
from numba import cuda
from numba.cuda import random

# 比率算法算法
def ratio_main(event:np.array,detectPlace: np.array,amplification: int = 32*1024,**kwargs):
    '''
    通过比率算法扩展poca点
    :param event: 原始数据(None,10)[poca_x,poca_y,poca_z,theta,p1_x, p1_y, p1_z, p2_x, p2_y, p2_z]
    :param detectPlace: (3,2)[x,y,z]-[min,max)
    :param amplification: 扩展次数
    :param kwargs:theta_cut-角度阈值;device_GPU-是否使用GPU计算;cube_size-探测区域的大小
    :return:(None,6)[MSR_x, MSR_y, MSR_z, MSC, ratio,available]
    '''
    theta_cut = kwargs.get("theta_cut",0.9)
    device_GPU = kwargs.get("device_GPU",True)# todo: 检测GUP是否就绪，未就绪则改为CPU计算
    cube_size = kwargs.get("cube_size",5)
    #============GPU处理部分==========
    # 预处理,分配显存空间
    '''
    input
    1.poca point,Angle:pocaPoints(None,4)-[x,y,z,angle]
    2.poca point-incoming point Vector:poca_inVector(None,4)-[x,y,z]
    3.outgoing point-poca point Vector:out_pocaVector(None,4)-[x,y,z]
    output
    (amplification,6)[MSR_x, MSR_y, MSR_z, MSC, ratio,available]
    '''
    toDevice = np.empty(event.shape).astype(np.float32)
    toDevice[:,:4] = event[:,:4]
    toDevice[:,4:7] = event[:,:3] - event[:, 4:7]
    toDevice[:,7:] = event[:,7:] - event[:,:3]
    toDevice = cuda.to_device(toDevice)
    output = cuda.device_array((amplification,6))
    # 初始化网格参数和随机数生成器
    threads_num = 32
    blocks = math.ceil(amplification / threads_num)
    rng_states = random.create_xoroshiro128p_states(amplification,seed=1)
    # 初始化探测空间
    detectPlace[:,1] = detectPlace[:,1] - detectPlace[:,0]
    detectPlace = detectPlace.reshape((-1,))
    cuda.synchronize()
    _ratioForGPU[blocks,threads_num](rng_states,toDevice,output,*detectPlace,cube_size/2,theta_cut)
    cuda.synchronize()
    result = output.copy_to_host()
    return result[result[:,5] > 0.8]

@cuda.jit
def _ratioForGPU(randomCreater,rawData,output,X_start,X_length,Y_start,Y_length,Z_start,Z_length,cube_size,theta_cut):
    # share memory distribution
    random_points = cuda.shared.array(shape=(32, 3),dtype=numba.float32)    #random points
    RotiaParameters = cuda.shared.array(shape=(32, 3),dtype=numba.float32)  #N_all,Cut_N,Angle_sigma
    tmpSorage = cuda.shared.array(shape=(32, 6),dtype=numba.float32)
    # local memory distribution
    poca_randomVector = cuda.local.array((3,),numba.float32)    #poca point-random point Vector,Angle
    # init randomPoint
    idx = cuda.grid(1)
    random_points[cuda.threadIdx.x,0] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3)*X_length+X_start
    random_points[cuda.threadIdx.x,1] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3+1)*Y_length+Y_start
    random_points[cuda.threadIdx.x,2] = random.xoroshiro128p_uniform_float32(randomCreater,idx*3+2)*Z_length+Z_start
    # init CountParameters
    for i in range(3):
        RotiaParameters[cuda.threadIdx.x,i] = 0.
    # start cycle
    for i in range(rawData.shape[0]):
        # get poca_randomVector
        check = True
        for j in range(3):
            poca_randomVector[j] = rawData[i,j] - random_points[cuda.threadIdx.x,j]
            if poca_randomVector[j] >= cube_size:
                check = False
        # poca在探测区域内
        if check:
            RotiaParameters[cuda.threadIdx.x,0] += 1
            norm = 0.
            for j in range(3):
                norm += poca_randomVector[j]**2
            Angle = rawData[i,3] * abs(1. -norm * 2. / (cube_size * math.sqrt(3.)))
            RotiaParameters[cuda.threadIdx.x,2] += Angle**2
            if Angle <= theta_cut:
                RotiaParameters[cuda.threadIdx.x,2] += 1
        # poca在探测区域外
        else:
            # poca在探测区域上方
            if poca_randomVector[2] < 0:
                upDown = 0
            # poca在探测区域下方
            else:
                upDown = 3
            # load data(poca point and poca_incomingVector/outgoing_pocaVector depend on arg:upDown)
            # from rawData(global memory) to share memory
            for j in range(3):
                tmpSorage[cuda.threadIdx.x,j] = rawData[i,j] # poca point
                tmpSorage[cuda.threadIdx.x,j+3] = rawData[i,j+4+upDown] #poca_incomingVector
            check = True
            for j in range(2):
                tmp = tmpSorage[cuda.threadIdx.x,3+j] / tmpSorage[cuda.threadIdx.x,5] * \
                    (random_points[cuda.threadIdx.x,2] + cube_size / 2 - tmpSorage[cuda.threadIdx.x,2]) \
                        + tmpSorage[cuda.threadIdx.x,j] - random_points[cuda.threadIdx.x,j]
                if tmp >= cube_size:
                    check = False
                    break
                tmp = tmpSorage[cuda.threadIdx.x, 3 + j] / tmpSorage[cuda.threadIdx.x, 5] * \
                      (random_points[cuda.threadIdx.x, 2] - cube_size / 2 - tmpSorage[cuda.threadIdx.x, 2]) \
                      + tmpSorage[cuda.threadIdx.x, j] - random_points[cuda.threadIdx.x, j]
                if tmp >= cube_size:
                    check = False
                    break
            if check:
                RotiaParameters[cuda.threadIdx.x, 0] += 1
                RotiaParameters[cuda.threadIdx.x, 1] += 1
    for i in range(3):
        output[idx,i] = random_points[cuda.threadIdx.x,i]
    output[idx,3] = math.sqrt(RotiaParameters[cuda.threadIdx.x,2] / RotiaParameters[cuda.threadIdx.x,0])
    output[idx,4] = RotiaParameters[cuda.threadIdx.x,1] / RotiaParameters[cuda.threadIdx.x,0]
    if RotiaParameters[cuda.threadIdx.x, 0] > math.floor(100 * (cube_size*2) **2 *0.1):
        output[idx,5] = 1
    else:
        output[idx, 5] = -1