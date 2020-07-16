# Alpha0.2构架思路

版本Alpha0.1具有许多的缺陷：

1. 当terminal进程崩溃之后，虽然设备通讯进程不会受影响，但是重启terminal进程不能重新与设备通讯进程建立连接
2. 由于从Python调用C#DLL库，许多在C#中的状态参数和反馈在Python中接收和处理不便，不能很好的进行控制。
3. 设备通讯进程和terminal进程构架的扩展性太差

Alpha0.2采用网络编程的思路，将与设备操作的进程模块构架成一个本地服务，通过socket套接字进行操作流的通讯，套接字发送XML格式的数据，同时通过XML文件进行配置信息的存储和交互。

## server构架

sever主要在C#下构架，Python只做开启C#进程的作用。

1. 对于Alpha0.1的C#库函数大体不变，但是要对于部分函数进行修改，添加部分功能，重新实现部分功能：

   | 类          | 函数                                            | 修改情况                                                     | 备注     |
   | ----------- | ----------------------------------------------- | ------------------------------------------------------------ | -------- |
   | DAQ_IO_DLL  | check_USB(bool link=True)                       | 添加了参数，当link为False时，可以只查找USB设备而不重新连接USB设备 | 重构功能 |
   | SC_model_2E | saveAsXML(string path = "./myConfigurtion.xml") | 将SlowControl的配置情况按照XML格式存储起来                   | 添加功能 |
   | SC_model_2E | load_XML(string path = “./myConfigurtion.xml”)  | 载入XML，按照XML内的参数对配置进行修改配置                   | 添加功能 |

   

2. C#内添加socket通讯模块，包括socket服务器端、解析客户端请求。

3. server进程直接由C#开启，所以需要C#内部开启服务进程

## client构架

Alpha0.2中简单构架命令行中的client，实际可构架client如下：

1. 仿照Alpha0.1在Python界面进行构架terminal进程，通过socket连接server进程，解析处理输入字符串命令，向server发送命令流
2. 编写多个类脚本式命令，直接在命令行中运行命令，每个命令通过socket与server进行一次连接，传输相应命令流。
3. 在Python交互式界面、jupyte界面直接操作client类进行命令流通讯
4. 基于client类建立GUI交互式界面

### 构架思路

client分为三部分

第一部分是socket连接通讯模块

第二部分是解析命令流模块

第三部分是人机交互模块

对于数据分析功能另行编写

## socket套接字

####  服务器端：

  01，申请一个socket

  02，绑定到一个IP地址和一个端口上

  03，开启侦听，等待接收连接

####  客户端：

  01，申请一个socket

  02，连接服务器(指明IP地址和端口号)

  服务器端接收到连接请求后，产生一个新的socket(端口大于1024)与客户端建立连接并进行通信，原监听socket继续监听。

 注意：负责通信的Socket不能无限创建，创建的数量和操作系统有关。

## XML解析和创建

client将生成对应的格式XML文件，由此指定的配置参数值，server服务端的配置参数将读取XML文件，对默认的configure参数进行修改。

client与server的通讯结构也拟以XML格式进行传输，方便对数据内容进行解析和扩展。

### C#解析和创建XML

C#中对XML的操作可以分为两类：

第一类是对XML文档的解析和创建。

C#通过内建模块[XmlDocument](https://docs.microsoft.com/zh-cn/dotnet/api/system.xml.xmldocument?view=netcore-3.1#Find)对XML文档进行操作， 可使用此类在文档中加载、验证、编辑、添加和放置 XML。 

第二类是将已有的对象序列化为XML文件或将XML文件反序列化为C#对象。

C#通过内建模块`XmlSerializer`将对象序列化到 XML 文档中和从 XML 文档中反序列化对象。 `XmlSerializer`使您得以控制如何将对象编码到 XML 中。 

#### 用途

1. 对于server与client之间的通讯是以XML的格式进行通讯，C#内对client中传入的字节流先转化成string对象，然后使用将调用`XmlDocument`模块对具有Xml格式的string进行解析，得到指令内容。
2. C#中拟将`SC_Model_2E`和`probe_Model`的参数，通过`XmlSerializer`序列化为xml格式的数据，client通过读取xml文件来获取当前配置情况，同时通过修改xml文件，server中反序列化xml文件成`SC_Model_2E`和`probe_Model`对象来修改配置情况。

