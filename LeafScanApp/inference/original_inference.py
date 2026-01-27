from core.cache import get_cache
from models.original_area_model import run_model
from storage import ARTIFACTS, JobFields, JobTypes 

from .defoliation_schedule_inference import schedule_defoliation_inference

def original_inference(video_name, state=None):
    """Runs ML model to infer original area and update cache."""
    
    cache = get_cache()
    if not state:
        state = cache.load(video_name, JobTypes.ORIGINAL_AREA)
    
    try:
        if state["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping original area inference")
            return     
        elif state["status"] == "completed":
            pred_original_area = state["results"][JobTypes.DEFOLIATION]
        else:
            params = state["params"]
            leaf_number = params[JobFields.IN_LEAF]
            leaf_widths = params[JobFields.IN_WIDTHS]

            pred_original_area = run_model(leaf_number, leaf_widths)

            state["results"][JobTypes.ORIGINAL_AREA] = pred_original_area
            state["status"] = "completed"

            cache.save(video_name, JobTypes.ORIGINAL_AREA, state)
            cache.update(video_name, JobTypes.DEFOLIATION, {JobTypes.ORIGINAL_AREA: pred_original_area})

            cache.meta.update_field(video_name, ARTIFACTS[JobTypes.ORIGINAL_AREA].output_flag)
        
        print(f"✅ Original area: {pred_original_area:.2f}")
        inf_job, inf_queue_size = schedule_defoliation_inference(video_name, None)
        print(inf_job.id)

        return pred_original_area

    except Exception as e:
        state["status"] = "failed"
        cache.save(video_name, JobTypes.ORIGINAL_AREA, state)
        raise RuntimeError(f"Original inference failed: {e}")
