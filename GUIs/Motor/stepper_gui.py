
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import matplotlib.backends.backend_tkagg as tkagg
#import matplotlib.patches as patches


import log as global_log
from tkinter import *
from gui import *
from controller import *

   
log=global_log.log()
controller=CONTROLLER()
root = Tk()
my_gui=GUI(root, controller, position=None, client=None, log=log)
my_gui.run()
root.mainloop()
os._exit(0)

    



