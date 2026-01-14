from core.cache import get_cache
from models.original_area_model import run_model
from .defoliation_schedule_inference import schedule_defoliation_inference

def original_inference(video_name, state=None):
    """Runs ML model to infer original area and update cache."""
    
    cache = get_cache()
    if not state:
        state = cache.load(video_name, 'original_area')
    
    try:
        if state["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping inference")
            return     
        elif state["status"] == "completed":
            pred_original_area = state["results"]["original_area"]
        else:
            params = state["params"]
            leaf_number = params["leafNumber"]
            leaf_widths = params["leafWidths"]

            pred_original_area = run_model(leaf_number, leaf_widths)

            state["results"]["original_area"] = pred_original_area
            state["status"] = "completed"
            cache.save(video_name, "original_area", state)

            cache.update(video_name, "defoliation", {"original_area": pred_original_area})
        
        print(f"✅ Original area: {pred_original_area:.2f}")
        job, queue_size = schedule_defoliation_inference(video_name, None)
        print(job.id)

        return pred_original_area

    except Exception as e:
        state["status"] = "failed"
        cache.save(video_name, "original_area", state)
        raise RuntimeError(f"Original inference failed: {e}")
