# USB接口初步

## 一、USB接口构成

 在USB设备的逻辑组织中，包含**设备、配置、接口和端点**4个层次。 

 ![img](https://img-blog.csdn.net/20180809081452266?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L2V5ZGoyMDA4/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70) 

每个USB设备都提供了不同级别的配置信息，可以包含一个或多个配置，不同的配置使设备表现出不同的功能组合（在探测/连接期间需从其中选定一个），配置由多个接口组成。 

 在USB协议中，接口由多个端点组成，代表一个基本的功能，是USB设备驱动程序控制的对象，一个功能复杂的USB设备可以具有多个接口。

每个配置中可以有多个接口，而设备接口是端点的汇集（collection）。  如USB扬声器可以包含一个音频接口以及对旋钮和按钮的接口。一个配置中的所有接口可以同时有效，并可被不同的驱动程序连接。

每个接口可以有备用接口，以提供不同质量的服务参数。  

端点是USB通信的最基本形式，每一个USB设备接口在主机看来就是一个端点的集合。

主机只能通过端点与设备进行通信，以使用设备的功能。在USB系统中每一个端点都有惟一的地址，这是由设备地址和端点号给出的。每个端点都有一定的属性，其中包括传输方式、总线访问频率、带宽、端点号和数据包的最大容量等。一个USB端点只能在一个方向承载数据，或者从主机到设备（称为输出端点），或者从设备到主机（称为输入端点），因此端点可看作一个单向的管道。端点0通常为控制端点，用于设备初始化参数等。只要设备连接到USB上并且上电端点0就可以被访问。端点1、2等一般用作数据端点，存放主机与设备间往来的数据。 

-------------------

如果按照USB协议栈的层次划分：
一个Host可能有一个或者多个Device
一个Device可能有一个或者多个Interface
一个Interface可能有一个或者多个Endpoint

首先端点跟信号线没任何关系，如果对应到TCP/IP协议栈的话，类似于TCP/UDP里的端口概念。

**Host（主机）连的是Device（设备）**，这一层是走物理连接的，也就是这个信号线。对应到网络协议栈，就是两台主机，或者服务器-客户机这种层次（USB线相当于网线）。

**Device（设备）下可能有多个Interfece（接口）**，从这开始都是逻辑概念了，一个Interface，可以理解为像两个联网的电脑上里不同的通信软件，比如有浏览器，有QQ，每个Interface模拟一个设备功能，比如集成了键盘和鼠标的USB设备，里面就是两个interface，一个是键盘，另一个是鼠标。Interface之间通常是隔离的，互相不干扰。

**每个Interface（接口）下面有一个或者多个Endpoint（端点）**，这也是逻辑概念，比如QQ要通信，可能开好几个端口，同样U盘要跟主机通信，要有控制信号和数据信号，这些都是不同的端点。端点是USB设备通信的基本单位，所有通信几乎都是从端点发起的。

## 二、PyUSB结构

### 1.搜寻USB设备（find USB device）

 找到一个USB设备并返回它。`find()`是用来发现USB设备的函数。您可以将USB设备描述符字段的任何组合作为参数传递来匹配设备。例如：

```python
 find(idVendor=0x3f4, idProduct=0x2009)
```

 将返回`idVendor`字段等于`0x3f4`, `idProduct`等于`0x2009`的设备的设备对象。 

 如果有多个设备符合条件，则返回找到的第一个设备。如果找不到匹配的设备，函数将返回`None`。如果希望获得所有设备，可以将参数`find_all`设置为`True`，然后`find`将返回一个包含所有匹配设备的迭代器。如果没有找到匹配的设备，它将返回一个空的迭代器。例如：

```python
for printer in find(find_all=True, bDeviceClass=7):
	print (printer)
```

 这个调用将使所有的USB打印机连接到系统。(实际上可能不是，因为一些设备将它们的类信息放在接口描述符中)。

 您还可以使用定制的匹配条件 : 

```python
dev = find(custom_match = lambda d: d.idProduct=0x3f4 and d.idvendor=0x2009)
```

 使用自定义匹配的更精确的打印机查找程序应该是这样的:

```python
def is_printer(dev):
    import usb.util
    if dev.bDeviceClass == 7:
    	return True
    for cfg in dev:
        if usb.util.find_descriptor(cfg, bInterfaceClass=7) is not None:
            return True

for printer in find(find_all=True, custom_match = is_printer):
    print (printer)
```

 现在，即使设备类代码在接口描述符中，也会找到打印机。 

 您可以将自定义匹配与设备描述符字段相结合。在这种情况下，字段必须匹配，`custom_match`必须返回`True`。在我们前面的例子中，如果我们想获得属于制造商`0x3f4`的所有打印机，代码应该是这样的 :

```python
printers = list(find(find_all=True, idVendor=0x3f4, custom_match=is_printer))
```

 如果您想使用`find`作为包含所有设备的列表类型，只需使用find_all = True调用它 

```python
devices = list(find(find_all=True))
```

 最后，可以将自定义后端传递给`find`函数

```python
find(backend = MyBackend())
```

 PyUSB为`libusb 0.1`、`libusb 1.0`和`OpenUSB`提供内置后端。如果您没有显式地提供后端，`find()`函数将根据系统可用性选择一个预定后端。后端是解释在 `usb.backend` 模块。 

### 2.class Device

设备对象。

这个类根据USB规范包含设备描述符的所有字段。您可以将它们作为类属性访问。

例如，要访问设备描述符的`bDescriptorType`字段，您可以这样做:

```python
>>> import usb.core
>>> dev = usb.core.find()
>>> dev.bDescriptorType
```

此外，该类提供了与硬件通信的方法。
通常，应用程序首先调用`set_configuration()`方法将设备置于已知配置状态，可选地调用
`set_interface_altsetting()`来选择所使用的接口的替代设置 (如果有的话)，并调用`write()`和`read()`方法分别发送和接收数据。

当在一个新的硬件上工作时，第一次尝试可能是这样的: 

```python
>>> import usb.core
>>> dev = usb.core.find(idVendor=myVendorId, idProduct=myProductId)
>>> dev.set_configuration()
>>> dev.write(1, 'test')
```

 这个示例找到感兴趣的设备(`myVendorId`和`myProductId`应该被设备的相应值替换)，然后配置该设备(默认情况下，配置值为1，这是大多数设备的典型值)，然后将一些数据写入端点`0x01`。 

 `write()`, `read()`和`ctrl_transfer()`方法的超时值以毫秒为单位指定。如果省略了该参数，那么将使用`Device.default_timeout`的值。用户可以随时设置此属性。 

#### 常用方法：

```python
def write(self, endpoint, data, timeout = None)
```

Write data to the endpoint.

##### endpoint

This method is used to send data to the device. The `endpoint` parameter corresponds to the `bEndpointAddress` member whose endpoint you want to communicate with.

你将数据发送给哪个端点。

##### data

The `data` parameter should be a sequence like type convertible to the array type (see array module).

数据只能是array类型。

##### timeout

The `timeout` is specified in miliseconds.

##### returns

The method returns the number of bytes written.

```python
def read(self, endpoint, size_or_buffer, timeout = None)
```

Read data from the endpoint.

##### endpoint

This method is used to receive data from the device. The `endpoint` parameter corresponds to the `bEndpointAddress` member whose endpoint you want to communicate with. 

##### size_or_buffer

The `size_or_buffer` parameter either tells how many bytes you want to read or supplies the buffer to receive the data (it *must* be an object of the type array).

If the `size_or_buffer` parameter is the number of bytes to read, the method returns an array object with the data read. 

If the `size_or_buffer` parameter is an array object, it returns the number of bytes actually read.

##### timeout

The `timeout` is specified in miliseconds.



```python
def configurations(self):
	r"""Return a tuple of the device configurations."""
    return tuple(self)
```





### 3.class Configuration

 表示配置对象。

这个类包含根据USB规范配置描述符的所有字段。您可以将它们作为类属性访问。例如，要访问配置描述符的`bConfigurationValue`字段，您可以这样做: 

```python
>>> import usb.core
>>> dev = usb.core.find()
>>> for cfg in dev:
>>>     print cfg.bConfigurationValue
```

#### 常用函数：

```python
def interfaces(self):
    r"""Return a tuple of the configuration interfaces."""
    return tuple(self)
```



```python
def set(self):   
    r"""Set this configuration as the active one."""    		 
    self.device.set_configuration(self.bConfigurationValue)
```



### 4.class Interface

表示接口对象。
这个类包含接口描述符的所有字段

根据USB规格。您可以作为类访问它们
属性。例如，要访问字段`bInterfaceNumber`

对于接口描述符，您可以这样做:

```python
>>> import usb.core
>>> dev = usb.core.find()
>>> for cfg in dev:
>>>     for i in cfg:
>>>         print i.bInterfaceNumber
```

#### 常用函数：

```python
def endpoints(self):
    r"""Return a tuple of the interface endpoints."""
    return tuple(self)
```

### 5.class Endpoint

表示端点对象。
这个类根据USB规范包含端点描述符的所有字段。
您可以将它们作为类属性访问。
例如，要访问端点描述符的`bEndpointAddress`字段，可以这样做

```python
>>> import usb.core
>>> dev = usb.core.find()
>>> for cfg in dev:
>>>     for i in cfg:
>>>         for e in i:
>>>             print e.bEndpointAddress
```

#### 常用函数：

```python
def write(self, data, timeout = None):
	return self.device.write(self, data, timeout)
```

```python
def read(self, size_or_buffer, timeout = None):
    return self.device.read(self, size_or_buffer, timeout)
```

