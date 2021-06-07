import numpy as np
from nn_analysis import resnet50

waveform = np.zeros(1000000)
path = 'C:\\Users\\ii\\Documents\\AZ-jkb\\sirius_models\\resnet_model-13_03_2021.h5' # path of neural network model

print ("initialize")
f1 = resnet50(waveform, path) # accecc initializer/class
print ("apply")
f2 = f1.load_model(waveform,path) # perform prediction using resnet, which will give avg.rate(MHz)

#rate = cnn.load_model(waveform, model)
print (f2)