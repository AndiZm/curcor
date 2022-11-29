import numpy as np
import matplotlib.pyplot as plt
import random

def y(x,a,b):
    return a * np.sin(b*x)
def dy(x, a, da, b, db):
    return np.sqrt( ( np.sin(b*x)*da )**2 + ( a*np.cos(b*x)*x*db )**2 )

a  = 10
da = 0

b  = 1
db = 0.1

xplot = np.arange(0,100,0.01)

# error band values:
lower = []; upper = []
for i in xplot:
    uncertainty = dy(x=i, a=a, da=da, b=b, db=db)
    lower.append( y(x=i, a=a, b=b) - uncertainty )
    upper.append( y(x=i, a=a, b=b) + uncertainty )

plt.fill_between(xplot, lower, upper, color="red", alpha=0.3)
plt.plot( xplot, y(xplot, a, b) , color="red")

#bs = np.arange(b-db, b+db, db/10)
#for i in bs:
#    plt.plot( xplot, y(xplot, a, i), color="grey", alpha=0.3 )
#plt.plot( xplot, y(xplot, a, b+db), color="grey", alpha=0.3 )

plt.axvline(x = 10.0*np.pi, alpha=0.3)
plt.axvline(x = 10.5*np.pi, alpha=0.3)
plt.axvline(x = 2         , alpha=0.3)

# Test with a few random realizations and calculate the values at 10 and 10.5 pi
for i in range (0,50):
    b_real = random.gauss(b, db)
    y_value = y(10.0*np.pi, a, b_real); plt.plot(10.0*np.pi, y_value, "x", color="black")
    y_value = y(10.5*np.pi, a, b_real); plt.plot(10.5*np.pi, y_value, "x", color="black")
    y_value = y(2,          a, b_real); plt.plot(2,          y_value, "x", color="black")



plt.show()