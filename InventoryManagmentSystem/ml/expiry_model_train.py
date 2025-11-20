import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import pickle

data = {
    'days_left': [200, 150, 90, 60, 30, 15, 7, 3, 1, 0],
    'risk':      [0,   0,   0,  1,  1,  1,  2, 2, 2, 2]
}

df = pd.DataFrame(data)

X = df[['days_left']]
y = df['risk']

model = DecisionTreeClassifier()
model.fit(X, y)

with open('expiry_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")
