"""
Train expiry risk prediction model using Decision Tree Classifier.
This model predicts expiry risk based on days left until expiry.
"""
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# Expanded training data with more examples for better accuracy
data = {
    'days_left': [
        # Low risk (0) - More than 30 days
        365, 300, 250, 200, 180, 150, 120, 90, 60, 45, 40, 35, 32, 31,
        # Medium risk (1) - 7 to 30 days
        30, 28, 25, 20, 15, 12, 10, 8, 7,
        # High risk (2) - Less than 7 days or expired
        6, 5, 4, 3, 2, 1, 0, -1, -5, -10, -30
    ],
    'risk': [
        # Low risk
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        # Medium risk
        1, 1, 1, 1, 1, 1, 1, 1, 1,
        # High risk
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2
    ]
}

df = pd.DataFrame(data)

X = df[['days_left']]
y = df['risk']

# Split data for validation (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model with better parameters
model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Model trained successfully!")
print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
print(f"Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Low', 'Medium', 'High']))

# Save model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "expiry_model.pkl")

with open(MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)

print(f"\nModel saved to: {MODEL_PATH}")
print("\nRisk Levels:")
print("  0 = Low risk (more than 30 days)")
print("  1 = Medium risk (7-30 days)")
print("  2 = High risk (less than 7 days or expired)")
