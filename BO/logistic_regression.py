print(__doc__)

# Code source: Gaël Varoquaux
# Modified for documentation by Jaques Grobler
# License: BSD 3 clause
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
import skopt.utils as skopt_utils


from pandas import DataFrame


LogisticRegression_file = "/tmp/skopt_LogisticRegression_"
def get_logistic_model(app_name):
    """
    read model or create model.
    """
    model_file = LogisticRegression_file+app_name
    if os.path.exists(model_file) == False:
        logreg = linear_model.LogisticRegression(warm_start=True)
        print("initialize logistic regression model {}".format(app_name))
    else:
        logreg = skopt_utils.load(model_file)
        print("read logistic regression model for {}".format(app_name))
    return logreg

def fit_logistic_model(logreg, X, y):
    logreg.fit(X, y)    
    return logreg

def prediect_logistic_model(logreg, X):
    ret = logreg.predict(X) 
    print(ret)

    return ret

def save_logistic_model(logreg, app_name):
    model_file = LogisticRegression_file+app_name
    skopt_utils.dump(opt, model_file)
    return True


def test():
    X = [[10000, 750, 3], [10000, 250, 3], [20000, 800, 3]]
    y = [1, 0, 1]
    
    X_train = np.reshape(X, (3, 3))
    print(X_train)
    # we create an instance of Neighbours Classifier and fit the data.
    
    logreg = get_logistic_model("test")
    ret = None
    ret = logreg.fit(X_train, y)
    
    print(ret)
    
    X = [[20000, 850, 3556]]
    
    
    ret = logreg.predict(X)
    
    print(ret, logreg.decision_function(X))
    
    
    X = [[10000, 750, 3], [10000, 250, 3], [20000, 850, 3], [20000, 750, 3]]
    y = [1 ,0, 0, 1]
    X_train = np.reshape(X, (4, 3))
    
    ret = logreg.fit(X_train, y)
    
    print(ret)
    
    X = [[20000, 850, 3]]
    
    ret = logreg.predict(X)
    
    print(ret, logreg.decision_function(X), logreg.predict_proba(X) )
    
test()    
