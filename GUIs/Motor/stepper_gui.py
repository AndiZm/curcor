
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import matplotlib.backends.backend_tkagg as tkagg
#import matplotlib.patches as patches

from tkinter import *
from gui import *
from controller import *

   
controller=CONTROLLER()
root = Tk()
my_gui=GUI(root,controller)
my_gui.run()
root.mainloop()
os._exit(0)

    



