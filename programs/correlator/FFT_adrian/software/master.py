import subprocess
from tqdm import tqdm

ct3_disk = "D"
ct4_disk = "H"
datapath = "20220418_HESS/regor"

start = 0
end   = 1391
step  = 20

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    #commands.append( "python3.9 subanalysis.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)