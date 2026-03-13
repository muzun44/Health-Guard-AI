import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

# 1. Training Data
data = {
    'age': [25, 50, 20, 65, 30, 70],
    'sugar': [80, 200, 90, 250, 85, 300],
    'pressure': [120, 150, 110, 160, 115, 170],
    'result': [0, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)
X = df[['age', 'sugar', 'pressure']]
y = df['result']

# 2. Train Model
model = RandomForestClassifier()
model.fit(X, y)

# 3. Save Model
with open('medical_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Status: Success! Model created.")