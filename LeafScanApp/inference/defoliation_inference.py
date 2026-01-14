from core.cache import get_cache

def defoliation_inference(video_name, state=None):
    """Calculates defoliation % based on original and simulated areas."""
    
    cache = get_cache()
    if not state:
        state = cache.load(video_name, 'defoliation')
    
    try:
        if state["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping inference")
            return 
        elif state["status"] == "completed":
            pred_defoliation = state["results"]["defoliation"]
        else:
            params = state["params"]
            orig = params["original_area"]
            sim = params["simulated_area"]

            pred_defoliation = (1 - (sim / orig)) * 100

            state["results"]["defoliation"] = pred_defoliation
            state["status"] = "completed"
            cache.save(video_name, "defoliation", state)

        print(f"✅ Defoliation: {pred_defoliation:.2f}%")
        return pred_defoliation

    except Exception as e:
        state["status"] = "failed"
        cache.save(video_name, "defoliation", state)
        raise RuntimeError(f"Defoliation inference failed: {e}")