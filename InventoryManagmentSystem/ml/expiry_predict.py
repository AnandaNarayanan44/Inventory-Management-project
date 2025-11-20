import pickle
from datetime import date
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "expiry_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_expiry_risk(expiry_date):
    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        days_left = 0

    result = model.predict([[days_left]])[0]
    return result, days_left
