

from scipy.optimize import curve_fit
import numpy as np
from numpy import genfromtxt
import matplotlib.pyplot as plt 

# Get data:
my_data = genfromtxt("./sandbox/response_data/valve_response_dlite_setup.csv", delimiter=',')
xdata = my_data[:,0]
ydataup = -1.0*my_data[:,1]
ydatadown = -1.0*my_data[:,2]

plt.scatter(xdata, ydataup, c='b', label='Duty Increasing')
plt.scatter(xdata, ydatadown, c='r', label='Duty Decreasing')
plt.xlabel('Prop Valve Duty Cycle')
plt.ylabel('Flow (LPM)')
plt.legend()
plt.show()

# Sigmoid function to fit: 
def sigmoid(x, L ,x0, k, b):
    y = L / (1 + np.exp(-k*(x-x0)))+b
    return (y)

# Function which fits sigmoid function to the data:
def fit_sigmoid(xdata, ydata):
    p0 = [max(ydata), np.median(xdata),1,min(ydata)] # this is an mandatory initial guess
    popt, pcov = curve_fit(sigmoid, xdata, ydata, p0, method='dogbox', maxfev=50000)
    return popt
    
def inverse_sigmoid(y, L ,x0, k, b):
    x = -1.0*np.log(L / (y - b) - 1.0) / k + x0
    return (x)
    
# Function which takes trained sigmoid model and predicts on data:
def predict_data(xdata, popt):
    preddata = sigmoid(xdata, popt[0], popt[1], popt[2], popt[3])
    return preddata

#Plot the fit: 
def generate_sig_plot(xdata, ydataup, preddataup, ydatadown, preddatadown):
    plt.scatter(xdata, ydataup, c='b')
    plt.scatter(xdata, ydatadown, c='g')
    plt.scatter(xdata, preddataup, c='r')
    plt.scatter(xdata, preddatadown, c='k')
    plt.show() 
   
poptup = fit_sigmoid(xdata, ydataup)
preddataup = predict_data(xdata, poptup)
poptdown = fit_sigmoid(xdata, ydatadown)
preddatadown = predict_data(xdata, poptdown)

generate_sig_plot(xdata, ydataup, preddataup, ydatadown, preddatadown)

arrsav = np.arange(0, 101, 1)

n_span_up = (np.max(preddataup) - np.min(preddataup)) / 101
arrup = np.arange(np.min(preddataup), np.max(preddataup), n_span_up)
n_span_down = (np.max(preddatadown) - np.min(preddatadown)) / 101
arrdown = np.arange(np.min(preddatadown), np.max(preddatadown), n_span_down)

duty_up = inverse_sigmoid(arrup, poptup[0], poptup[1], poptup[2], poptup[3])
duty_down = inverse_sigmoid(arrdown, poptdown[0], poptdown[1], poptdown[2], poptdown[3])




# Save predictions:
# Normalize by max flow:
#preddataup = preddataup / np.max(preddataup)
#preddatadown = preddatadown / np.max(preddatadown)

save_arr = np.zeros((len(xdata),3))
save_arr[:,0] = arrsav
save_arr[:,1] = duty_up
save_arr[:,2] = duty_down

save_arr = np.round(save_arr,4)
save_arr[0,:] = 0.0

# Save:
# open a binary file in write mode
response_file = open("./sandbox/response_data/SMC_PVQ31_5G_23_01N_DLITE_response", "wb")
# save array to the file
np.save(response_file, save_arr)
# close the file
response_file.close()


'''
# Test response function:
def response(value, xdata, preddata):
    idx = (np.abs(preddata - value)).argmin()
    return xdata[idx]
    
    
print(response(0.5, xdata, preddataup))
print(response(0.5, xdata, preddatadown))

ydataup = ydataup / np.max(ydataup)
ydatadown = ydatadown / np.max(ydatadown)
generate_sig_plot(xdata, ydataup, preddataup, ydatadown, preddatadown)
'''






