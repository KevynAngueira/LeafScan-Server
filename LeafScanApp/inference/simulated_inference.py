import os
import shutil
import tempfile

from core.cache import get_cache
from core.dependencies import dependencies_ready
from core.paths import VIDEO_DIR, OUT_DIR, SLICES_DIR
from models.leafscan_model import run_leafscan
from storage import ARTIFACTS, JobFields, JobTypes

from .defoliation_schedule_inference import schedule_defoliation_inference

def simulated_inference(entry_id, state=None):
    """Orchestrates LeafScan inference and updates cache."""
    
    cache = get_cache()
    if not state:
        state = cache.load(entry_id, JobTypes.SIMULATED_AREA)
    
    output_flag = bool(
        cache.meta.get_field(
            entry_id, 
            ARTIFACTS[JobTypes.SIMULATED_AREA].output_flag
        )
    )

    try:
        ready, missing, rerunnable = dependencies_ready(
            entry_id,
            JobFields.OUT_SIMULATED
        )
        
        # 1️⃣ Missing inputs → do nothing
        if not ready or state["status"] == "waiting":
            state["status"] = "waiting"
            cache.save(entry_id, JobTypes.SIMULATED_AREA, state)
            print("⏸ Simulated Area: waiting on dependencies")
            return 
       
        # 2️⃣ Artifact says completed AND flag agrees → trust and return
        elif state["status"] == "completed":
            pred_sim_area = state["results"][JobTypes.SIMULATED_AREA]
            print(f"✅ Simulated Area (cached): {pred_sim_area:.2f}%")
            return pred_sim_area
            
        # 3️⃣ Anything else → recompute
        params = state["params"]
        length = float(params[JobFields.IN_LENGTH])

        #if length: cache.meta.update_field(entry_id, JobFields.IN_LENGTH, 0)
        if length is None:
            raise ValueError("Missing simulated area params")

        with cache.load_video_stream(entry_id) as stream:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                shutil.copyfileobj(stream, tmp)
                tmp_path = tmp.name
        try:
            video_output_path = OUT_DIR / entry_id
            pred_sim_area = run_leafscan(entry_id, tmp_path, video_output_path, length)
        except:
            self.cache.meta.update_field(entry_id, JobFields.IN_VIDEO, 0)
            raise ValueError("Error opening LeafScan video")
        finally:
            # Ensure temp file is cleaned up even if run_leafscan fails
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        state["results"][JobTypes.SIMULATED_AREA] = pred_sim_area
        state["status"] = "completed"
        
        cache.save(entry_id, JobTypes.SIMULATED_AREA, state)
        cache.update(entry_id, JobTypes.DEFOLIATION, {JobTypes.SIMULATED_AREA: pred_sim_area})
        
        cache.meta.update_field(entry_id, ARTIFACTS[JobTypes.SIMULATED_AREA].output_flag)

        print(f">>>> Simulated {entry_id} >>>>")
        print(cache.meta.get_entry(entry_id))
        print(f"<<<< Simulated {entry_id} <<<<")
        print()
    
        print(f"✅ Simulated area (computed): {pred_sim_area:.2f}")
        job, queue_size = schedule_defoliation_inference(entry_id, None)
        print(job.id)

        return pred_sim_area

    except Exception as e:
        state["status"] = "failed"
        cache.save(entry_id, JobTypes.SIMULATED_AREA, state)
        raise RuntimeError(f"Simulated inference failed: {e}")
