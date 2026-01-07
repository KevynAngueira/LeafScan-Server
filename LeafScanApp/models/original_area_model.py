import joblib
import pandas as pd

model_instance = None

def init_model(model_path=None):
    """Load and cache the trained model."""
    if not model_path:
        model_path = "/home/icicle/VSCode/LeafAnalysis/LeafScan/Models/leaf_model_gb.pkl"
    global model_instance
    model_instance = joblib.load(model_path)
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
