import pickle
from datetime import date
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "expiry_model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except Exception:
    model = None

def predict_expiry_risk(expiry_date):
    today = date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        days_left = 0

    if model:
        result = model.predict([[days_left]])[0]
    else:
        if days_left <= 7:
            result = "High"
        elif days_left <= 30:
            result = "Medium"
        else:
            result = "Low"
    return result, days_left
