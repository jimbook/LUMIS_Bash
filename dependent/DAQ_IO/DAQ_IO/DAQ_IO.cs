using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using CyUSB;
using System.Threading.Tasks;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Formatters.Binary;

namespace DAQ_IO_DLL
{
    public class DAQ_IO
    {
        //与USB驱动相关的变量和函数
        private USBDeviceList usbDevices;//usb设备列表
        private CyUSBDevice myDevice;//usb设备
        private CyBulkEndPoint bulkInEndPt;//用于接收数据
        private CyBulkEndPoint bulkOutEndPt;//用于发送数据
        private bool usbStatus = false;//usb状态：：是否准备好；实际是给其他上层函数查看的
        private const int VID = 0x04B4;
        private const int PID = 0x1004;

        //寻找usb设备，并连接
        /* 寻找匹配的USB设备，
         * 失败返回false，
         * 成功则返回true，同时配置myDevice、bulkInEndPt、bulkOutEndPt、usbStatus
         * bool变量可以传递给python，可在Python中调用
         */
        public bool check_USB()
        {
            usbDevices = new USBDeviceList(CyConst.DEVICES_CYUSB);
            bool result = true;
            myDevice = usbDevices[VID, PID] as CyUSBDevice;
            if (myDevice != null)
            {
                usbStatus = true;
                bulkOutEndPt = myDevice.EndPointOf(0x08) as CyBulkEndPoint; // EP8
                bulkInEndPt = myDevice.EndPointOf(0x82) as CyBulkEndPoint; //EP2
                bulkInEndPt.XferSize = bulkInEndPt.MaxPktSize * 8;  // transfer size means the max limits of data in USB driver
                bulkInEndPt.TimeOut = 100;
            }
            else
            {
                usbStatus = false;
                bulkOutEndPt = null;
                bulkInEndPt = null;
                result = false;
            }
            return result;
        }

        public DAQ_IO() { }

        //返回usb接收和发送设备
        //发送二进制命令|send binary data to usbdev
        /* 发送二进制命令
         * 默认USB配置成功，
         * 输入参数OutData是要发送的命令，xferLen是byte命令长度
         * byte[]不能从Python向C#直接传递，不宜在Python中调用
         */
        public bool CommandSend(byte[] OutData, int xferLen)
        {
            return bulkOutEndPt.XferData(ref OutData, ref xferLen);
        }
        /*为了匹配原库的部分代码而保留
         * 保留发送二进制命令
         * 默认USB配置成功，
         * 输入参数OutData是要发送的命令，xferLen是byte命令长度，但是实际只支持2bytes长度的命令
         * 不宜在python中调用
         */
        private bool CommandSend(int Outdata, int xferLen)
        {
            byte[] cmdbytes = new byte[2];
            cmdbytes[0] = (byte)Outdata;
            cmdbytes[1] = (byte)(Outdata >> 8);
            return bulkOutEndPt.XferData(ref cmdbytes, ref xferLen);
        }
        /* 发送二进制命令
         * 默认USB配置成功，
         * 输入参数OutData是要发送的命令,内部会转换成2bytes长的byte[]
         * int能在Python与C#之间直接传递，用于在python中调用
         */
        private bool CommandSend(int Outdata)
        {

            byte[] cmdbytes = new byte[2];
            int xferLen = 2;
            cmdbytes[0] = (byte)Outdata;
            cmdbytes[1] = (byte)(Outdata >> 8);
            return bulkOutEndPt.XferData(ref cmdbytes, ref xferLen);
        }
        //接收二进制数据包|recieve binary data from usbdev
        /* 接收二进制数据包
         * 默认USB已经配置好
         * 将接收的参数放入InData中，xferLen是本次读取的字节长度，
         * byte[]不能从Python向C#直接传递，不宜在Python中调用
         */
        public bool DataRecieve(byte[] InData, ref int xferLen)
        {
            return bulkInEndPt.XferData(ref InData, ref xferLen, true);
        }

