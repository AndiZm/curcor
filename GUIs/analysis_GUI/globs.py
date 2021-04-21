basicpath_sig = "/mnt/c/Users/andiz/Documents/ii/curcor/measurements"
basicpath_ref = "/mnt/c/Users/andiz/Documents/ii/curcor/measurements"
body_sig = ""; body_ref = ""
boolSig = False; boolRef = False
boolLP = False
boolPatCorr = True
boolRMSlogx = True; boolRMSlogy = True

G2_cum_sig = []; G2_cum_ref = []

g2_sig = []; g2_ref = []; g2_diff = []
files_sig = []; files_ref = []

g2_sig_fft = []; g2_ref_fft = []; g2_diff_fft = []

rmssin_sig = []; rmssin_ref = []
rmscum_sig = []; rmscum_ref = []
rmscum_diff = []

rmssin_sig_exp = []; rmssin_ref_exp = []
rmscum_sig_exp = []; rmscum_ref_exp = []
rmscum_diff_exp = []

rmssin_sig_frac = []; rmssin_ref_frac = []
rmscum_sig_frac = []; rmscum_ref_frac = []
rmscum_diff_frac = []

N_e_sig = 0; N_e_ref = 0.

offset_a_sig = 0.; offset_b_sig = 0.
offset_a_ref = 0.; offset_b_reg = 0.

rates_a_sig = []; rates_b_sig = []
rates_a_ref = []; rates_b_ref = []

# Buttons
updateButton = []
expcorrButton = []

# Labels
bodySigLabel = []; bodyRefLabel = []
calibSigLabel = []; calibRefLabel = []
offSigLabel = []; offRefLabel = []
offASigLabel = []; offARefLabel = []
offBSigLabel = []; offBRefLabel = []
avgChargeASigLabel = []; avgChargeARefLabel = []
avgChargeBSigLabel = []; avgChargeBRefLabel = []
intValLabel = []; timeResValLabel = ()

# Entries
begSigEntry = []; begRefEntry = []
endSigEntry = []; endRefEntry = []
corrSigEntry = []; corrRefEntry = []
rmsRangeLeftEntry = []; rmsRangeRightEntry = []
fitRangeLeftEntry = []; fitRangeRightEntry = []
cutOffEntry = []; orderEntry = []

# Calib data
histo_x_sig = []; histo_a_sig = []; histo_b_sig = []; pa_sig = [[],[],[]]; pb_sig = [[],[],[]]; xplot_sig = []; nsum_a_sig = []; nsum_b_sig = []; ps_a_sig = []; ps_b_sig = []; ps_x_sig = []; ph_a_sig = []; ph_b_sig = []; avg_charge_a_sig = []; avg_charge_b_sig = []
histo_x_ref = []; histo_a_ref = []; histo_b_ref = []; pa_ref = [[],[],[]]; pb_ref = [[],[],[]]; xplot_ref = []; nsum_a_ref = []; nsum_b_ref = []; ps_a_ref = []; ps_b_ref = []; ps_x_ref = []; ph_a_ref = []; ph_b_ref = []; avg_charge_a_ref = []; avg_charge_b_ref = []

# Plottings
corrCanvas = []
corrAx = []; fftAx = []; ratesAx = []; rmssingAx = []; rmscumAx = []
g2_sig_plot = []; g2_ref_plot = []; g2_diff_plot = []
g2_sig_fft_plot = []; g2_ref_fft_plot = []; g2_diff_fft_plot = []
rmssin_sig_plot = []; rmssin_ref_plot = []
rmscum_sig_plot = []; rmscum_ref_plot = []
rmscum_diff_plot = []
rmssin_sig_exp_plot = []; rmssin_ref_exp_plot = []
rmscum_sig_exp_plot = []; rmscum_ref_exp_plot = []
rmscum_diff_exp_plot = []
rates_a_sig_plot = []; rates_b_sig_plot = []
fit_plot = []