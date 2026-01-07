from core.cache import load_cache, save_cache

def defoliation_inference(video_name, cache=None):
    """Calculates defoliation % based on original and simulated areas."""
    try:
        if not cache:
            cache = load_cache(video_name, 'defoliation')

        if cache["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping inference")
            return 
        elif cache["status"] == "completed":
            pred_defoliation = cache["results"]["defoliation"]
        else:
            params = cache["params"]
            orig = params["original_area"]
            sim = params["simulated_area"]

            pred_defoliation = (1 - (sim / orig)) * 100

            cache["results"]["defoliation"] = pred_defoliation
            cache["status"] = "completed"
            save_cache(video_name, "defoliation", cache)

        print(f"✅ Defoliation: {pred_defoliation:.2f}%")
        return pred_defoliation

    except Exception as e:
        cache["status"] = "failed"
        save_cache(video_name, "defoliation", cache)
        raise RuntimeError(f"Defoliation inference failed: {e}")