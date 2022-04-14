import subprocess
from tqdm import tqdm

start = 0
end   = 2775
step  = 20

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python.exe subanalysis.py -s {} -e {}".format(start_send, end_send) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i])