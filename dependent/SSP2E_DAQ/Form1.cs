using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Reflection;
using CyUSB;
using NationalInstruments.VisaNS;

namespace SSP2E_DAQ
{
    public partial class Form1 : Form
    {
        //about USB
        private USBDeviceList usbDevices;//
        private CyUSBDevice myDevice;//
        private CyBulkEndPoint bulkInEndPt;//
        private CyBulkEndPoint bulkOutEndPt;//
        private bool usbStatus = false;//
        private const int VID = 0x04B4;//
        private const int PID = 0x1004;//

        //store path of data file
        private string fileDic;
        private string fileName;

        //about Slow config
        Iversion slowConfig;
        SC_board_manager slowControlManager = new SC_board_manager();
        SC_board_manager probeManager = new SC_board_manager();
        SC_model_2E slowConfig_2E_1 = new SC_model_2E();

        //about probe_config
        Probe_2E Probe_config = new Probe_2E();

        //default HV set value
        private decimal current_hv = 50;
        private CancellationTokenSource hv_setTks = new CancellationTokenSource();

        //data taking thread
        private CancellationTokenSource dataAcqTks = new CancellationTokenSource();

        //electronic calibration thread
        private CancellationTokenSource specialTaskTks = new CancellationTokenSource();

        //change parameters
        private string rx_Integer = @"^\d+$";   //匹配非负 整数

        //exception report
        private StringBuilder exceptionReport = new StringBuilder();

        public Form1()
        {
            InitializeComponent();
            File_path_showbox.Text = folderBrowserDialog1.SelectedPath;
            fileDic = folderBrowserDialog1.SelectedPath + "\\\\default_test";
            slowControlManager.clearChip();
            slowConfig = slowConfig_2E_1;
        }

        //connect USB
        private void conn_usb_Click(object sender, EventArgs e)
        {
            if (check_USB() != true)
            {
                MessageBox.Show("USB can't be connected", "Error");
            }
        }

        //slow control register config
        private void sc_config_Click(object sender, EventArgs e)
        {
            sc_config_once();
            // show relative message
            File_path_showbox.AppendText("Slow control config successed\n");
        }

        //change parameters ,here is an example. Use "set_property" method to change others like this
        private void trig_dac_value_TextChanged(object sender, EventArgs e)
        {
            uint value = 0;
            Regex rx_int = new Regex(rx_Integer);

            // check input valid
            if (rx_int.IsMatch(trig_dac_value.Text))
            {
                value = uint.Parse(trig_dac_value.Text);
                if (0 <= value && value <= 1023)
                {
                    slowConfig.set_property(slowConfig.settings["TRIG_DAC"], value);
                    return;
                }
            }
            MessageBox.Show("value need be in range of 0-1023", "Value invalid");
        }

        //file save
        private void File_path_select_botton_Click(object sender, EventArgs e)
        {
            folderBrowserDialog1.ShowDialog();
            fileDic = folderBrowserDialog1.SelectedPath;
            File_path_showbox.Text = fileDic;
        }

        //probe config to enable
        private void probe_config_Click(object sender, EventArgs e)
        {
            var ana_p = "Out PA HG/Out PA LG";//or "Threshold" or "Out fs" or "Out ramp TDC"
            Probe_config.init();
            uint ana_p_chn = (uint) 1;        
            uint gain = (uint) 1;// 1 for HG, 0 for LG
            Probe_config.set_property(ana_p, ana_p_chn, 0, gain);
            probe_config_once();
        }

        //HV smooth botton
        private void HV_smooth_btn_Click(object sender, EventArgs e)
        {
            hv_setTks.Cancel();
            hv_setTks.Dispose();       //clean up old token source
            hv_setTks = new CancellationTokenSource(); // generate a new token
            if (check_USB() == false)
            {
                MessageBox.Show("USB or Instrument is not connected", "Error");
                return;
            }

            if (usbStatus == true)


                try
                {
                    Task hv_setting = Task.Factory.StartNew(() => this.HV_set_smooth_threadFunc(hv_setTks.Token, false, false), hv_setTks.Token);

                }
                catch (AggregateException excption)
                {

                    foreach (var v in excption.InnerExceptions)
                    {

                        exceptionReport.AppendLine(excption.Message + " " + v.Message);
                    }

                }
        }

