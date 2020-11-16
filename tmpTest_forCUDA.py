from numba import cuda
import numpy as np
import numba
import math
from time import time

@cuda.jit
def gpu_add(a, b, result, n):
    idx = cuda.threadIdx.x + cuda.blockDim.x * cuda.blockIdx.x
    if idx < n :
        result[idx] = a[idx] + b[idx]

@cuda.jit
def gpu_copy(rawData, output,n):
    l = cuda.shared.array((32,32),numba.float32)
    idx = cuda.threadIdx.x + cuda.blockDim.x * cuda.blockIdx.x
    if idx < n:
        for i in range(3):
            output[idx,i] = rawData[idx,i] + n

def main():
    n = 50000000
    x = np.arange(n).astype(np.int32)
    y = 2 * x

    # 拷贝数据到设备端
    x_device = cuda.to_device(x)
    y_device = cuda.to_device(y)
    # 在显卡设备上初始化一块用于存放GPU计算结果的空间
    gpu_result = cuda.device_array(n)
    cpu_result = np.empty(n)

    threads_per_block = 1024
    blocks_per_grid = math.ceil(n / threads_per_block)
    start = time()
    gpu_add[blocks_per_grid, threads_per_block](x_device, y_device, gpu_result, n)
    cuda.synchronize()
    r = gpu_result.copy_to_host()
    print(r[:100])
    print("gpu vector add time " + str(time() - start))
    start = time()
    np.add(x, y,out = cpu_result)
    print("cpu vector add time " + str(time() - start))

    if (np.array_equal(cpu_result, gpu_result.copy_to_host())):
        print("result correct!")

if __name__ == "__main__":
    n = np.arange(3)
    print(np.linalg.norm(n))
    print(np.sqrt(np.sum(n**2)))
    n = np.arange(6).reshape((3,2))
    print(n)
    print(n.reshape((-1,)))

    n = 5000
    rawData = np.arange(n*3).astype(np.int32).reshape((-1,3))
    r = cuda.to_device(rawData)
    out = cuda.device_array(rawData.shape)
    cuda.synchronize()
    threads_per_block = 32
    blocks_per_grid = math.ceil(n / threads_per_block)
    gpu_copy[blocks_per_grid, threads_per_block](r,out,n)
    output = out.copy_to_host()
    print(output[:10])