import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.signal import find_peaks
sns.set(style='darkgrid')
from keras.models import load_model

class resnet50 :
    def __init__(self, array, model_path):
        self.array = array
        self.model_path = model_path
    def load_model(self,array, model_path):
        array =  array
        array = np.where(array<0,0,array)
        array = array-1
        array = np.where(array<0,0,array)
        samp_X = array.reshape(np.int(array.shape[0]/100),100)
        
        def rmse(y_true, y_pred):
            return K.sqrt(K.mean(K.square(y_pred - y_true)))
        path = model_path
        model = load_model(path, custom_objects={'rmse':rmse})
        
        samp_X1 = samp_X[:122000]
        test_X = samp_X1.reshape(samp_X1.shape[0],samp_X1.shape[1],1)
        y_pred = model.predict(test_X, verbose=1)
        y_pred1 = np.where(y_pred== 1.3125455,0,y_pred)
        mean_rate = np.mean(y_pred1*6.25)
        #print(mean_rate, file_ind)
        #meanRate.append(mean_rate)
        return mean_rate