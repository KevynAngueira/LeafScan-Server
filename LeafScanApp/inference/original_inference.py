from core.cache import load_cache, save_cache, update_cache
from models.original_area_model import run_model
from .defoliation_schedule_inference import schedule_defoliation_inference

def original_inference(video_name, cache=None):
    """Runs ML model to infer original area and update cache."""
    try:
        if not cache:
            cache = load_cache(video_name, 'original_area')

        if cache["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping inference")
            return     
        elif cache["status"] == "completed":
            pred_original_area = cache["results"]["original_area"]
        else:
            params = cache["params"]
            leaf_number = params["leafNumber"]
            leaf_widths = params["leafWidths"]

            pred_original_area = run_model(leaf_number, leaf_widths)

            cache["results"]["original_area"] = pred_original_area
            cache["status"] = "completed"
            save_cache(video_name, "original_area", cache)

            update_cache(video_name, "defoliation", {"original_area": pred_original_area})
        
        print(f"✅ Original area: {pred_original_area:.2f}")
        job, queue_size = schedule_defoliation_inference(video_name, None)
        print(job.id)

        return pred_original_area

    except Exception as e:
        cache["status"] = "failed"
        save_cache(video_name, "original_area", cache)
        raise RuntimeError(f"Original inference failed: {e}")
