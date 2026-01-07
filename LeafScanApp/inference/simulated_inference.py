import os
import shutil
from core.cache import load_cache, save_cache, update_cache
from core.paths import VIDEO_DIR, OUT_DIR, SLICES_DIR
from models.leafscan_model import run_leafscan
from .defoliation_schedule_inference import schedule_defoliation_inference

def simulated_inference(video_name, cache=None):
    """Orchestrates LeafScan inference and updates cache."""
    try:  
        if not cache:
            cache = load_cache(video_name, 'simulated_area')

        if cache["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping inference")
            return 
        elif cache["status"] == "completed":
            pred_simulated_area = cache["results"]["simulated_area"]        
        else:
            params = cache["params"]
            length = float(params["length"])

            video_path = os.path.join(VIDEO_DIR, f"{video_name}.mp4")
            video_output_path = OUT_DIR / video_name
            pred_simulated_area = run_leafscan(video_name, video_path, video_output_path, length)

            cache["results"]["simulated_area"] = pred_simulated_area
            cache["status"] = "completed"
            save_cache(video_name, "simulated_area", cache)

            update_cache(video_name, "defoliation", {"simulated_area": pred_simulated_area})
        
        print(f"✅ Simulated area: {pred_simulated_area:.2f}")
        job, queue_size = schedule_defoliation_inference(video_name, None)
        print(job.id)

        return pred_simulated_area

    except Exception as e:
        cache["status"] = "failed"
        save_cache(video_name, "simulated_area", cache)
        raise RuntimeError(f"Simulated inference failed: {e}")
