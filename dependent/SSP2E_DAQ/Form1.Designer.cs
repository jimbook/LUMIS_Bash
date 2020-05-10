namespace SSP2E_DAQ
{
    partial class Form1
    {
        /// <summary>
        /// 必需的设计器变量。
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// 清理所有正在使用的资源。
        /// </summary>
        /// <param name="disposing">如果应释放托管资源，为 true；否则为 false。</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows 窗体设计器生成的代码

        /// <summary>
        /// 设计器支持所需的方法 - 不要修改
        /// 使用代码编辑器修改此方法的内容。
        /// </summary>
        private void InitializeComponent()
        {
            this.conn_usb = new System.Windows.Forms.Button();
            this.sc_config = new System.Windows.Forms.Button();
            this.probe_config = new System.Windows.Forms.Button();
            this.start_acq = new System.Windows.Forms.Button();
            this.stop_acq = new System.Windows.Forms.Button();
            this.File_path_select_botton = new System.Windows.Forms.Button();
            this.File_path_showbox = new System.Windows.Forms.TextBox();
            this.trig_dac_value = new System.Windows.Forms.TextBox();
            this.TRIG_DAC_label = new System.Windows.Forms.Label();
            this.File_path_label = new System.Windows.Forms.Label();
            this.folderBrowserDialog1 = new System.Windows.Forms.FolderBrowserDialog();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.HV_status = new System.Windows.Forms.Label();
            this.temp_HV = new System.Windows.Forms.Label();
            this.HV_on = new System.Windows.Forms.Button();
            this.HV_off = new System.Windows.Forms.Button();
            this.HV_smooth_btn = new System.Windows.Forms.Button();
            this.auto_ecalib = new System.Windows.Forms.Button();
            this.ecali_status = new System.Windows.Forms.Label();
            this.task_stop = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // conn_usb
            // 
            this.conn_usb.Location = new System.Drawing.Point(70, 71);
            this.conn_usb.Name = "conn_usb";
            this.conn_usb.Size = new System.Drawing.Size(96, 51);
            this.conn_usb.TabIndex = 0;
            this.conn_usb.Text = "conn_usb";
            this.conn_usb.UseVisualStyleBackColor = true;
            this.conn_usb.Click += new System.EventHandler(this.conn_usb_Click);
            // 
            // sc_config
            // 
            this.sc_config.Location = new System.Drawing.Point(70, 137);
            this.sc_config.Name = "sc_config";
            this.sc_config.Size = new System.Drawing.Size(96, 47);
            this.sc_config.TabIndex = 1;
            this.sc_config.Text = "sc_config";
            this.sc_config.UseVisualStyleBackColor = true;
            this.sc_config.Click += new System.EventHandler(this.sc_config_Click);
            // 
            // probe_config
            // 
            this.probe_config.Location = new System.Drawing.Point(70, 206);
            this.probe_config.Name = "probe_config";
            this.probe_config.Size = new System.Drawing.Size(96, 48);
            this.probe_config.TabIndex = 2;
            this.probe_config.Text = "probe_config";
            this.probe_config.UseVisualStyleBackColor = true;
            this.probe_config.Click += new System.EventHandler(this.probe_config_Click);
            // 
            // start_acq
            // 
            this.start_acq.Location = new System.Drawing.Point(70, 276);
            this.start_acq.Name = "start_acq";
            this.start_acq.Size = new System.Drawing.Size(96, 51);
            this.start_acq.TabIndex = 3;
            this.start_acq.Text = "start_acq";
            this.start_acq.UseVisualStyleBackColor = true;
            this.start_acq.Click += new System.EventHandler(this.start_acq_Click);
            // 
            // stop_acq
            // 
            this.stop_acq.Location = new System.Drawing.Point(196, 276);
            this.stop_acq.Name = "stop_acq";
            this.stop_acq.Size = new System.Drawing.Size(87, 51);
            this.stop_acq.TabIndex = 4;
            this.stop_acq.Text = "stop_acq";
            this.stop_acq.UseVisualStyleBackColor = true;
            this.stop_acq.Click += new System.EventHandler(this.stop_acq_Click);
            // 
            // File_path_select_botton
            // 
            this.File_path_select_botton.Location = new System.Drawing.Point(696, 415);
            this.File_path_select_botton.Name = "File_path_select_botton";
            this.File_path_select_botton.Size = new System.Drawing.Size(75, 23);
            this.File_path_select_botton.TabIndex = 5;
            this.File_path_select_botton.Text = "select";
            this.File_path_select_botton.UseVisualStyleBackColor = true;
            this.File_path_select_botton.Click += new System.EventHandler(this.File_path_select_botton_Click);
            // 
            // File_path_showbox
            // 
            this.File_path_showbox.Location = new System.Drawing.Point(115, 415);
            this.File_path_showbox.Name = "File_path_showbox";
            this.File_path_showbox.Size = new System.Drawing.Size(558, 21);
            this.File_path_showbox.TabIndex = 6;
            // 
            // trig_dac_value
            // 
            this.trig_dac_value.Location = new System.Drawing.Point(232, 163);
            this.trig_dac_value.Name = "trig_dac_value";
            this.trig_dac_value.Size = new System.Drawing.Size(70, 21);
            this.trig_dac_value.TabIndex = 7;
            this.trig_dac_value.Text = "251";
            this.trig_dac_value.TextChanged += new System.EventHandler(this.trig_dac_value_TextChanged);
            // 
            // TRIG_DAC_label
            // 
            this.TRIG_DAC_label.AutoSize = true;
            this.TRIG_DAC_label.Location = new System.Drawing.Point(230, 137);
            this.TRIG_DAC_label.Name = "TRIG_DAC_label";
            this.TRIG_DAC_label.Size = new System.Drawing.Size(53, 12);
            this.TRIG_DAC_label.TabIndex = 8;
            this.TRIG_DAC_label.Text = "TRIG_DAC";
            // 
            // File_path_label
            // 
            this.File_path_label.AutoSize = true;
            this.File_path_label.Location = new System.Drawing.Point(50, 420);
            this.File_path_label.Name = "File_path_label";
            this.File_path_label.Size = new System.Drawing.Size(59, 12);
            this.File_path_label.TabIndex = 9;
            this.File_path_label.Text = "File_path";
            // 
            // folderBrowserDialog1
            // 
            this.folderBrowserDialog1.SelectedPath = "C:\\";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(701, 224);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(41, 12);
            this.label2.TabIndex = 12;
            this.label2.Text = "HV_now";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(701, 296);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(41, 12);
            this.label3.TabIndex = 13;
            this.label3.Text = "status";
            // 
            // HV_status
            // 
            this.HV_status.AutoSize = true;
            this.HV_status.Location = new System.Drawing.Point(748, 296);
            this.HV_status.Name = "HV_status";
            this.HV_status.Size = new System.Drawing.Size(23, 12);
            this.HV_status.TabIndex = 14;
            this.HV_status.Text = "off";
            // 
            // temp_HV
            // 
            this.temp_HV.AutoSize = true;
            this.temp_HV.Location = new System.Drawing.Point(754, 224);
            this.temp_HV.Name = "temp_HV";
            this.temp_HV.Size = new System.Drawing.Size(17, 12);
            this.temp_HV.TabIndex = 15;
            this.temp_HV.Text = "xx";
            // 
            // HV_on
            // 
            this.HV_on.Location = new System.Drawing.Point(484, 277);
            this.HV_on.Name = "HV_on";
            this.HV_on.Size = new System.Drawing.Size(82, 50);
            this.HV_on.TabIndex = 16;
            this.HV_on.Text = "HV_on";
            this.HV_on.UseVisualStyleBackColor = true;
            this.HV_on.Click += new System.EventHandler(this.HV_on_Click);
            // 
            // HV_off
            // 
            this.HV_off.Location = new System.Drawing.Point(598, 277);
            this.HV_off.Name = "HV_off";
            this.HV_off.Size = new System.Drawing.Size(75, 50);
            this.HV_off.TabIndex = 17;
            this.HV_off.Text = "HV_off";
            this.HV_off.UseVisualStyleBackColor = true;
            this.HV_off.Click += new System.EventHandler(this.HV_off_Click);
            // 
            // HV_smooth_btn
            // 
            this.HV_smooth_btn.Location = new System.Drawing.Point(484, 206);
            this.HV_smooth_btn.Name = "HV_smooth_btn";
            this.HV_smooth_btn.Size = new System.Drawing.Size(189, 48);
            this.HV_smooth_btn.TabIndex = 18;
            this.HV_smooth_btn.Text = "HV_smooth";
            this.HV_smooth_btn.UseVisualStyleBackColor = true;
            this.HV_smooth_btn.Click += new System.EventHandler(this.HV_smooth_btn_Click);
            // 
            // auto_ecalib
            // 
            this.auto_ecalib.Location = new System.Drawing.Point(484, 71);
            this.auto_ecalib.Name = "auto_ecalib";
            this.auto_ecalib.Size = new System.Drawing.Size(104, 51);
            this.auto_ecalib.TabIndex = 19;
            this.auto_ecalib.Text = "elec_calib_task";
            this.auto_ecalib.UseVisualStyleBackColor = true;
            this.auto_ecalib.Click += new System.EventHandler(this.auto_ecalib_Click);
            // 
            // ecali_status
            // 
            this.ecali_status.AutoSize = true;
            this.ecali_status.Location = new System.Drawing.Point(726, 90);
            this.ecali_status.Name = "ecali_status";
            this.ecali_status.Size = new System.Drawing.Size(29, 12);
            this.ecali_status.TabIndex = 20;
            this.ecali_status.Text = "IDLE";
            // 
            // task_stop
            // 
            this.task_stop.Location = new System.Drawing.Point(598, 71);
            this.task_stop.Name = "task_stop";
            this.task_stop.Size = new System.Drawing.Size(104, 51);
            this.task_stop.TabIndex = 21;
            this.task_stop.Text = "task_stop";
            this.task_stop.UseVisualStyleBackColor = true;
            this.task_stop.Click += new System.EventHandler(this.task_stop_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(800, 450);
            this.Controls.Add(this.task_stop);
            this.Controls.Add(this.ecali_status);
            this.Controls.Add(this.auto_ecalib);
            this.Controls.Add(this.HV_smooth_btn);
            this.Controls.Add(this.HV_off);
            this.Controls.Add(this.HV_on);
            this.Controls.Add(this.temp_HV);
            this.Controls.Add(this.HV_status);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.File_path_label);
            this.Controls.Add(this.TRIG_DAC_label);
            this.Controls.Add(this.trig_dac_value);
            this.Controls.Add(this.File_path_showbox);
            this.Controls.Add(this.File_path_select_botton);
            this.Controls.Add(this.stop_acq);
            this.Controls.Add(this.start_acq);
            this.Controls.Add(this.probe_config);
            this.Controls.Add(this.sc_config);
            this.Controls.Add(this.conn_usb);
            this.Name = "Form1";
            this.Text = "Form1";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button conn_usb;
        private System.Windows.Forms.Button sc_config;
        private System.Windows.Forms.Button probe_config;
        private System.Windows.Forms.Button start_acq;
        private System.Windows.Forms.Button stop_acq;
        private System.Windows.Forms.Button File_path_select_botton;
        private System.Windows.Forms.TextBox File_path_showbox;
        private System.Windows.Forms.TextBox trig_dac_value;
        private System.Windows.Forms.Label TRIG_DAC_label;
        private System.Windows.Forms.Label File_path_label;
        private System.Windows.Forms.FolderBrowserDialog folderBrowserDialog1;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label HV_status;
        private System.Windows.Forms.Label temp_HV;
        private System.Windows.Forms.Button HV_on;
        private System.Windows.Forms.Button HV_off;
        private System.Windows.Forms.Button HV_smooth_btn;
        private System.Windows.Forms.Button auto_ecalib;
        private System.Windows.Forms.Label ecali_status;
        private System.Windows.Forms.Button task_stop;
    }
}

