from core.cache import get_cache
from storage import get_meta_store, ARTIFACTS, JobFields, JobTypes

def defoliation_inference(video_name, state=None):
    """Calculates defoliation % based on original and simulated areas."""
    
    cache = get_cache()
    if not state:
        state = cache.load(video_name, JobTypes.DEFOLIATION)
    
    try:
        if state["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping defoliation inference")
            return 
        elif state["status"] == "completed":
            pred_defoliation = state["results"][JobTypes.DEFOLIATION]
        else:
            params = state["params"]
            orig = params[JobTypes.ORIGINAL_AREA]
            sim = params[JobTypes.SIMULATED_AREA]

            pred_defoliation = (1 - (sim / orig)) * 100

            state["results"][JobTypes.DEFOLIATION] = pred_defoliation
            state["status"] = "completed"
            
            cache.save(video_name, JobTypes.DEFOLIATION, state)

            cache.meta.update_field(video_name, ARTIFACTS[JobTypes.DEFOLIATION].output_flag)
            cache.meta.update_field(video_name, JobFields.RESULT_DEFOLIATION, pred_defoliation)

        print(f"✅ Defoliation: {pred_defoliation:.2f}%")
        return pred_defoliation

    except Exception as e:
        state["status"] = "failed"
        cache.save(video_name, JobTypes.DEFOLIATION, state)
        raise RuntimeError(f"Defoliation inference failed: {e}")