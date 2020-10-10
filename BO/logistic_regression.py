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
def get_model(app_name):
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

def fit_model(logreg, X, y):
    logreg.fit(X, y)    
    return logreg

def prediect_model(logreg, X):
    ret = logreg.predict(X) 
    print(ret)

    return ret

def save_model(logreg, app_name):
    model_file = LogisticRegression_file+app_name
    skopt_utils.dump(logreg, model_file)
    return True


def main():
    X = [[10000, 750, 3], [10000, 250, 3], [20000, 800, 3], [20000, 600, 3]]
    y = [1, 0, 1, 0]
    Y = np.reshape(y, (4, 1))
 
    X_train = np.reshape(X, (4, 3))
    print(X_train)
    # we create an instance of Neighbours Classifier and fit the data.
    
    ret = None
    logreg = get_model("test")
    #print(ret, logreg.coef_)
    try:
        print(logreg.intercept_) 
    except:
        print("error")
    ret = logreg.fit(X_train, Y)
    
    print(ret, logreg.coef_)
    
    X = [[20000, 850, 3556]]
    
    
    ret = logreg.predict(X)
    
    print(ret, logreg.decision_function(X))
    
    X = [[20000, 750, 3] ]
    y = [1]
    X_train = np.reshape(X, (1, 3))
    Y = np.reshape(y, (1, 1))
 
    ret = logreg.fit(X_train, Y)
    
    print(ret)
    

    X = [[20000, 750, 3], [20000, 850, 3]]
    y = [1, 0]
    X_train = np.reshape(X, (2, 3))
    Y = np.reshape(y, (2, 1))
 
    ret = logreg.fit(X_train, Y)
    
    print(ret)
    
    X = [[20000, 850, 3]]
    
    ret = logreg.predict(X)
    
    print(logreg.coef_, logreg.intercept_, logreg.decision_function(X), logreg.predict_proba(X) )

if __name__ == "__main__":
    main()
