import subprocess
from tqdm import tqdm

start = 0
end   = 500
step  = 20

commands = []
index = start
while index < end+1:
    start_send = index
    index += step
    end_send   = min(index, end+1)

    commands.append( "python3.9 subanalysis_auto_acrux.py -s {} -e {}".format(start_send, end_send) )
    commands.append( "python3.9 subanalysis_auto_acrux_motoron.py -s {} -e {}".format(start_send, end_send) )
    commands.append( "python3.9 subanalysis_auto_halogen.py -s {} -e {}".format(start_send, end_send) )
for i in tqdm(range(len(commands))):
    subprocess.run(commands[i], shell=True)