| 命令码             | 描述                                                         | 返回                                                         | 额外参数                                                     | 返回参数                                                     |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **操作命令**       |                                                              |                                                              |                                                              |                                                              |
| `connectUSB`       | 连接USB设备                                                  | 连接成功：1；未连接成功：0；发生错误；-1                     | NULL                                                         | NULL                                                         |
| `setSC`            | 从存储`SlowControl`配置信息的XML读取配置信息，向USB设备发送配置信息 | 配置成功：1；未配置成功：0；发生错误：-1                     | [<SCPath>XML路径</SCPath>]：如果没有设置则为默认配置         | NULL                                                         |
| `switchHV`         | 开关高压模块                                                 | 设置成功：1；未设置成功：0；发生错误：-1                     | <on-off>bool<on-off>：True为开启，Flase为关闭                | NULL                                                         |
| `setHV`            | 设置高压                                                     | 设置成功：1；未设置成功：0；发生错误：-1                     | <voltag>float</voltag>：表示目标电压                         | NULL                                                         |
| `smoothHV`         | 平滑调节高压                                                 | 设置成功：1；未设置成功：0；发生错误：-1                     | <voltag>float</voltag>：表示目标电压                         | 在平滑调节的过程中会不断反馈当前电压值：<voltage>float</voltage>；当调节完成后才返回return项。 |
| `startAcceptData`  | 开启接收数据线程                                             | 操作成功：1；操作失败：0；发生错误：-1                       | [<DataDir>指定Data保存文件夹路径</DataDir>]：如果没有设置则保存到默认路径 | <DataPath>路径</DataPath>：数据存储的绝对路径                |
| `stopAcceptData`   | 关闭数据接收线程                                             | 操作成功：1；操作失败：0；发生错误：-1                       | NULL                                                         |                                                              |
| `exit`             | 退出communication进程                                        | 成功退出：1；退出失败（比如还有正在运行的任务）：0；发生错误：-1 | NULL                                                         | 当进程即将结束时，会额外发送一次消息：<exit />               |
| **获取状态的命令** |                                                              |                                                              |                                                              |                                                              |
| `alive`            | 检查进程是否还在正常运行                                     | 还在运行：1；                                                | NULL                                                         | 如果超时未返回则认为进程已经死掉。                           |
| `checkUSB`         | 检查USB设备是否上线（仍在连接）                              | 正常搜索到设备：1；未搜索到设备：0；发生错误：-1             | NULL                                                         | NULL                                                         |
| `HV`               | 查看高压状态                                                 | 正常执行：1；发生错误：-1                                    | [<arg>argument</arg>]：如果没有指定，则返回HV开关状态和HV电压值。指定voltage则只返回HV电压值，指定switch则只返回HV开关状态。 | [<switch>bool</switch>]：True为HV模块已开启，False为HV模块未开启。[<voltage>float</voltage>]：返回当前高压模块的电压值。 |
| `SC`               | 查看`slowControl`配置情况                                    | 正常执行：1；发生错误：-1                                    | NULL                                                         | 在当前通讯外，会进行一次新的UDP会话，发送一个XML文件来描述`slowControl`的配置情况。 |
| `probe`            | 查看`probe`配置情况                                          | 正常执行：1；发生错误：-1                                    | NULL                                                         | 在当前通讯外，会进行一次新的UDP会话，发送一个XML文件来描述`probe`的配置情况。 |

```xml
<DAQ>
	<return>1<\return>
	<INFO><\INFO>
	<ERROR><\ERROR>
<\DAQ>
```

|        | 信息                     | 备注                                             |
| ------ | ------------------------ | ------------------------------------------------ |
| return | 1、0、-1                 | 返回0时会附加INFO节点，返回-1时会附加ERROR节点。 |
| INFO   | 造成命令未成功执行的原因 |                                                  |
| ERROR  | 错误信息                 |                                                  |

## 数据传输方式

由于采集的数据量比较大，远超过4KB；同时数据传输要求数据安全稳定的传输，减少丢失的可能性，所以采用 TCP/IP协议进行数据传输 。

当client端向server端发送指令[开启接收数据线程]后，server开启接收数据线程然后向client返回消息[成功开启线程]，之后client开启通过 TCP协议与server建立一个长连接进行数据的接收。

## 任务解析

| **任务**                      |                                            |                                |
| ----------------------------- | ------------------------------------------ | ------------------------------ |
| **socket通讯模块**            | C#中为server服务端，Python中为client客户端 | `C#`:True,`Python`:underway    |
| **通讯协议规范**              | 规范各类命令与数据的传输方式和格式         |                                |
| xml解析模块                   |                                            | `C#`：True，`Python`：underway |
| C#解析命令                    |                                            | finished                       |
| Python解析命令                |                                            | wait for start                 |
| C#配置类的xml序列化与反序列化 |                                            | wait for start                 |
| Python载入和修改xml           |                                            | underway                       |
| C#server与驱动库链接          |                                            | finished                       |
| client人机交互                |                                            | underway                       |
| **数据解析模块**              |                                            | underway                       |

