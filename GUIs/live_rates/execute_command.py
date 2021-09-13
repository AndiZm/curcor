import os
import numpy as np

zeroadder = ["0000","0000","000","00","0",""]
def numberstring(x):
    if x == 0:
        nod = 1
    else:
        nod = int(np.log10(x))+1
    return zeroadder[nod] + str(x)

copystring = "C:\\Users\\ii\\FastCopy\\FastCopy.exe /no_ui "

def transfer_files (sourcepath, destinationpath, numbers):
    print ("*** Transfer files: Start copying")
    execute_string = copystring
    for i in numbers:
        execute_string += sourcepath + numberstring(i) + ".bin "
    
    execute_string += "/to=" + destinationpath
    
    os.system(execute_string)
    print ("*** Transfer files: finished copying")
    
    for i in numbers:
        os.system("del " + sourcepath + numberstring(i) + ".bin")
    print ("*** Transfer files: finished clearing")