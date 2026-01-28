from core.cache import get_cache
from core.dependencies import dependencies_ready
from storage import get_meta_store, ARTIFACTS, JobFields, JobTypes

def defoliation_inference(entry_id, state=None):
    """Calculates defoliation % based on original and simulated areas."""
    
    cache = get_cache()
    if not state:
        state = cache.load(entry_id, JobTypes.DEFOLIATION)
    
    output_flag = bool(
        cache.meta.get_field(
            entry_id, 
            ARTIFACTS[JobTypes.DEFOLIATION].output_flag
        )
    )

    try:
        ready, missing, rerunnable = dependencies_ready(
            entry_id,
            JobFields.OUT_DEFOLIATION
        )
        
        # 1️⃣ Missing inputs → do nothing
        if not ready or state["status"] == "waiting":
            state["status"] = "waiting"
            cache.save(entry_id, JobTypes.ORIGINAL_AREA, state)
            print("⏸ Defoliation: waiting on dependencies")
            return 
       
        # 2️⃣ Artifact says completed AND flag agrees → trust and return
        if state["status"] == "completed":
            pred_defoliation = state["results"][JobTypes.DEFOLIATION]
            print(f"✅ Defoliation (cached): {pred_defoliation:.2f}%")
            return pred_defoliation
            
        # 3️⃣ Anything else → recompute
        params = state["params"]
        orig = params.get(JobTypes.ORIGINAL_AREA)
        sim = params.get(JobTypes.SIMULATED_AREA)

        #if orig: cache.meta.update_field(entry_id, ARTIFACTS[JobTypes.ORIGINAL_AREA].output_flag, 0)
        #if sim: cache.meta.update_field(entry_id, ARTIFACTS[JobTypes.SIMULATED_AREA].output_flag, 0)
        if orig is None or sim is None:
            print(ready, missing, rerunnable)
            raise ValueError("Missing original or simulated area")

        pred_defoliation = (1 - (sim / orig)) * 100

        state["results"][JobTypes.DEFOLIATION] = pred_defoliation
        state["status"] = "completed"
        
        cache.save(entry_id, JobTypes.DEFOLIATION, state)

        cache.meta.update_field(entry_id, ARTIFACTS[JobTypes.DEFOLIATION].output_flag)
        cache.meta.update_field(entry_id, JobFields.RESULT_DEFOLIATION, pred_defoliation)

        print(f">>> Defoliation {entry_id} >>>>")
        print(cache.meta.get_entry(entry_id))
        print(f"<<<< Defoliation {entry_id} <<<<")
        print()

        print(f"✅ Defoliation (computed): {pred_defoliation:.2f}%")
        return pred_defoliation

    except Exception as e:
        state["status"] = "failed"
        cache.save(entry_id, JobTypes.DEFOLIATION, state)
        raise RuntimeError(f"Defoliation inference failed: {e}")