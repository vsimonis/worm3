import numpy as np
import pandas as pd

alldata = pd.io.parsers.read_csv('surf-h299-1.csv', sep =',', header = 0, index_col = 0)

n_samples, n_features = alldata.shape
n_digits = len(np.unique(alldata.mov))
labels = alldata.mov

data = alldata[['size', 'angle', 'response']]

cols = range(0,128)


surfs = alldata[cols]

from sklearn import tree
from sklearn.cross_validation import train_test_split
from sklearn.metrics import confusion_matrix

surf_train, surf_test, labels_train, labels_test = train_test_split(surfs, labels, random_state =0)


clf = tree.DecisionTreeClassifier()
clf = clf.fit(surfs, labels)

labels_pred = clf.predict(surf_test)

print surf_train.shape
print surf_test.shape

cm = confusion_matrix(labels_test, labels_pred)
print cm


from sklearn.externals.six import StringIO
with open("Dt-surf-h299.dot", 'w') as f:
    f= tree.export_graphviz(clf, out_file=f)



