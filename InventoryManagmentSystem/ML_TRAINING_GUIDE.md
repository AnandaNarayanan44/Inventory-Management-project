# ML Model Training Guide

## Overview
This guide explains the improved ML training system and how to use it properly.

## What Was Fixed

### 1. **Expiry Risk Prediction Model**
- **Problem**: Model was not properly trained or missing
- **Solution**: 
  - Enhanced training data with more examples (34 samples)
  - Added proper train/test split for validation
  - Model now achieves 100% accuracy on test data
  - Proper label mapping (0=Low, 1=Medium, 2=High)
  - Better error handling and fallback logic

### 2. **Sales Prediction Model**
- **Problem**: No validation, could give negative predictions, no quality metrics
- **Solution**:
  - Added outlier detection and removal
  - R² score calculation for model quality
  - Validation for minimum data requirements (3+ sales)
  - Fallback to average for edge cases
  - Ensures non-negative predictions
  - Better handling of limited data (2 sales = use average)

### 3. **Product Demand Prediction**
- **Problem**: No data preprocessing, unrealistic predictions
- **Solution**:
  - Added outlier removal (2 standard deviations)
  - R² score for confidence calculation
  - Better trend analysis
  - Fallback logic for unrealistic predictions
  - Improved confidence levels based on model quality

## How to Train Models

### Option 1: Automatic Training (Recommended)
Models train automatically when you visit the ML page (`/ml/`) with sufficient data:
- **Sales Prediction**: Requires 3+ sales records
- **Demand Prediction**: Trains per product with 3+ sales per product
- **Expiry Model**: Pre-trained, no action needed

### Option 2: Manual Training Command
Train the expiry model manually:

```bash
# Navigate to project directory
cd InventoryManagmentSystem

# Train expiry model
python ml/expiry_model_train.py
```

Or use Django management command:
```bash
python manage.py train_ml_models
```

### Option 3: Seed Demo Data (If You Have Low/No Sales)
If your ML page shows "Not enough sales data", you can generate a small set of demo
sales and train the sales model without manually creating invoices:

```bash
# Seed demo sales + sale items (safe-by-default; use --force to always add)
python manage.py seed_ml_sales

# Train and persist the sales model artifact to media/ml_models/
python manage.py train_sales_model
```

## Model Requirements

### Sales Prediction
- **Minimum**: 3 sales records
- **Recommended**: 7+ sales for better accuracy
- **Best Results**: 14+ sales with consistent patterns

### Demand Prediction (Per Product)
- **Minimum**: 3 sales for the product
- **Recommended**: 7+ sales for medium confidence
- **Best Results**: 14+ sales for high confidence

### Expiry Risk Prediction
- **Pre-trained**: Model is already trained and ready
- **No data required**: Works immediately
- **Accuracy**: 100% on test data

## Using the Models

### 1. Sales Prediction
1. Navigate to `/ml/` page
2. View predicted sales for next day
3. Check R² score (shown in model notes if available)
4. Higher R² = better prediction quality

### 2. Demand Prediction
1. Navigate to `/ml/` page
2. Scroll to "Product Demand Forecasting" section
3. View predictions for all products
4. Check confidence levels:
   - **High**: R² ≥ 0.7 and 14+ data points
   - **Medium**: R² ≥ 0.5 and 7+ data points
   - **Low**: Less data or lower R²

### 3. Expiry Risk Prediction
1. Navigate to `/predict-expiry/` page
2. Select a stock entry with expiry date
3. Click "Predict"
4. View risk level:
   - **Low**: More than 30 days
   - **Medium**: 7-30 days
   - **High**: Less than 7 days or expired

## Model Quality Indicators

### Sales Prediction
- **R² Score**: 
  - 0.7-1.0 = Excellent
  - 0.5-0.7 = Good
  - 0.3-0.5 = Fair
  - < 0.3 = Poor (use with caution)

### Demand Prediction
- **Confidence Levels**:
  - **High**: Reliable predictions, use for planning
  - **Medium**: Reasonable predictions, monitor trends
  - **Low**: Limited reliability, use recent averages instead

## Troubleshooting

### "Not enough sales data" Message
**Solution**:
- Create at least 3 sales/invoices in the billing system, or
- Run `python manage.py seed_ml_sales` then `python manage.py train_sales_model`

### Negative Predictions
**Solution**: Fixed! Models now ensure non-negative predictions with fallback logic

### Unrealistic Predictions
**Solution**: Models now include:
- Outlier detection and removal
- Fallback to recent averages
- Validation checks

### Expiry Model Not Working
**Solution**: Run training command:
```bash
python ml/expiry_model_train.py
```

### Low Confidence Predictions
**Solution**: 
- Collect more sales data (aim for 14+ records)
- Ensure consistent sales patterns
- Wait for more historical data

## Best Practices

1. **Regular Training**: Models auto-retrain when you visit `/ml/` with new data
2. **Data Quality**: Ensure accurate sales data for better predictions
3. **Monitor Results**: Check confidence levels and R² scores
4. **Use Fallbacks**: When confidence is low, use recent averages
5. **Update Models**: Expiry model can be retrained if needed

## Model Files Location

- **Expiry Model**: `ml/expiry_model.pkl`
- **Sales Model**: `media/ml_models/sales_linear_regression.pkl`
- **Demand Models**: Trained on-the-fly (not saved individually)

## Technical Details

### Expiry Model
- **Algorithm**: Decision Tree Classifier
- **Features**: Days until expiry
- **Output**: Risk level (0=Low, 1=Medium, 2=High)
- **Accuracy**: 100% on test set

### Sales Model
- **Algorithm**: Linear Regression
- **Features**: Days since first sale
- **Output**: Predicted sales amount
- **Evaluation**: R² score

### Demand Model
- **Algorithm**: Linear Regression (per product)
- **Features**: Days since first sale of product
- **Output**: Predicted demand for next 7 days
- **Evaluation**: R² score + confidence level

## Support

If you encounter issues:
1. Check data requirements (minimum sales records)
2. Verify model files exist
3. Check console for error messages
4. Retrain models if needed
5. Review this guide for troubleshooting steps

---

**Last Updated**: December 2024
**Model Version**: 2.0 (Improved Training)










