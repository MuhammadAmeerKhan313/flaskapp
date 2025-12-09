import pickle
import numpy as np
import pandas as pd

model = pickle.load(open('models/best_model.pkl', 'rb'))
scaler = pickle.load(open('models/scaler.pkl', 'rb'))

column_names = ['attendance', 'homework_completion', 'test_scores', 'participation']

def predict_performance(features):
    input_data = pd.DataFrame([features], columns=column_names)
    scaled_features = scaler.transform(input_data)
    prediction = model.predict(scaled_features)
    probability = model.predict_proba(scaled_features)
    return prediction[0], np.max(probability)