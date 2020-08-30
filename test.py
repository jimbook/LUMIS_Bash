import re
import os
for root,dirs,files in os.walk('C:\\Users\\jimbook\\Desktop\\缪子\\test_SP2E_USTC'):
    for file in files:
        r = re.match(r'^Test_SP2E_BGA_FRA 703-\d+.data$',file)
        if r is not None:
            with open(os.path.join(root,file),'r') as f:
                readBuff = f.read()
            with open(os.path.join('./dependence/CalibrationData',file),'w') as f:
                f.write(readBuff)
            print(file)
