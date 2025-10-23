# ml_models.py
import numpy as np
from hmmlearn import hmm
import joblib
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
ALERT_MODEL_PATH = os.path.join(MODEL_DIR, 'alert_hmm.pkl')
DROWSY_MODEL_PATH = os.path.join(MODEL_DIR, 'drowsy_hmm.pkl')


def train_and_save_hmms():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # --- Synthetic Alert Data (3 features: blink, nod, accel) ---
    alert_features = np.array([
        [100, 0.2, 0.0],
        [110, 0.1, 0.1],
        [90, 0.3, -0.1],
        [120, 0.2, 0.0]
    ])

    # --- Synthetic Drowsy Data ---
    drowsy_features = np.array([
        [500, 0.9, 0.5],
        [700, 1.2, -0.2],
        [600, 0.8, 0.1],
        [800, 1.5, 0.0]
    ])

    # Use 1 hidden state for single-frame scoring
    alert_model = hmm.GaussianHMM(n_components=1, covariance_type="diag", n_iter=100)
    alert_model.fit(alert_features)
    joblib.dump(alert_model, ALERT_MODEL_PATH)
    print(f"Alert model trained and saved to {ALERT_MODEL_PATH}")

    drowsy_model = hmm.GaussianHMM(n_components=1, covariance_type="diag", n_iter=100)
    drowsy_model.fit(drowsy_features)
    joblib.dump(drowsy_model, DROWSY_MODEL_PATH)
    print(f"Drowsy model trained and saved to {DROWSY_MODEL_PATH}")


def load_models():
    if not os.path.exists(ALERT_MODEL_PATH) or not os.path.exists(DROWSY_MODEL_PATH):
        print("Models not found, training new ones...")
        train_and_save_hmms()

    alert_model = joblib.load(ALERT_MODEL_PATH)
    drowsy_model = joblib.load(DROWSY_MODEL_PATH)
    return alert_model, drowsy_model


def predict_state(feature_vector, alert_model, drowsy_model):
    """
    Single-frame feature_vector = [avg_blink_duration_ms, nod_freq_hz, avg_accel_ay]
    Returns 'Alert' or 'Drowsy'
    """
    X = np.array(feature_vector).reshape(1, 3)  # shape (1, 3)
    alert_score = alert_model.score(X)
    drowsy_score = drowsy_model.score(X)
    print(f"Alert Score: {alert_score:.2f}, Drowsy Score: {drowsy_score:.2f}")
    return "Alert" if alert_score > drowsy_score else "Drowsy"


if __name__ == '__main__':
    train_and_save_hmms()
