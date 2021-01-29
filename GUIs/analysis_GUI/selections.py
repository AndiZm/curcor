import globs as gl
import tkFileDialog as filedialog
from os import listdir
from os.path import isfile, join
import numpy as np
import os
import tkFileDialog as filedialog

def selectBodyFile_sig():
	filename = filedialog.askopenfilename(initialdir=gl.basicpath_sig, title="Select any signal file", filetypes=(("correlation files", "*.corr"),("all files","*.*")))
	gl.body_sig = filename[:filename.find(".")-6]
	gl.basicpath_sig = gl.body_sig.rpartition("/")[0] + "/"
	gl.bodySigLabel.config(text=gl.body_sig.split("/")[-1])
	allfilesSig = [f for f in listdir(gl.basicpath_sig) if (isfile(join(gl.basicpath_sig, f)) and f.startswith(gl.body_sig.split("/")[-1]))]; allfilesSig.sort()
	beg = int(allfilesSig[0].split("_")[-1].split(".")[0])
	end = int(allfilesSig[-1].split("_")[-1].split(".")[0])
	gl.begSigEntry.delete(0,'end'); gl.begSigEntry.insert(0,str(beg))
	gl.endSigEntry.delete(0,'end'); gl.endSigEntry.insert(0,str(end))
	gl.boolSig = True
	selectSigCalib(); selectSigOffset()
def selectBodyFile_ref():
	filename = filedialog.askopenfilename(initialdir=gl.basicpath_ref, title="Select any signal file", filetypes=(("correlation files", "*.corr"),("all files","*.*")))
	gl.body_ref = filename[:filename.find(".")-6]
	gl.basicpath_ref = gl.body_ref.rpartition("/")[0] + "/"
	gl.bodyRefLabel.config(text=gl.body_ref.split("/")[-1])
	allfilesRef = [f for f in listdir(gl.basicpath_ref) if (isfile(join(gl.basicpath_ref, f)) and f.startswith(gl.body_ref.split("/")[-1]))]; allfilesRef.sort()
	beg = int(allfilesRef[0].split("_")[-1].split(".")[0])
	end = int(allfilesRef[-1].split("_")[-1].split(".")[0])
	gl.begRefEntry.delete(0,'end'); gl.begRefEntry.insert(0,beg)
	gl.endRefEntry.delete(0,'end'); gl.endRefEntry.insert(0,end)
	gl.boolRef = True
	selectRefCalib(); selectRefOffset()
def delSigFiles():
	gl.bodySigLabel.config(text="no files selected")
	gl.begSigEntry.delete(0,'end')
	gl.endSigEntry.delete(0,'end')
	gl.offSigLabel.config(text="No off selected")
	gl.calibSigLabel.config(text="No calib selected")
	gl.offASigLabel.config(text="--"); gl.offBSigLabel.config(text="--")
	gl.avgChargeASigLabel.config(text="--"); gl.avgChargeBSigLabel.config(text="--")
	gl.corrSigEntry.delete(0,'end'); gl.corrSigEntry.insert(0,"1")
	gl.boolSig = False
def delRefFiles():
	gl.bodyRefLabel.config(text="no files selected")
	gl.begRefEntry.delete(0,'end'); gl.endRefEntry.delete(0,'end')
	gl.offRefLabel.config(text="No off selected")
	gl.calibRefLabel.config(text="No calib selected")
	gl.offARefLabel.config(text="--"); gl.offBRefLabel.config(text="--")
	gl.avgChargeARefLabel.config(text="--"); gl.avgChargeBRefLabel.config(text="--")
	gl.corrRefEntry.delete(0,'end'); gl.corrRefEntry.insert(0,"1")
	gl.boolRef = False