        //参数配置相关
        SC_model_2E slowConfig = new SC_model_2E();//slowControl配置参数存储
        SC_board_manager slowControlManager = new SC_board_manager();//主板配置管理
        Probe_2E probeConfig = new Probe_2E();//探针配置参数存储
        SC_board_manager probeManager = new SC_board_manager();//探针配置管理
        //配置slow_control
        //单次配置slowControl
        /* 配置slowControl
         * 将变量slowConfig用slowControlManager变为二进制，
         * 第一个byte为0x03，第二个byte从slowControlManager输出的二进制数组获取，每次发送两个bytes，直到数组数据发送完毕
         * 可以直接在Python中调用
         */
        public void sc_config_once()
        {

            //before sc config, do some FPGA logic configurationa first
            int chip_num = 1;
            CommandSend(0x1300 + chip_num, 2);//send chip_num, we only have 1 SP2E.
            CommandSend(0x0c00, 2);//disable external trigger, valid and eraze. {cmd[2],cmd[1],cmd[0]}
            CommandSend(0x0900, 2);//disable flag_tdc_ext.
            CommandSend(0x0e02, 2);//send event_num package
            CommandSend(0x1100, 2);//disable s_curve_count
            CommandSend(0x1500, 2);//Slow clock=5MHz
            CommandSend(0x1600, 2);//Sync signal output every 1000 Slow clock period
            CommandSend(0x1a01, 2);//enable limit acquire
            CommandSend(0x1b03, 2);//mask length (3+1)*25ns
            CommandSend(0x1900, 2);//top level of external trigger,valid and eraze, I disable it here. Enable it by send 0x19e4


            int byte_count = 0;

            byte[] cmdBytes = new byte[2];
            byte[] bit_block = new byte[1000];  //SPIROC2b has 929 config bit, 929 / 8 = 116 ... 1, need 117 bytes, SPIROC2E need 1186 / 8 = 148 ... 2, so 149 bytes

            List<SC_model_2E> slowConfigTmpChain2E = new List<SC_model_2E>();
            // Is not pretty use slowControlManager this way!!!!!!! but I just used it.
            // setting should detech with config
            slowControlManager.clearChip();
            for (int i = 0; i < 1; i++)
            {
                slowConfigTmpChain2E.Add(Copy<SC_model_2E>(slowConfig));
                slowConfigTmpChain2E[i].set_property(slowConfig.settings["CHIPID"], reverse_bit(bin2gray(1), 8));  // the last chip config first
            }

            // First chip that push in the manager will transmit first, configure the furthest chip
            for (int i = 0; i >= 0; i--)
            {
                slowControlManager.chipVersion = 2;
                slowControlManager.pushChip(slowConfigTmpChain2E[i]);
            }
            byte_count = slowControlManager.bit_transform(bit_block);

            // reset spiroc2b           
            //CommandSend(0x0400, 2);
            Thread.Sleep(100);

            // set probe/sc setting as slow control
            cmdBytes[1] = 0x06;
            cmdBytes[0] = 0x01;
            CommandSend(cmdBytes, 2);

            // choose data transfer to sc buffer
            cmdBytes[1] = 0x05;
            cmdBytes[0] = 0x01;
            CommandSend(cmdBytes, 2);
            Thread.Sleep(100);
            // send config data
            cmdBytes[1] = 0x03;
            for (int i = 0; i < byte_count; i++)
            {
                cmdBytes[0] = bit_block[i];
                CommandSend(cmdBytes, 2);
                //Thread.Sleep(100);
            }

            // close channel of data to sc buffer
            cmdBytes[1] = 0x05;
            cmdBytes[0] = 0x00;
            CommandSend(cmdBytes, 2);

            // start slow config from fpga to asic
            cmdBytes[1] = 0x08;
            cmdBytes[0] = 0x00;
            CommandSend(cmdBytes, 2);
            Thread.Sleep(100);
        }
        /*更改slowControl配置 
         * 用于
         */
        //单次配置probe
        /*配置probe
         * 原理同上
         * 注意：更改/初次配置时，一定要将probeConfig初始化（调用probeConfig.init()）
         * 可以在Python中调用，但是一定要初始化配置类
         */
        public void probe_config_once()
        {
            //before probe config, do some FPGA logic configurationa first
            int chip_num = 1;
            CommandSend(0x1300 + chip_num, 2);//send chip_num, we only have 1 SP2E.
            CommandSend(0x0c00, 2);//disable external trigger, valid and eraze. {cmd[2],cmd[1],cmd[0]}
            CommandSend(0x0900, 2);//disable flag_tdc_ext.
            CommandSend(0x0e02, 2);//send event_num package
            CommandSend(0x1100, 2);//disable s_curve_count
            CommandSend(0x1500, 2);//Slow clock=5MHz
            CommandSend(0x1600, 2);//Sync signal output every 1000 Slow clock period
            CommandSend(0x1a01, 2);//enable limit acquire
            CommandSend(0x1b03, 2);//mask length (3+1)*25ns
            CommandSend(0x1900, 2);//top level of external trigger,valid and eraze, I disable it here. Enable it by send 0x19e4

            int byte_count = 0;

            byte[] cmdBytes = new byte[2];
            byte[] bit_block = new byte[1000];  //SPIROC2E has 992 Probe config bit, 992 * 6 / 8 = 744 , need 744 bytes
            probeManager.clearChip();
            for (int i = 0; i < 1; i++)
            {
                probeManager.pushChip(Copy<Probe_2E>(probeConfig));
            }
            byte_count = probeManager.bit_transform(bit_block);

            // set probe/sc setting as probe
            CommandSend(0x0600, 2);

            // choose data transfer to sc buffer
            cmdBytes[1] = 0x05;
            cmdBytes[0] = 0x01;
            CommandSend(cmdBytes, 2);
            Thread.Sleep(100);
            // send config data
            cmdBytes[1] = 0x03;
            for (int i = 0; i < byte_count; i++)
            {
                cmdBytes[0] = bit_block[i];
                CommandSend(cmdBytes, 2);
                //Thread.Sleep(100);
            }

            // close channel of data to sc buffer
            cmdBytes[1] = 0x05;
            cmdBytes[0] = 0x00;

            CommandSend(cmdBytes, 2);

            // start slow config from fpga to asic
            cmdBytes[1] = 0x08;
            cmdBytes[0] = 0x00;
            CommandSend(cmdBytes, 2);
            Thread.Sleep(100);

        }

