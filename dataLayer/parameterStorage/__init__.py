import pandas as pd
import os
__path,_ = os.path.split(__file__)
Baseline = pd.read_csv(os.path.join(__path, "baseline_default.csv"), header=0, index_col=0)
Threshold = pd.read_csv(os.path.join(__path, "threshold_default.csv"), header=0, index_col=0)
ChannelReplace = pd.read_csv(os.path.join(__path, "channelReplace_default.csv"), header=0, index_col=0)
DetectorSize = pd.read_csv(os.path.join(__path, "detectorGeometrySize_default.csv"), header=0, index_col=0)
GeometryCoordinateSystem = pd.read_csv(os.path.join(__path, "geometryCoordinateSystem_default.csv"), header=0, index_col=0)
MeanScale = pd.read_csv(os.path.join(__path, "meanScale_default.csv"), header=0, index_col=0)
