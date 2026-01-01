"""
ML module for predicting product demand based on historical sales data.
"""
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import joblib
import os
from django.conf import settings


def predict_product_demand(product_id, sales_history, days_ahead=7):
    """
    Predict demand for a specific product based on historical sales.
    
    Args:
        product_id: ID of the product
        sales_history: List of dicts with 'date' and 'quantity' keys
        days_ahead: Number of days to predict ahead (default: 7)
    
    Returns:
        dict with prediction, confidence, and trend
    """
    try:
        if not sales_history or len(sales_history) < 3:
            return {
                'predicted_demand': 0,
                'confidence': 'low',
                'trend': 'insufficient_data',
                'current_avg': 0,
                'message': 'Insufficient sales data for accurate prediction'
            }
        
        # Prepare data
        dates = [item['date'] for item in sales_history]
        quantities = [item['quantity'] for item in sales_history]
        
        # Validate data
        if not dates or not quantities or len(dates) != len(quantities):
            return {
                'predicted_demand': 0,
                'confidence': 'low',
                'trend': 'insufficient_data',
                'current_avg': 0,
                'message': 'Invalid sales data format'
            }
        
        # Convert dates to days since first sale
        first_date = min(dates)
        days = np.array([(date - first_date).days for date in dates]).reshape(-1, 1)
        qty = np.array(quantities, dtype=float)
        
        # Check for valid data
        if len(days) < 3 or np.all(qty == 0):
            return {
                'predicted_demand': 0,
                'confidence': 'low',
                'trend': 'insufficient_data',
                'current_avg': float(np.mean(qty)) if len(qty) > 0 else 0,
                'message': 'Insufficient variation in sales data'
            }
        
        # Train model
        model = LinearRegression()
        model.fit(days, qty)
        
        # Predict for next N days
        last_day = max([(date - first_date).days for date in dates])
        future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
        predictions = model.predict(future_days)
        
        # Calculate average predicted demand (ensure non-negative)
        avg_prediction = max(0, float(np.mean(predictions)))
        
        # Calculate trend
        if len(qty) >= 7:
            recent_avg = float(np.mean(qty[-7:]))
        else:
            recent_avg = float(np.mean(qty))
        
        if len(qty) >= 2:
            older_avg = float(np.mean(qty[:max(1, len(qty)//2)]))
        else:
            older_avg = recent_avg
        
        if older_avg == 0:
            trend = 'stable'
        elif recent_avg > older_avg * 1.1:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.9:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate confidence based on data points and variance
        variance = float(np.var(qty))
        mean_qty = float(np.mean(qty))
        data_points = len(qty)
        
        if data_points >= 14 and (mean_qty == 0 or variance < mean_qty * 0.5):
            confidence = 'high'
        elif data_points >= 7:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'predicted_demand': round(avg_prediction, 2),
            'confidence': confidence,
            'trend': trend,
            'current_avg': round(recent_avg, 2),
            'message': None
        }
    except Exception as e:
        # Return safe defaults on any error
        return {
            'predicted_demand': 0,
            'confidence': 'low',
            'trend': 'insufficient_data',
            'current_avg': 0,
            'message': f'Prediction error: {str(e)}'
        }


def predict_all_products_demand(products, sales_data_func, days_ahead=7):
    """
    Predict demand for all products.
    
    Args:
        products: QuerySet of Product objects
        sales_data_func: Function that takes product_id and returns sales history
        days_ahead: Number of days to predict ahead
    
    Returns:
        List of dicts with product info and predictions
    """
    predictions = []
    
    for product in products:
        sales_history = sales_data_func(product.id)
        prediction = predict_product_demand(product.id, sales_history, days_ahead)
        
        predictions.append({
            'product': product,
            'product_id': product.id,
            'product_name': product.name,
            'category': product.category,
            'current_stock': getattr(product, 'current_stock', 0),
            **prediction
        })
    
    return predictions


def save_demand_model(product_id, model, model_dir=None):
    """Save a trained demand prediction model."""
    if model_dir is None:
        model_dir = settings.MEDIA_ROOT / "ml_models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / f"demand_model_{product_id}.pkl"
    joblib.dump(model, model_path)
    return model_path


def load_demand_model(product_id, model_dir=None):
    """Load a saved demand prediction model."""
    if model_dir is None:
        model_dir = settings.MEDIA_ROOT / "ml_models"
    
    model_path = model_dir / f"demand_model_{product_id}.pkl"
    if model_path.exists():
        return joblib.load(model_path)
    return None

