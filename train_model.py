import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle

data = pd.read_csv('data/student_data.csv')

X = data.drop(columns=['performance'])
y = data['performance']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier()

model.fit(X_train_scaled, y_train)

with open('models/best_model.pkl' , 'wb') as f:
    pickle.dump(model, f)
    
with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
    
print("Model and Scaler saved Successfully")