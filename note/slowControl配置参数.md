|                               |                 |      |
| ----------------------------- | --------------- | ---- |
| conn_usb_Click                | 连接USB         |      |
| sc_config_Click               | 配置slowControl |      |
| trig_dac_value_TextChanged    | 示例修改配置    |      |
| File_path_select_botton_Click | 选择存储路径    |      |
| probe_config_Click            | 配置probe       |      |
| HV_smooth_btn_Click           | 缓慢配置高压    |      |
| HV_on_Click                   | 打开高压        |      |
| HV_off_Click                  | 关闭高压        |      |
| start_acq_Click               |                 |      |
| task_stop_Click               |                 |      |
| auto_ecalib_Click             |                 |      |
| task_stop_Click               |                 |      |

## slowControl配置参数

|                     |        |                                                |              |
| ------------------- | ------ | ---------------------------------------------- | ------------ |
| TRIG_DAC            | 10bits |                                                |              |
| DISCRIMINATOR_MASK1 | 18bits | 控制 SP2E 的 channel 35~18 的 trigger 是否有效 | 0有效，1无效 |
| DISCRIMINATOR_MASK2 | 18bits | 控制 SP2E 的 channel 17~0 的 trigger 是否有效  |              |
| PROBE_OTA           | 1bit   | 使用 analogue probe 前需要置 1                 | 默认为 0     |
| EN_OR36             | 1bit   | 使能（置 1）36 路通道的触发或输出              |              |
| AUTO_GAIN           | 1bit   |                                                | 默认为0      |
| GAIN_SELECT         | 1bit   |                                                | 默认为0      |
| ADC_EXT_INPUT       | 1bit   |                                                | 默认为0      |
| SWITCH_TDC_ON       | 1bit   |                                                | 默认为1      |