        //HV on
        private void HV_on_Click(object sender, EventArgs e)
        {
            if (check_USB() == false)
            {
                MessageBox.Show("USB or Instrument is not connected", "Error");
                return;
            }
            hv_switch(true);
            HV_status.Text = "ON";
            HV_on.Enabled = false;
            HV_off.Enabled = true;
        }

        private void HV_off_Click(object sender, EventArgs e)
        {
            try
            {
                hv_setTks.Cancel();
                hv_setTks.Dispose();       //clean up old token source
                hv_setTks = new CancellationTokenSource(); // generate a new token
                //HV_value.Value = 50;
                Task hv_setting = Task.Factory.StartNew(() => this.HV_set_smooth_threadFunc(hv_setTks.Token, true, false), hv_setTks.Token);

            }
            catch (AggregateException excption)
            {

                foreach (var v in excption.InnerExceptions)
                {

                    exceptionReport.AppendLine(excption.Message + " " + v.Message);
                }

            }
            HV_status.Text = "OFF";
            HV_on.Enabled = true;
            HV_off.Enabled = false;
        }

        //start acq botton
        private void start_acq_Click(object sender, EventArgs e)
        {
            byte[] cmdBytes = new byte[2];// clear USB fifo
            // start acq cmd is 0x0100;
            cmdBytes[1] = 0x01;
            cmdBytes[0] = 0x00;

            dataAcqTks.Dispose();       //clean up old token source
            dataAcqTks = new CancellationTokenSource(); // generate a new token

            CommandSend(cmdBytes, 2);
            // check USB status
            if (usbStatus == false)
            {
                MessageBox.Show("USB is not connected");
            }

            // create file writer
            fileName = string.Format("{0:yyyyMMdd_HHHHmmss}", DateTime.Now) + ".dat";
            if (!Directory.Exists(fileDic))
            {
                Directory.CreateDirectory(fileDic);
            }

            BinaryWriter bw = new BinaryWriter(File.Open(fileDic + "\\\\" + fileName, FileMode.Append, FileAccess.Write, FileShare.Read));

            // Start data acquision thread
            try
            {
                Task dataAcqTsk = Task.Factory.StartNew(() => this.dataAcq_threadFunc(dataAcqTks.Token, bw), dataAcqTks.Token);
            }
            catch (AggregateException excption)
            {

                foreach (var v in excption.InnerExceptions)
                {

                    exceptionReport.AppendLine(excption.Message + " " + v.Message);
                }

            }
            stop_acq.Enabled = true;
            start_acq.Enabled = false;
        }

        //stop acq botton
        private void stop_acq_Click(object sender, EventArgs e)
        {
            byte[] cmdBytes = new byte[2];

            // start acq cmd is 0x0200;
            cmdBytes[1] = 0x02;
            cmdBytes[0] = 0x00;

            CommandSend(cmdBytes, 2);

            // check USB status
            if (usbStatus == false)
            {
                MessageBox.Show("USB is not connected");
            }
            dataAcqTks.Cancel();


            start_acq.Enabled = true;
            stop_acq.Enabled = false;
        }

        //ecali task botton
        private void auto_ecalib_Click(object sender, EventArgs e)
        {
            specialTaskTks.Dispose();       //clean up old token source
            specialTaskTks = new CancellationTokenSource(); // generate a new token
            if (check_USB() == false)
            {
                MessageBox.Show("USB or Instrument is not connected", "Error");
                return;
            }
            if (usbStatus == true)
                try
                {
                    Task voltageSweepTask = Task.Factory.StartNew(() => this.elecCalib2E_threadFunc(specialTaskTks.Token), specialTaskTks.Token);

                }
                catch (AggregateException excption)
                {

                    foreach (var v in excption.InnerExceptions)
                    {

                        exceptionReport.AppendLine(excption.Message + " " + v.Message);
                    }

                }
            ecali_status.Text = "Elec. Calibrating";
            ecali_status.ForeColor = Color.Green;
            auto_ecalib.Enabled = false;
            task_stop.Enabled = true;
        }

        //task stop botton
        private void task_stop_Click(object sender, EventArgs e)
        {
            specialTaskTks.Cancel();
            ecali_status.Text = "IDLE";
            ecali_status.ForeColor = Color.Black;
            auto_ecalib.Enabled = true;
            task_stop.Enabled = false;
        }
    }
}
