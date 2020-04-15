import sys
dll_path = r".//dependent"
sys.path.append(dll_path)
import clr
clr.AddReference("DAQ_IO")
from DAQ_IO_DLL import SC_board_manager
SC = SC_board_manager()
SC.clearChip()
print(SC.chip_num)



