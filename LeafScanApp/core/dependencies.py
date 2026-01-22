from inference.all_schedulers import SCHEDULERS
from storage import get_meta_store, JobFields

DEPENDENCY_SCHEMA = {
    JobFields.OUT_ORIGINAL: [JobFields.IN_PARAMS],
    JobFields.OUT_SIMULATED: [JobFields.IN_VIDEO, JobFields.IN_PARAMS],
    JobFields.OUT_DEFOLIATION: [JobFields.OUT_ORIGINAL, JobFields.OUT_SIMULATED],
}

def check_dependencies(video_name: str, stage: str, missing_params):
    
    meta = get_meta_store()
    required_params = DEPENDENCY_SCHEMA.get(stage, [])

    all_satisfied = True
    for r in required_params:
        value = meta.get_field(video_name, r)
        is_present = bool(int(value))

        sub_satisfied = True
        if not is_present:
            if r in DEPENDENCY_SCHEMA:
                sub_satisfied = check_dependencies(video_name, r, missing_params)

                if sub_satisfied:
                    job, queue_size = SCHEDULERS[r](video_name, None)
            else:
                missing_params.append(r)
                sub_satisfied = False
        
        all_satisfied = all_satisfied and sub_satisfied
    
    return all_satisfied