import joblib
import pandas as pd
from LeafScan.Models import load_model

model_instance = None

def init_model(model_name=None):
    """Load and cache the trained model."""
    if not model_name:
        model_name = "leaf_model_gb.pkl"
    global model_instance
    model_instance = load_model(model_name)
    print("✅ Model loaded successfully")
    return model_instance


def run_model(leaf_number, leaf_widths):
    """Predict original area using the ML model."""
    global model_instance
    if model_instance is None:
        model_instance = init_model()

    param_dict = {f"Width_{i}": w for i, w in enumerate(leaf_widths)}
    param_dict["Leaf_Number"] = leaf_number
    model_params = pd.DataFrame([param_dict])
    
    prediction = model_instance.predict(model_params)[0]
    return float(prediction)
