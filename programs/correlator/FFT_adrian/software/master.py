import subprocess
from tqdm import tqdm

step  = 20
ct3_disk = "K"
ct4_disk = "L"

datapath = "20220423_HESS/nunki"

start = 0
end   = 585

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis6.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)