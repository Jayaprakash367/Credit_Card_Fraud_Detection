"""
Credit Card Fraud Detection - Model Training Script
Trains a Random Forest classifier for fraud detection
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
import joblib
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'credit_card_fraud_dataset.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
PREPROCESSOR_PATH = os.path.join(BASE_DIR, 'preprocessor.pkl')

def load_and_prepare_data():
    """Load and prepare the dataset."""
    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nClass distribution:")
    print(df['IsFraud'].value_counts())
    print(f"\nFraud rate: {df['IsFraud'].mean() * 100:.2f}%")
    
    return df

def create_preprocessor():
    """Create the preprocessing pipeline."""
    categorical_features = ['TransactionType', 'Location']
    numerical_features = ['Amount']
    
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])
    
    return preprocessor, numerical_features + categorical_features

def train_model(df):
    """Train the fraud detection model."""
    print("\n" + "=" * 50)
    print("Training Model")
    print("=" * 50)
    
    # Feature selection
    feature_names = ['Amount', 'TransactionType', 'Location']
    X = df[feature_names]
    y = df['IsFraud']
    
    # Create preprocessor
    preprocessor, _ = create_preprocessor()
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Fit preprocessor on training data
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    
    # Train Random Forest model
    print("\nTraining Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle imbalanced classes
    )
    
    model.fit(X_train_transformed, y_train)
    
    # Evaluate the model
    print("\n" + "=" * 50)
    print("Model Evaluation")
    print("=" * 50)
    
    # Training accuracy
    train_pred = model.predict(X_train_transformed)
    train_accuracy = accuracy_score(y_train, train_pred)
    print(f"Training Accuracy: {train_accuracy * 100:.2f}%")
    
    # Test accuracy
    test_pred = model.predict(X_test_transformed)
    test_accuracy = accuracy_score(y_test, test_pred)
    print(f"Test Accuracy: {test_accuracy * 100:.2f}%")
    
    # ROC-AUC Score
    test_proba = model.predict_proba(X_test_transformed)[:, 1]
    roc_auc = roc_auc_score(y_test, test_proba)
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    
    # Cross-validation
    print("\nCross-validation (5-fold)...")
    cv_scores = cross_val_score(model, X_train_transformed, y_train, cv=5)
    print(f"CV Scores: {cv_scores}")
    print(f"CV Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Classification Report
    print("\nClassification Report:")
    print(classification_report(y_test, test_pred, target_names=['Legitimate', 'Fraud']))
    
    # Confusion Matrix
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, test_pred)
    print(cm)
    
    # Feature Importance
    print("\nFeature Importance:")
    try:
        cat_features = preprocessor.named_transformers_['cat'].get_feature_names_out(['TransactionType', 'Location'])
        all_feature_names = ['Amount'] + list(cat_features)
        importances = model.feature_importances_
        
        feature_imp = sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)
        for name, imp in feature_imp[:10]:
            print(f"  {name}: {imp:.4f}")
    except Exception as e:
        print(f"  Could not extract feature importance: {e}")
    
    return model, preprocessor, feature_names

def save_model(model, preprocessor, feature_names):
    """Save the trained model and preprocessor."""
    print("\n" + "=" * 50)
    print("Saving Model and Preprocessor")
    print("=" * 50)
    
    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")
    
    # Save preprocessor and feature names
    joblib.dump((preprocessor, feature_names), PREPROCESSOR_PATH)
    print(f"Preprocessor saved to: {PREPROCESSOR_PATH}")
    
    print("\nModel training complete!")

def main():
    """Main function to train and save the model."""
    print("=" * 60)
    print("Credit Card Fraud Detection - Model Training")
    print("=" * 60)
    
    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        return
    
    # Load data
    df = load_and_prepare_data()
    
    # Train model
    model, preprocessor, feature_names = train_model(df)
    
    # Save model
    save_model(model, preprocessor, feature_names)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print("\nYou can now run the Flask application with: python app.py")

if __name__ == '__main__':
    main()
