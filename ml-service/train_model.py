"""
Train a yield prediction model for AFIP.
Uses synthetic-but-realistic data based on Tanzanian maize growing conditions.
In production, replace with real historical data (NDVI, soil, rainfall, yield).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

np.random.seed(42)

def generate_training_data(n_samples=1000):
    """
    Generate realistic synthetic training data.
    Features:
    - ndvi: 0.1 to 0.9 (vegetation health)
    - ph: 4.5 to 7.5 (soil acidity)
    - nitrogen: 0.5 to 3.0 g/kg
    - carbon: 5 to 30 g/kg
    - rainfall: 300 to 1200 mm (seasonal)
    - temperature: 18 to 32 C (average)
    """
    ndvi = np.random.uniform(0.1, 0.9, n_samples)
    ph = np.random.uniform(4.5, 7.5, n_samples)
    nitrogen = np.random.uniform(0.5, 3.0, n_samples)
    carbon = np.random.uniform(5, 30, n_samples)
    rainfall = np.random.uniform(300, 1200, n_samples)
    temperature = np.random.uniform(18, 32, n_samples)

    # Realistic yield formula (maize, t/ha) with noise
    # Base 1.5 t/ha + contributions
    yield_t_ha = (
        1.0
        + 1.8 * ndvi
        + 0.15 * (ph - 5.5)  # pH near 6.5 is optimal
        + 0.35 * nitrogen
        + 0.02 * carbon
        + 0.0015 * rainfall
        - 0.04 * (temperature - 25) ** 2 / 10
        + np.random.normal(0, 0.25, n_samples)  # noise
    )
    # Clamp to realistic range
    yield_t_ha = np.clip(yield_t_ha, 0.5, 6.0)

    df = pd.DataFrame({
        'ndvi': ndvi,
        'ph': ph,
        'nitrogen': nitrogen,
        'carbon': carbon,
        'rainfall': rainfall,
        'temperature': temperature,
        'yield_t_ha': yield_t_ha,
    })
    return df

def train():
    print("Generating training data...")
    df = generate_training_data(2000)

    X = df[['ndvi', 'ph', 'nitrogen', 'carbon', 'rainfall', 'temperature']]
    y = df['yield_t_ha']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training XGBoost model...")
    # Using RandomForest for simplicity (no xgboost dependency issues)
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"MAE: {mae:.3f} t/ha")
    print(f"R²: {r2:.3f}")

    # Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/yield_model.pkl")
    print("Model saved to models/yield_model.pkl")

    # Save metrics
    with open("models/metrics.txt", "w") as f:
        f.write(f"MAE={mae:.4f}\nR2={r2:.4f}\nn_samples={len(df)}\n")

    return model

if __name__ == "__main__":
    train()