### Calibration files ###
def selectSigCalib():
	filename = filedialog.askopenfilename(initialdir = gl.basicpath_sig+"/calibs", title = "Load calibration", filetypes = (("calib files",".calib"),("all files",".*")))
	calibLoad = filename; gl.calibSigLabel.config(text=calibLoad.split("/")[-1])
	gl.histo_x_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,0]; gl.histo_a_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,1]; gl.histo_b_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,2]
	gl.ps_x_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,0]; gl.ps_a_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,1]; gl.ps_b_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,2]
	gl.xplot_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot")
	gl.pa_sig[0] = np.loadtxt(calibLoad)[0]; gl.pa_sig[1] = np.loadtxt(calibLoad)[1]; gl.pa_sig[2] = np.loadtxt(calibLoad)[2]
	gl.pb_sig[0] = np.loadtxt(calibLoad)[3]; gl.pb_sig[1] = np.loadtxt(calibLoad)[4]; gl.pb_sig[2] = np.loadtxt(calibLoad)[5]
	gl.nsum_a_sig = np.loadtxt(calibLoad)[6]; gl.nsum_b_sig = np.loadtxt(calibLoad)[7]
	gl.ph_a_sig = np.loadtxt(calibLoad)[8]; gl.ph_b_sig = np.loadtxt(calibLoad)[9]
	gl.avg_charge_a_sig = np.loadtxt(calibLoad)[10]; gl.avg_charge_b_sig = np.loadtxt(calibLoad)[11]
	gl.avgChargeASigLabel.config(text="{:.3f}".format(gl.avg_charge_a_sig)); gl.avgChargeBSigLabel.config(text="{:.3f}".format(gl.avg_charge_b_sig))
def selectSigCalib_concrete(filename):
	calibLoad = filename; gl.calibSigLabel.config(text=calibLoad.split("/")[-1])
	gl.histo_x_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,0]; gl.histo_a_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,1]; gl.histo_b_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,2]
	gl.ps_x_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,0]; gl.ps_a_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,1]; gl.ps_b_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,2]
	gl.xplot_sig = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot")
	gl.pa_sig[0] = np.loadtxt(calibLoad)[0]; gl.pa_sig[1] = np.loadtxt(calibLoad)[1]; gl.pa_sig[2] = np.loadtxt(calibLoad)[2]
	gl.pb_sig[0] = np.loadtxt(calibLoad)[3]; gl.pb_sig[1] = np.loadtxt(calibLoad)[4]; gl.pb_sig[2] = np.loadtxt(calibLoad)[5]
	gl.nsum_a_sig = np.loadtxt(calibLoad)[6]; gl.nsum_b_sig = np.loadtxt(calibLoad)[7]
	gl.ph_a_sig = np.loadtxt(calibLoad)[8]; gl.ph_b_sig = np.loadtxt(calibLoad)[9]
	gl.avg_charge_a_sig = np.loadtxt(calibLoad)[10]; gl.avg_charge_b_sig = np.loadtxt(calibLoad)[11]
	gl.avgChargeASigLabel.config(text="{:.3f}".format(gl.avg_charge_a_sig)); gl.avgChargeBSigLabel.config(text="{:.3f}".format(gl.avg_charge_b_sig))

def selectRefCalib():
	filename = filedialog.askopenfilename(initialdir = gl.basicpath_ref+"/calibs", title = "Load calibration", filetypes = (("calib files",".calib"),("all files",".*")))
	calibLoad = filename; gl.calibRefLabel.config(text=calibLoad.split("/")[-1])
	gl.histo_x_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,0]; gl.histo_a_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,1]; gl.histo_b_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,2]
	gl.ps_x_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,0]; gl.ps_a_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,1]; gl.ps_b_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,2]
	gl.xplot_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot")
	gl.pa_ref[0] = np.loadtxt(calibLoad)[0]; gl.pa_ref[1] = np.loadtxt(calibLoad)[1]; gl.pa_ref[2] = np.loadtxt(calibLoad)[2]
	gl.pb_ref[0] = np.loadtxt(calibLoad)[3]; gl.pb_ref[1] = np.loadtxt(calibLoad)[4]; gl.pb_ref[2] = np.loadtxt(calibLoad)[5]
	gl.nsum_a_ref = np.loadtxt(calibLoad)[6]; gl.nsum_b_ref = np.loadtxt(calibLoad)[7]
	gl.ph_a_ref = np.loadtxt(calibLoad)[8]; gl.ph_b_ref = np.loadtxt(calibLoad)[9]
	gl.avg_charge_a_ref = np.loadtxt(calibLoad)[10]; gl.avg_charge_b_ref = np.loadtxt(calibLoad)[11]
	gl.avgChargeARefLabel.config(text="{:.3f}".format(gl.avg_charge_a_ref)); gl.avgChargeBRefLabel.config(text="{:.3f}".format(gl.avg_charge_b_ref))