        //调高压相关
        private decimal current_hv = 50;//当前电压
        //设置高压电压
        /*通过command发送指令
         * 需要打开高压
         */
        public void hv_set(decimal voltage)
        {
            byte[] voltage_hex = new byte[4];
            uint temp;
            string cmd;
            byte[] cmd_hex = new byte[100];
            int cmd_length = 0;

            temp = (uint)(voltage / (decimal)1.812 * 1000);
            voltage_hex[0] = toascii((byte)(temp >> 12));
            voltage_hex[1] = toascii((byte)((temp >> 8) & 0x0f));
            voltage_hex[2] = toascii((byte)((temp >> 4) & 0x0f));
            voltage_hex[3] = toascii((byte)(temp & 0x0f));

            cmd = "HST0000000000000000" + System.Text.Encoding.ASCII.GetString(voltage_hex) + "C8BE";
            cmd_hex = System.Text.Encoding.ASCII.GetBytes(cmd);
            cmd_length = 27;
            CommandSend(0x0503, 2); //选通HV control config sending channel

            uart_send(cmd_hex, cmd_length);

            CommandSend(0x0502, 2); //停止选通HV control config sending channel
        }
        //开启/关闭高压
        public void hv_switch(bool turnOn)
        {
            string cmd = "";
            byte[] cmd_hex = new byte[100];
            int cmd_length = cmd.Length;
            if (turnOn)
            {
                cmd = "HON";
            }
            else
            {
                cmd = "HOF";
            }
            cmd_hex = System.Text.Encoding.ASCII.GetBytes(cmd);
            cmd_length = 3;
            CommandSend(0x0503, 2); //选通HV control config sending channel
            uart_send(cmd_hex, cmd_length);
            CommandSend(0x0502, 2); //停止选通HV control config sending channel
        }

