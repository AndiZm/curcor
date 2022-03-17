# list of all files to evaluate
files = []
# info id relates to the position in the calibration file array for the specific day
info_id = []
# calibration parameters for each day
off_1 = []
off_2 = []
calib_1 = []
calib_2 = []

### 2022-02-23 ###
off_1.append(-1.875039434999999921e-01)
off_2.append(2.796415305000000129e-01)
calib_1.append(-59.111833199224705)
calib_2.append(-67.38270732002343)

for i in range (0,2191):#91
    files.append( "../20220223_roof/sirius_{:05d}.fcorr".format(i) )
    info_id.append(int(0))


### 2022-02-27 ###
off_1.append(-3.603750420000000343e-01)
off_2.append(1.352422540000000062e-01)
calib_1.append(-65.2418293569126)
calib_2.append(-70.77924338810277)

for i in range (0,3670):
    files.append( "../20220227_roof/sirius_{:05d}.fcorr".format(i) )
    info_id.append(int(1))

### 2022-02-28 ###
off_1.append(-2.992445699999999320e-01)
off_2.append(1.731211954999999914e-01)
calib_1.append(-64.1976299649758)
calib_2.append(-72.3535181676592)

for i in range (250,3025):
    files.append( "../20220228_roof/sirius_{:05d}.fcorr".format(i) )
    info_id.append(int(2))

### 2022-03-01 ###
off_1.append(-2.192952975000000138e-01)
off_2.append(1.943128819999999923e-01)
calib_1.append(-64.86034819968731)
calib_2.append(-66.26559787316005)

for i in range (0,2747):
    files.append( "../20220301_roof/sirius_{:05d}.fcorr".format(i) )
    info_id.append(3)

### 2022-03-03 ### CHANGE PARAMETERS
off_1.append(-2.192952975000000138e-01)
off_2.append(1.943128819999999923e-01)
calib_1.append(-64.86034819968731)
calib_2.append(-66.26559787316005)

for i in range (0,2776):
    files.append( "../20220303_roof/sirius_{:05d}.fcorr".format(i) )
    info_id.append(4)