using CyUSB;
using NationalInstruments.VisaNS;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using System.Threading.Tasks;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Formatters.Binary;

namespace SSP2E_DAQ
{
    partial class Form1
    {
        //user functions



        //connect and check usb function，user can add some labels on GUI to indicate the USB connecting status
        private bool check_USB()
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
        }//
        //auto electronic calibration, make sure that you have already prepared all registers well
        private void elecCalib2E_threadFunc(CancellationToken taskToken)
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
            string fullPath = folderBrowserDialog1.SelectedPath + '\\' + subDic;//jimbook：从GUI中的path窗口里取得文件存储路径
            if (!Directory.Exists(fullPath))
                Directory.CreateDirectory(fullPath);

            // Probe system initiate
            Probe_config.init();
            Probe_config.set_property("8-bit DAC output", 0, 0, 0);
            // set probe/sc setting as probe
            CommandSend(0x0600, 2);
            //the outside loop is on channel
            for (uint chn = 0; chn < 36; chn++)
            {

                //config probe to specific channel
                Probe_config.set_property("8-bit DAC output", chn, 0, 0);
                int byte_count = 0;

                byte[] cmdBytes = new byte[2];
                byte[] bit_block = new byte[1000];  //SPIROC2E has 992 Probe config bit, 992 * 6 / 8 = 744 , need 744 bytes
                probeManager.clearChip();
                for (int i = 0; i < 1; i++)
                {
                        probeManager.pushChip(Copy<Probe_2E>(Probe_config));  
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
                        foreach (var value in excption.InnerExceptions)
                        {
                            exceptionReport.AppendLine(excption.Message + " " + value.Message);
                        }
                    }
            }
            MessageBox.Show("eletronic calibration is completed, please stop it");
        }

        //slow control configuration function, use it after that you have changed all the parameters for your application
        private void sc_config_once()
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
                slowConfigTmpChain2E.Add(Copy<SC_model_2E>(slowConfig_2E_1));
                slowConfigTmpChain2E[i].set_property(slowConfig_2E_1.settings["CHIPID"], reverse_bit(bin2gray(1), 8));  // the last chip config first
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
        }//

        //Probe configuration function
        private void probe_config_once()
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
                probeManager.pushChip(Copy<Probe_2E>(Probe_config));    
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

        }//

        //HV_set_smooth_threadFunc
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
                    temp_HV.Text = tmp_v.ToString();
                    temp_HV.ForeColor = Color.Black;
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
                temp_HV.Text = target_voltage.ToString();
                temp_HV.ForeColor = Color.Green;
            }
            if (turnOff)
            {
                hv_switch(false);
            }

        }//
        
        //HV ON/OFF function
        void hv_switch(bool turnOn)
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
        }//

        //command sending method
        private bool CommandSend(byte[] OutData, int xferLen)
        {
            bool bResult = false;
            if (bulkOutEndPt == null)
            {
                bResult = false;
            }
            else
            {
                bResult = bulkOutEndPt.XferData(ref OutData, ref xferLen);
            }
            return bResult;
        }//

        //data recieve method
        private bool DataRecieve(byte[] InData, ref int xferLen)
        {
            bool bResult;
            bResult = bulkInEndPt.XferData(ref InData, ref xferLen, true);
            return bResult;
        }//

        //data taking thread function
        private void dataAcq_threadFunc(CancellationToken token, BinaryWriter bw)
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
                        //bw.Close();
                        //bw.Dispose();
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

        }//





        //following functions are not user functions in fact, but I just put them here.
        public static T Copy<T>(T RealObject)
        {
            using (Stream objectStream = new MemoryStream())
            {
                //利用 System.Runtime.Serialization序列化与反序列化完成引用对象的复制     
                IFormatter formatter = new BinaryFormatter();
                formatter.Serialize(objectStream, RealObject);
                objectStream.Seek(0, SeekOrigin.Begin);
                return (T)formatter.Deserialize(objectStream);
            }
        }//
        uint reverse_bit(uint c, uint width)
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
        }//
        uint bin2gray(uint x)
        {
            return x ^ (x >> 1);
        }//

        private bool CommandSend(int Outdata, int xferLen)
        {
            bool bResult = false;
            byte[] cmdbytes = new byte[2];
            cmdbytes[0] = (byte)Outdata;
            cmdbytes[1] = (byte)(Outdata >> 8);
            if (bulkOutEndPt == null)
            {
                bResult = false;
            }
            else
            {
                bResult = bulkOutEndPt.XferData(ref cmdbytes, ref xferLen);
            }
            return bResult;
        }//

        //HV
        void hv_set(decimal voltage)
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
        }//
        int uart_send(byte[] cmd, int n)
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

        }//
        byte toascii(byte origin)
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
        }//

    }
}