        //线程相关
        public CancellationTokenSource hv_setTks = new CancellationTokenSource();
        public CancellationTokenSource dataAcqTks = new CancellationTokenSource();
        public CancellationTokenSource specialTaskTks = new CancellationTokenSource();
        //读取数据并写入二进制流中
        /* 原库保留项
         * 是一个线程函数
         * 不建议在Python中调用
         */
        public void dataAcq_threadFunc(CancellationToken token, BinaryWriter bw)
        {
            byte[] data_buffer = new byte[512];
            int len;
            bool bResult;
            while (true)
            {
                if (token.IsCancellationRequested)
                {
                    Thread.Sleep(100);
                    len = 512;
                    bResult = DataRecieve(data_buffer, ref len); // len could be changed for transmit actually num of byte that received
                    bw.Write(data_buffer, 0, len);   // data source, start_index, data_length
                    if (bResult == false)
                    {
                        bw.Flush();
                        break;
                    }
                }
                else
                {
                    len = 512;
                    bResult = DataRecieve(data_buffer, ref len); // len could be changed for transmit actually num of byte that received
                    bw.Write(data_buffer, 0, len);
                    bw.Flush();
                }

            }
            bw.Flush();
            bw.Close();
            bw.Dispose();

        }
        /* 在C#中调用读取数据线程，将数据放入目标文件夹中
         * 返回创建文件的文件名
         * 在Python中调用，返回创建的文件名
         * 可以从文件中读取数据，用于在Python中显示数据
         */
        public string start_acq(string fileDic)
        {
            byte[] cmdBytes = new byte[2];// clear USB fifo
            // start acq cmd is 0x0100;
            cmdBytes[1] = 0x01;
            cmdBytes[0] = 0x00;

            dataAcqTks.Dispose();       //clean up old token source
            dataAcqTks = new CancellationTokenSource(); // generate a new token

            CommandSend(cmdBytes, 2);

            // create file writer
            string fileName = "tempData_" + string.Format("{0:yyyyMMdd_HHHHmmss}", DateTime.Now) + ".dat";
            BinaryWriter bw = new BinaryWriter(File.Open(fileDic + "\\\\" + fileName, FileMode.Append, FileAccess.Write, FileShare.Read));

            // Start data acquision thread
            try
            {
                Task dataAcqTsk = Task.Factory.StartNew(() => this.dataAcq_threadFunc(dataAcqTks.Token, bw), dataAcqTks.Token);
            }
            catch (AggregateException excption)
            {

            }
            return fileName;
        }
        /*停止读取数据线程
         */
        public void stop_acq()
        {
            byte[] cmdBytes = new byte[2];
            // stop acq cmd is 0x0200;
            cmdBytes[1] = 0x02;
            cmdBytes[0] = 0x00;
            CommandSend(cmdBytes, 2);
            dataAcqTks.Cancel();
        }
        /* 读取数据，每次读取512个bytes，然后返回byte数组
         * 具体读取逻辑在python中实现
         * 内部参数可在Python调用，调用dataAcp在Python中实现逻辑
         */
        public byte[] data_buffer;//数据存储处
        public int len;
        public bool bResult;//数据读取返回值
        public byte[] getBuffer()
        {
            return data_buffer;
        }
        public bool dataAcq()
        {
            data_buffer = new byte[512];
            Thread.Sleep(100);
            len = 512;
            bResult = DataRecieve(data_buffer, ref len); // len could be changed for transmit actually num of byte that received
            return bResult;
        }
        //平滑开启高压
        /*为原库代码
         * 在Python中不宜调用此函数，
         * 已在Python中重写，可调用重写代码
         */
        private void HV_set_smooth_threadFunc(CancellationToken token, bool turnOff, bool turnOn)
        {
            decimal target_voltage;
            target_voltage = 50;//it should be rewritten by GUI
                                //           target_voltage = HV_value.Value;
            decimal tmp_v = current_hv;
            if (turnOn)
            {
                hv_switch(true);
            }
            while (Math.Abs(tmp_v - target_voltage) > (decimal)0.2)
            {
                if (token.IsCancellationRequested != true)
                {
                    if (tmp_v < 68)
                    {
                        if (target_voltage > tmp_v)
                            tmp_v += 1;
                        else
                            tmp_v -= 1;
                    }
                    else
                    {
                        if (target_voltage > tmp_v)
                            tmp_v += (decimal)0.1;
                        else
                            tmp_v -= (decimal)0.1;
                    }
                    hv_set(tmp_v);
                    current_hv = tmp_v;
                    Thread.Sleep(500);

                }
                else
                {
                    break;
                }

            }
            if (token.IsCancellationRequested != true)
            {
                hv_set(target_voltage);
            }
            if (turnOff)
            {
                hv_switch(false);
            }

        }//
        //auto electronic calibration, make sure that you have already prepared all registers well
        /*半自动电刻度，
         * 调用时会阻塞1min
         * 返回保存数据的文件名
         * 可以在Python中调用
         */
        private string elecCalib2E(string fileDict)
        {
            //before sc config, do some FPGA logic configurationa first
            int chip_num = 1;
            CommandSend(0x1300 + chip_num, 2);//send chip_num, we only have 1 SP2E.
            CommandSend(0x0c00, 2);//disable external trigger, valid and eraze. {cmd[2],cmd[1],cmd[0]}
            CommandSend(0x0900, 2);//disable flag_tdc_ext.
            CommandSend(0x0e02, 2);//send event_num package
            CommandSend(0x1100, 2);//disable s_curve_count
            CommandSend(0x1500, 2);//Slow clock=5MHz
            CommandSend(0x1600, 2);//Sync signal output every 1000 Slow clock period
            CommandSend(0x1a01, 2);//enable limit acquire
            CommandSend(0x1b03, 2);//mask length (3+1)*25ns
            CommandSend(0x1900, 2);//top level of external trigger,valid and eraze, I disable it here. Enable it by send 0x19e4

            // initiate file writer and dictionary
            BinaryWriter bw;
            DateTime dayStamp = DateTime.Now;
            string subDic = string.Format("{0:yyyyMMdd}_{0:HHmm}_Electronic_Calib", dayStamp);
            string fullPath = fileDict + '\\' + subDic;//jimbook：从GUI中的path窗口里取得文件存储路径
            if (!Directory.Exists(fullPath))
                Directory.CreateDirectory(fullPath);

            // Probe system initiate
            probeConfig.init();
            probeConfig.set_property("8-bit DAC output", 0, 0, 0);
            // set probe/sc setting as probe
            CommandSend(0x0600, 2);
            //the outside loop is on channel
            for (uint chn = 0; chn < 36; chn++)
            {

                //config probe to specific channel
                probeConfig.set_property("8-bit DAC output", chn, 0, 0);
                int byte_count = 0;

                byte[] cmdBytes = new byte[2];
                byte[] bit_block = new byte[1000];  //SPIROC2E has 992 Probe config bit, 992 * 6 / 8 = 744 , need 744 bytes
                probeManager.clearChip();
                for (int i = 0; i < 1; i++)
                {
                    probeManager.pushChip(Copy<Probe_2E>(probeConfig));
                }
                byte_count = probeManager.bit_transform(bit_block);
                // choose data transfer to sc buffer
                cmdBytes[1] = 0x05;
                cmdBytes[0] = 0x01;
                CommandSend(cmdBytes, 2);

                // send config data
                cmdBytes[1] = 0x03;
                for (int i = 0; i < byte_count; i++)
                {
                    cmdBytes[0] = bit_block[i];
                    CommandSend(cmdBytes, 2);
                    //Thread.Sleep(100);
                }

                // close channel of data to sc buffer
                cmdBytes[1] = 0x05;
                cmdBytes[0] = 0x00;

                CommandSend(cmdBytes, 2);

                // start slow config from fpga to asic
                cmdBytes[1] = 0x08;
                cmdBytes[0] = 0x00;
                CommandSend(cmdBytes, 2);
                Thread.Sleep(100);


                // initiate file writter
                string fileName = string.Format("chn{0}.dat", chn);
                //create file writer
                bw = new BinaryWriter(File.Open(fullPath + '\\' + fileName, FileMode.Create, FileAccess.Write, FileShare.Read));
                dataAcqTks.Dispose();       //clean up old token source
                dataAcqTks = new CancellationTokenSource(); // generate a new token
                CommandSend(0x0100, 2); //start acq cycle
                try
                {
                    Task dataAcqTsk = Task.Factory.StartNew(() => this.dataAcq_threadFunc(dataAcqTks.Token, bw), dataAcqTks.Token);
                    Thread.Sleep(500);
                    // time up!
                    // stop asic first
                    CommandSend(0x0200, 2);
                    // stop data receiving
                    dataAcqTks.Cancel();
                    while (!dataAcqTsk.IsCompleted) ;
                }
                catch (AggregateException excption)
                {

                }
            }
            return fullPath;
        }

