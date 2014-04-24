import numpy as np
import pandas as pd

alldata = pd.io.parsers.read_csv('surf-h299-1.csv', sep =',', header = 0, index_col = 0)

p= alldata.columns.values.tolist()

print p
n_samples, n_features = alldata.shape
n_digits = len(np.unique(alldata.mov))
labels = alldata[['img', 'mov']]

data = alldata[['size', 'angle', 'response']]

cols = range(0,128)


surfs = alldata[cols]
surfs['img'] = alldata['img']

#surfs = surfs.groupby('img').head(1)
#labels = labels.groupby('img').head(1)

surfs = surfs[cols]
labels = labels.mov

from sklearn import tree
from sklearn.cross_validation import train_test_split
from sklearn.metrics import confusion_matrix

surf_train, surf_test, labels_train, labels_test = train_test_split(surfs, labels, random_state =0)


clf = tree.DecisionTreeClassifier(criterion = 'gini', splitter = 'best')#, max_depth = 5, min_samples_split = 10, min_samples_leaf = 5)
clf = clf.fit(surf_train, labels_train)

labels_pred = clf.predict(surf_test)

print surf_train.shape
print surf_test.shape

cm = confusion_matrix(labels_test, labels_pred)
print cm


from sklearn.externals.six import StringIO
with open("Dt-surf-h299-allkp.dot", 'w') as f:
    f= tree.export_graphviz(clf, out_file=f)



