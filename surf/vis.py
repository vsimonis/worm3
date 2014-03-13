import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from pylab import *

fig = plt.figure()
ax = fig.add_subplot(111, projection = '3d')

alldata = pd.io.parsers.read_csv('surf-h299-1.csv', sep =',', header = 0, index_col = 0)

n_samples, n_features = alldata.shape
n_digits = len(np.unique(alldata.mov))
labels = alldata.mov

data = alldata[['size', 'angle', 'response', 'mov']]

colors = [int(i % 5) for i in  data['mov']]

ax.scatter(data['size'], data['angle'], data['response'], c = colors)

plt.show()

