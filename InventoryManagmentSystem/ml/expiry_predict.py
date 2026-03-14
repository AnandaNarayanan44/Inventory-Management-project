"""
Expiry risk prediction module.
Predicts expiry risk level based on days left until expiry.
"""
import pickle
from datetime import date
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "expiry_model.pkl")

# Load model on module import
model = None
try:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        print(f"Expiry model loaded successfully from {MODEL_PATH}")
    else:
        print(f"Warning: Expiry model not found at {MODEL_PATH}. Run expiry_model_train.py to create it.")
except Exception as e:
    print(f"Error loading expiry model: {e}")
    model = None

# Risk level mapping
RISK_LABELS = {
    0: "Low",
    1: "Medium", 
    2: "High"
}

def predict_expiry_risk(expiry_date):
    """
    Predict expiry risk for a given expiry date.
    
    Args:
        expiry_date: Date object representing the expiry date
        
    Returns:
        tuple: (risk_level_string, days_left)
            - risk_level_string: "Low", "Medium", or "High"
            - days_left: Number of days until expiry (negative if expired)
    """
    if expiry_date is None:
        return "Unknown", None
    
    today = date.today()
    days_left = (expiry_date - today).days

    # Use trained model if available
    if model is not None:
        try:
            # Predict using model
            risk_numeric = model.predict([[days_left]])[0]
            risk_level = RISK_LABELS.get(risk_numeric, "Unknown")
        except Exception as e:
            print(f"Error in model prediction: {e}, using fallback logic")
            # Fallback to rule-based prediction
            if days_left < 0:
                risk_level = "High"
            elif days_left <= 7:
                risk_level = "High"
            elif days_left <= 30:
                risk_level = "Medium"
            else:
                risk_level = "Low"
    else:
        # Fallback to rule-based prediction if model not available
        if days_left < 0:
            risk_level = "High"
        elif days_left <= 7:
            risk_level = "High"
        elif days_left <= 30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
    
    return risk_level, days_left
