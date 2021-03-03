import telnetlib
import time
import hv_glob as gl
import hv_commands as com
from tkinter import *
from threading import Thread


gl.vset = [com.get_vset(0),com.get_vset(1),com.get_vset(2),com.get_vset(3)]
com.apply_ratio_0()
com.apply_ratio_2()
gl.vmon = [com.get_vmon(0),com.get_vmon(1),com.get_vmon(2),com.get_vmon(3)]

gl.root = Tk()
rootExitFrame=Frame(gl.root); rootExitFrame.grid(row=0,column=0)
def exit():
	gl.mon_thread = False
ExitButton = Button(rootExitFrame, text="Close", command=exit); ExitButton.grid(row=0,column=0)
gl.frameLabel = Label(rootExitFrame, text=str(gl.scheck)); gl.frameLabel.grid(row=0, column=1)
rootMainFrame = Frame(gl.root); rootMainFrame.grid(row=1,column=0)
gl.hv0Button = Button(rootMainFrame, text="HV 0", font=("Helvetica 12 bold"), bg="grey", command=com.toggle_0); gl.hv0Button.grid(row=0,column=2)
gl.hv1Label = Label(rootMainFrame, text="HV 1", font=("Helvetica 8 italic"), bg="grey"); gl.hv1Label.grid(row=0,column=3)
gl.hv2Button = Button(rootMainFrame, text="HV 2", font=("Helvetica 12 bold"), bg="grey", command=com.toggle_2); gl.hv2Button.grid(row=0,column=4)
gl.hv3Label = Label(rootMainFrame, text="HV 3", font=("Helvetica 8 italic"), bg="grey"); gl.hv3Label.grid(row=0,column=5)

# Init on or off
if com.get_status(0) == 1:
	gl.hv0Button.config(bg="orange")
	gl.hv1Label.config(bg="orange")
	gl.status0 = True
if com.get_status(2) == 1:
	gl.hv2Button.config(bg="orange")
	gl.hv3Label.config(bg="orange")
	gl.status2 = True


# Ratio between HV and Booster
def change_ratio():
	cr = Tk()
	cr_label01 = Label(cr, text="Ratio 0/1"); cr_label01.grid(row=0,column=0)
	cr_label23 = Label(cr, text="Ratio 2/3"); cr_label23.grid(row=0,column=1)
	cr_entry01 = Entry(cr, width=5); cr_entry01.grid(row=1,column=0); cr_entry01.insert(0,str(gl.ratio01))
	cr_entry23 = Entry(cr, width=5); cr_entry23.grid(row=1,column=1); cr_entry23.insert(0,str(gl.ratio23))
	def apply_ratio():
		gl.ratio01 = float(cr_entry01.get()); gl.ratio23 = float(cr_entry23.get())
		com.apply_ratio_0(); com.apply_ratio_2()
		cr.destroy()
	cr_Button = Button(cr, text="Apply", command=apply_ratio); cr_Button.grid(row=1,column=2)
ratioButton = Button(rootMainFrame, text="Ratio",command=change_ratio); ratioButton.grid(row=0,column=0)

# Set Voltage
def change_vSet():
	cvset = Tk()
	cvset_label0 = Label(cvset, text="HV 0"); cvset_label0.grid(row=0,column=0)
	cvset_label2 = Label(cvset, text="HV 2"); cvset_label2.grid(row=0,column=1)
	cvset_entry0 = Entry(cvset, width=5); cvset_entry0.grid(row=1,column=0); cvset_entry0.insert(0,str(gl.vset[0]))
	cvset_entry2 = Entry(cvset, width=5); cvset_entry2.grid(row=1,column=1); cvset_entry2.insert(0,str(gl.vset[2]))
	def apply_vSet():
		com.safe_vset_0(float(cvset_entry0.get())); com.safe_vset_2(float(cvset_entry2.get()))
		cvset.destroy()
	cvset_Button = Button(cvset, text="Apply", command=apply_vSet); cvset_Button.grid(row=1,column=2)
#vSetLabel = Label(rootMainFrame, text="V-Set"); vSetLabel.grid(row=2,column=0)
vSetButton = Button(rootMainFrame, text="V-Set",command=change_vSet); vSetButton.grid(row=2,column=0)
gl.vSet0Label = Label(rootMainFrame, width=5, text=str(gl.vset[0]), bg="black", fg="orange"); gl.vSet0Label.grid(row=2,column=2)
gl.vSet1Label = Label(rootMainFrame, width=4, text=str(gl.vset[1]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet1Label.grid(row=2,column=3)
gl.vSet2Label = Label(rootMainFrame, width=5, text=str(gl.vset[2]), bg="black", fg="orange"); gl.vSet2Label.grid(row=2,column=4)
gl.vSet3Label = Label(rootMainFrame, width=4, text=str(gl.vset[3]), font=("Helvetica 7"), bg="light grey", fg="black"); gl.vSet3Label.grid(row=2,column=5)

# MON Voltage
vMonLabel = Label(rootMainFrame, text ="V-Mon"); vMonLabel.grid(row=3,column=0)

gl.vMon0Label = Label(rootMainFrame, width=5, text=str(gl.vmon0), bg="black", fg="red"); gl.vMon0Label.grid(row=3,column=2)
gl.vMon1Label = Label(rootMainFrame, width=4, text=str(gl.vmon1), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon1Label.grid(row=3,column=3)
gl.vMon2Label = Label(rootMainFrame, width=5, text=str(gl.vmon2), bg="black", fg="red"); gl.vMon2Label.grid(row=3,column=4)
gl.vMon3Label = Label(rootMainFrame, width=4, text=str(gl.vmon3), font=("Helvetica 7"), bg="light grey", fg="red"); gl.vMon3Label.grid(row=3,column=5)

# MON Current
iMonLabel = Label(rootMainFrame, text ="I-Mon (mA)"); iMonLabel.grid(row=4,column=0)

gl.iMon0Label = Label(rootMainFrame, width=5, text="{:.2f}".format(com.get_imon(0)), font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon0Label.grid(row=4,column=2)
gl.iMon1Label = Label(rootMainFrame, width=4, text="{:.2f}".format(com.get_imon(1)), font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon1Label.grid(row=4,column=3)
gl.iMon2Label = Label(rootMainFrame, width=5, text="{:.2f}".format(com.get_imon(2)), font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon2Label.grid(row=4,column=4)
gl.iMon3Label = Label(rootMainFrame, width=4, text="{:.2f}".format(com.get_imon(3)), font=("Helvetica 7"), bg="light grey", fg="red"); gl.iMon3Label.grid(row=4,column=5)



com.start_monitor()

gl.root.mainloop()




print ("Done")