def selectRefCalib_concrete(filename):
	calibLoad = filename; gl.calibRefLabel.config(text=calibLoad.split("/")[-1])
	gl.histo_x_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,0]; gl.histo_a_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,1]; gl.histo_b_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".phd")[:,2]
	gl.ps_x_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,0]; gl.ps_a_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,1]; gl.ps_b_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".shape")[:,2]
	gl.xplot_ref = np.loadtxt(calibLoad[0:calibLoad.find(".")]+".xplot")
	gl.pa_ref[0] = np.loadtxt(calibLoad)[0]; gl.pa_ref[1] = np.loadtxt(calibLoad)[1]; gl.pa_ref[2] = np.loadtxt(calibLoad)[2]
	gl.pb_ref[0] = np.loadtxt(calibLoad)[3]; gl.pb_ref[1] = np.loadtxt(calibLoad)[4]; gl.pb_ref[2] = np.loadtxt(calibLoad)[5]
	gl.nsum_a_ref = np.loadtxt(calibLoad)[6]; gl.nsum_b_ref = np.loadtxt(calibLoad)[7]
	gl.ph_a_ref = np.loadtxt(calibLoad)[8]; gl.ph_b_ref = np.loadtxt(calibLoad)[9]
	gl.avg_charge_a_ref = np.loadtxt(calibLoad)[10]; gl.avg_charge_b_ref = np.loadtxt(calibLoad)[11]
	gl.avgChargeARefLabel.config(text="{:.3f}".format(gl.avg_charge_a_ref)); gl.avgChargeBRefLabel.config(text="{:.3f}".format(gl.avg_charge_b_ref))

### Offset files ###
def selectSigOffset():
	filename = filedialog.askopenfilename(initialdir=gl.basicpath_sig+"/calibs", title="Select offset file", filetypes=(("offset files", "*.off"),("all files","*.*")))
	gl.offset_a_sig = np.loadtxt(filename)[0]; gl.offset_b_sig = np.loadtxt(filename)[1]
	gl.offSigLabel.config(text=filename.split("/")[-1])
	gl.offASigLabel.config(text="{:.3f}".format(gl.offset_a_sig)); gl.offBSigLabel.config(text="{:.3f}".format(gl.offset_b_sig))
def selectSigOffset_concrete(filename):
	gl.offset_a_sig = np.loadtxt(filename)[0]; gl.offset_b_sig = np.loadtxt(filename)[1]
	gl.offSigLabel.config(text=filename.split("/")[-1])
	gl.offASigLabel.config(text="{:.3f}".format(gl.offset_a_sig)); gl.offBSigLabel.config(text="{:.3f}".format(gl.offset_b_sig))

def selectRefOffset():
	filename = filedialog.askopenfilename(initialdir=gl.basicpath_ref+"/calibs", title="Select offset file", filetypes=(("offset files", "*.off"),("all files","*.*")))
	gl.offset_a_ref = np.loadtxt(filename)[0]; gl.offset_b_ref = np.loadtxt(filename)[1]
	gl.offRefLabel.config(text=filename.split("/")[-1])
	gl.offARefLabel.config(text="{:.3f}".format(gl.offset_a_ref)); gl.offBRefLabel.config(text="{:.3f}".format(gl.offset_b_ref))