        //辅助函数
        private static T Copy<T>(T RealObject)
        {
            using (Stream objectStream = new MemoryStream())
            {
                //利用 System.Runtime.Serialization序列化与反序列化完成引用对象的复制     
                IFormatter formatter = new BinaryFormatter();
                formatter.Serialize(objectStream, RealObject);
                objectStream.Seek(0, SeekOrigin.Begin);
                return (T)formatter.Deserialize(objectStream);
            }
        }
        private uint reverse_bit(uint c, uint width)
        {
            // reverse a 6bit width value in bit-wise
            if (width == 6)
            {
                c = (c & 0x24) >> 2 | (c & 0x09) << 2 | (c & 0x12);
                c = (c & 0x38) >> 3 | (c & 0x07) << 3;
            }
            else if (width == 8)
            {
                c = (c & 0xf0) >> 4 | (c & 0x0f) << 4;
                c = (c & 0xcc) >> 2 | (c & 0x33) << 2;
                c = (c & 0xaa) >> 1 | (c & 0x55) << 1;
            }
            return c;
        }
        private uint bin2gray(uint x)
        {
            return x ^ (x >> 1);
        }
        private int uart_send(byte[] cmd, int n)
        {
            //send cmd in c11024_01 form.
            //for example, computer want to Set the temperature correction factor,
            //what I need transport is [ 0x02, 'H' , 'S' , 'T' , '0' , '0', 'A', '1', '0', '0', '0', '1', '0','0','0','0','0','0','0','0', 'C', '8', 'B' ,'E', '9', '7', '2', 'B', 0x03, 'E', '8', 0x0D]
            // n is  27
            // cmd is "HST00A1000100000000C8BE972B", care of case sensitive

            byte[] TempCommand = new byte[2];
            byte checksum = 0;
            byte letter_high = 0;
            byte letter_low = 0;
            //ViStatus status;
            //int return_count = 0;
            //STX signal 0x02.
            TempCommand[1] = 0x03;      //0x05 stand for this is uart-form data
            TempCommand[0] = 0x02;

            CommandSend(TempCommand, 2);

            //if (status != VI_SUCCESS)
            //    return (-1);

            //Sleep(10);


            //what tranmit here is alraedy ascii code, all we need is send it to USB with 0x05
            for (int i = 0; i < n; i++)
            {
                checksum += cmd[i];
                TempCommand[0] = cmd[i];
                CommandSend(TempCommand, 2);

            }


            //ETX signal 0x03
            TempCommand[0] = 0x03;
            CommandSend(TempCommand, 2);



            // sum check
            checksum += 0x05;
            letter_high = toascii((byte)(checksum >> 4));
            letter_low = toascii((byte)(checksum & 0x0F));

            TempCommand[0] = letter_high;
            CommandSend(TempCommand, 2);

            TempCommand[0] = letter_low;
            CommandSend(TempCommand, 2);

            //CR send

            TempCommand[0] = 0x0D;
            CommandSend(TempCommand, 2);
            /*
            status = viWrite(instr, TempCommand, 2, &return_count);

            if (status != VI_SUCCESS)
                return (-1);
                */
            Thread.Sleep(10);

            TempCommand[1] = 0x05;
            TempCommand[0] = 0x02;
            CommandSend(TempCommand, 2);
            /*
            status = viWrite(instr, TempCommand, 2, &return_count);

            if (status != VI_SUCCESS)
                return (-1);
                */
            return (1);

        }
        private byte toascii(byte origin)
        {
            byte ascii_out = 0;
            byte baseline1 = 0x30;
            byte baseline2 = 0x37;
            if (origin < 0x0a)
            {
                ascii_out = (byte)(baseline1 + origin);
            }
            else if (origin < 0x10)
            {
                ascii_out = (byte)(baseline2 + origin);
            }
            else
            {
                return 0;
            }
            return ascii_out;
        }
    }
}
