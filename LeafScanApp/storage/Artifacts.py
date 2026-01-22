from dataclasses import dataclass
from typing import Optional
from fnmatch import fnmatch

from .JobSchema import JobFields


@dataclass(frozen=True)
class Artifact:
    pattern: str
    input_flag: Optional[str] = None
    output_flag: Optional[str] = None
    upload_flag: Optional[str] = None
           

def artifact_from_filename(filename: str) -> Artifact | None:
    for artifact in ARTIFACTS.values():
        if fnmatch(filename, artifact.pattern):
            return artifact
    return None

# ---- Canonical registry ----

ARTIFACTS = {
    "video": Artifact(
        pattern="*_video.mp4",
        input_flag=JobFields.IN_VIDEO,
        upload_flag=JobFields.UP_VIDEO,
    ),
    
    "params": Artifact(
        pattern="params",
        input_flag=JobFields.IN_PARAMS,
    ),

    "original_area": Artifact(
        pattern="*_original_area.json",
        output_flag=JobFields.OUT_ORIGINAL,
        upload_flag=JobFields.UP_ORIGINAL,
    ),

    "simulated_area": Artifact(
        pattern="*_simulated_area.json",
        output_flag=JobFields.OUT_SIMULATED,
        upload_flag=JobFields.UP_SIMULATED,
    ),

    "defoliation": Artifact(
        pattern="*_defoliation.json",
        output_flag=JobFields.OUT_DEFOLIATION,
        upload_flag=JobFields.UP_DEFOLIATION
    )
}