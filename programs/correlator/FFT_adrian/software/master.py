import subprocess
from tqdm import tqdm

step  = 20
ct3_disk = "K"
ct4_disk = "L"

# Do more ...
datapath = "20220419_HESS/shaula"

start = 349
end   = 352

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)

# Do more ...
datapath = "20220420_HESS/shaula"

start = 3390
end   = 4784

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)

# Do more ...
datapath = "20220421_HESS/shaula"

start = 0
end   = 5574

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)

# Do more ...
datapath = "20220422_HESS/nunki"

start = 0
end   = 3924

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)

# Do more ...
datapath = "20220423_HESS/nunki"

start = 0
end   = 2225

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_AB.py -s {} -e {} --t3 {} --t4 {} -d {}".format(start_send, end_send, ct3_disk, ct4_disk, datapath) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)