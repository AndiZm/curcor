import subprocess
from tqdm import tqdm

# !! Check the telescope paths in subanalysis !!
# They need to be adapted to the used teleescopes

step  = 20
ct1_disk = "Z"
ct3_disk = "E"
ct4_disk = "F"

commands = []

# Baseline 134, Dschubba II
datapath = "20230510_HESS/Dschubba"
start = 1200
end   = 3144
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)
    #commands.append( "python subanalysis2C13.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
    commands.append( "python subanalysis3T.py -s {} -e {} --t1 {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct1_disk, ct3_disk, ct4_disk, datapath) )


for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)