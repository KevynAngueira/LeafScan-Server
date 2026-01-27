import os
import shutil
import tempfile

from core.cache import get_cache
from core.paths import VIDEO_DIR, OUT_DIR, SLICES_DIR
from models.leafscan_model import run_leafscan
from storage import ARTIFACTS, JobFields, JobTypes

from .defoliation_schedule_inference import schedule_defoliation_inference

def simulated_inference(video_name, state=None):
    """Orchestrates LeafScan inference and updates cache."""
    
    cache = get_cache()
    if not state:
        state = cache.load(video_name, JobTypes.SIMULATED_AREA)

    try:  
        
        if state["status"] == "waiting":
            print(f"Warning: Missing parameters, skipping simulated area inference")
            return 
        elif state["status"] == "completed":
            pred_simulated_area = state["results"][JobTypes.SIMULATED_AREA]        
        else:
            params = state["params"]
            length = float(params[JobFields.IN_LENGTH])

            with cache.load_video_stream(video_name) as stream:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    shutil.copyfileobj(stream, tmp)
                    tmp_path = tmp.name
            try:
                video_output_path = OUT_DIR / video_name
                pred_simulated_area = run_leafscan(video_name, tmp_path, video_output_path, length)
            finally:
                # Ensure temp file is cleaned up even if run_leafscan fails
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            state["results"][JobTypes.SIMULATED_AREA] = pred_simulated_area
            state["status"] = "completed"
            
            cache.save(video_name, JobTypes.SIMULATED_AREA, state)
            cache.update(video_name, JobTypes.DEFOLIATION, {JobTypes.SIMULATED_AREA: pred_simulated_area})
            
            cache.meta.update_field(video_name, ARTIFACTS[JobTypes.SIMULATED_AREA].output_flag)
        
        print(f"✅ Simulated area: {pred_simulated_area:.2f}")
        job, queue_size = schedule_defoliation_inference(video_name, None)
        print(job.id)

        return pred_simulated_area

    except Exception as e:

        state["status"] = "failed"
        cache.save(video_name, JobTypes.SIMULATED_AREA, state)
        raise RuntimeError(f"Simulated inference failed: {e}")
