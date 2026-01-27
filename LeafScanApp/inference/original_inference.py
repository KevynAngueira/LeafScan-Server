from core.cache import get_cache
from core.dependencies import dependencies_ready
from models.original_area_model import run_model
from storage import ARTIFACTS, JobFields, JobTypes 

from .defoliation_schedule_inference import schedule_defoliation_inference

def original_inference(entry_id, state=None):
    """Runs ML model to infer original area and update cache."""

    cache = get_cache()
    if not state:
        state = cache.load(entry_id, JobTypes.ORIGINAL_AREA)
    
    output_flag = bool(
        cache.meta.get_field(
            entry_id, 
            ARTIFACTS[JobTypes.ORIGINAL_AREA].output_flag
        )
    )

    try:
        ready, missing, rerunnable = dependencies_ready(
            entry_id,
            JobFields.OUT_ORIGINAL
        )
        
        # 1️⃣ Missing inputs → do nothing
        if not ready or state["status"] == "waiting":
            state["status"] = "waiting"
            cache.save(entry_id, JobTypes.ORIGINAL_AREA, state)
            print("⏸ Original Area: waiting on dependencies")
            return 
       
        # 2️⃣ Artifact says completed AND flag agrees → trust and return
        elif state["status"] == "completed":
            pred_orig_area = state["results"][JobTypes.ORIGINAL_AREA]
            print(f"✅ Original Area (cached): {pred_orig_area:.2f}%")
            return pred_orig_area
            
        # 3️⃣ Anything else → recompute
        params = state["params"]
        leaf_number = params.get(JobFields.IN_LEAF)
        leaf_widths = params.get(JobFields.IN_WIDTHS)

        #if leaf_number: cache.meta.update_field(entry_id, JobFields.IN_LEAF, 0)
        #if leaf_widths: cache.meta.update_field(entry_id, JobFields.IN_WIDTHS, 0)
        if leaf_number is None or leaf_widths is None:
            raise ValueError("Missing original area params")

        pred_orig_area = run_model(leaf_number, leaf_widths)

        state["results"][JobTypes.ORIGINAL_AREA] = pred_orig_area
        state["status"] = "completed"

        cache.save(entry_id, JobTypes.ORIGINAL_AREA, state)
        cache.update(entry_id, JobTypes.DEFOLIATION, {JobTypes.ORIGINAL_AREA: pred_orig_area})

        cache.meta.update_field(entry_id, ARTIFACTS[JobTypes.ORIGINAL_AREA].output_flag)

        print(f">>>> Original {entry_id} >>>>")
        print(cache.meta.get_entry(entry_id))
        print(f"<<<< Original {entry_id} <<<<")
        print()
    
        print(f"✅ Original Area (computed): {pred_orig_area:.2f}")
        inf_job, inf_queue_size = schedule_defoliation_inference(entry_id, None)
        print(inf_job.id)

        return pred_orig_area

    except Exception as e:
        state["status"] = "failed"
        cache.save(entry_id, JobTypes.ORIGINAL_AREA, state)
        raise RuntimeError(f"Original inference failed: {e}")