def selectRefOffset_concrete(filename):
	gl.offset_a_ref = np.loadtxt(filename)[0]; gl.offset_b_ref = np.loadtxt(filename)[1]
	gl.offRefLabel.config(text=filename.split("/")[-1])
	gl.offARefLabel.config(text="{:.3f}".format(gl.offset_a_ref)); gl.offBRefLabel.config(text="{:.3f}".format(gl.offset_b_ref))


# Configurations
def save_config():
	if not os.path.exists("configs"):
		os.mkdir("configs")
	savename = filedialog.asksaveasfilename(defaultextension=".config", filetypes=[("config files","*.config")], initialdir="configs", title="Choose filename")
	with open(savename, "w") as f:
		# Signal
		f.write("boolSig\t{}\n".format(gl.boolSig))
		f.write("basicpath\t" + gl.basicpath_sig + "\n")
		f.write("body\t" + gl.body_sig + "\n")
		f.write("beg\t" + gl.begSigEntry.get() + "\n")
		f.write("end\t" + gl.endSigEntry.get() + "\n")
		f.write("calibFile\t" + gl.basicpath_sig + "calibs/" + gl.calibSigLabel.cget("text") + "\n")
		f.write("offsetFile\t" + gl.basicpath_sig + "calibs/" + gl.offSigLabel.cget("text") + "\n")
		f.write("corrFactor\t" + gl.corrSigEntry.get() + "\n")
		f.write("\n")
		# Referemce
		f.write("boolRef\t{}\n".format(gl.boolRef))
		f.write("basicpath\t" + gl.basicpath_ref + "\n")
		f.write("body\t" + gl.body_ref + "\n")
		f.write("beg\t" + gl.begRefEntry.get() + "\n")
		f.write("end\t" + gl.endRefEntry.get() + "\n")
		f.write("calibFile\t" + gl.basicpath_ref + "calibs/" + gl.calibRefLabel.cget("text") + "\n")
		f.write("offsetFile\t" + gl.basicpath_ref + "calibs/" + gl.offRefLabel.cget("text") + "\n")
		f.write("corrFactor\t" + gl.corrRefEntry.get() + "\n")
		f.write("\n")

def load_config():
	if not os.path.exists("configs"):
		os.mkdir("configs")
	configfile = filedialog.askopenfilename(initialdir = "configs", title = "Load configuration", filetypes = (("config files","*.config"),("all files",".*")))
	file = open(configfile).read(); lines = file.split("\n")
	#Signal
	gl.boolSig = bool(lines[0].split("\t")[1])
	gl.basicpath_sig = lines[1].split("\t")[1]
	gl.body_sig = lines[2].split("\t")[1]; gl.bodySigLabel.config(text=gl.body_sig.split("/")[-1])
	gl.begSigEntry.delete(0,'end'); gl.begSigEntry.insert(0,lines[3].split("\t")[1])
	gl.endSigEntry.delete(0,'end'); gl.endSigEntry.insert(0,lines[4].split("\t")[1])
	selectSigCalib_concrete(lines[5].split("\t")[1])
	selectSigOffset_concrete(lines[6].split("\t")[1])
	gl.corrSigEntry.delete(0,'end'); gl.corrSigEntry.insert(0,lines[7].split("\t")[1])
	#Reference
	gl.boolRef = bool(lines[9].split("\t")[1])
	gl.basicpath_ref = lines[10].split("\t")[1]
	gl.body_ref = lines[11].split("\t")[1]; gl.bodyRefLabel.config(text=gl.body_ref.split("/")[-1])
	gl.begRefEntry.delete(0,'end'); gl.begRefEntry.insert(0,lines[12].split("\t")[1])
	gl.endRefEntry.delete(0,'end'); gl.endRefEntry.insert(0,lines[13].split("\t")[1])
	selectRefCalib_concrete(lines[14].split("\t")[1])
	selectRefOffset_concrete(lines[15].split("\t")[1])
	gl.corrRefEntry.delete(0,'end'); gl.corrRefEntry.insert(0,lines[16].split("\t")[1])
