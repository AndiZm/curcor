import simple_rec_fifo_new2 as acquisition
import execute_command as transfer
import numpy as np
import threading

zeroadder = ["0000","0000","000","00","0",""]
def numberstring(x):
    if x == 0:
        nod = 1
    else:
        nod = int(np.log10(x))+1
    return zeroadder[nod] + str(x)

package_size = int(10)

current_numbers = []
storage_places = ["D:\\writetest\\test_", "E:\\writetest\\test_"]

writeid = 0
def change_id():
    global writeid
    if writeid == 0:
        writeid = 1
    elif writeid == 1:
        writeid = 0

start = 0
end = 524

for i in range (start,end+1):
    current_numbers.append(i)
    filename = storage_places[writeid] + numberstring(i) + ".bin"
    print (filename)
    acquisition.measurement(filename)

    if (i+1) % package_size == 0 or i == end:
        copythread = threading.Thread(target=transfer.transfer_files, args=(storage_places[writeid],"Z:\\writetest",current_numbers))
        copythread.start()

        change_id()
        current_numbers = []


acquisition.close()