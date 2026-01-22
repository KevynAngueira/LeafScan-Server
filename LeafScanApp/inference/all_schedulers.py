from storage import JobFields
from .defoliation_schedule_inference import schedule_defoliation_inference
from .original_schedule_inference import schedule_original_inference
from .simulated_schedule_inference import schedule_simulated_inference

SCHEDULERS = {
    JobFields.OUT_ORIGINAL: schedule_original_inference,
    JobFields.OUT_SIMULATED: schedule_simulated_inference,
    JobFields.OUT_DEFOLIATION: schedule_defoliation_inference
}