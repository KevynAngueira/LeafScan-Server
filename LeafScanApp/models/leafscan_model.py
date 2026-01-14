import sys
import shutil
import numpy as np
from core.paths import SLICES_DIR

from LeafScan import LeafScan
from LeafScan.Configs import ViewExtractorConfig, LeafExtractorConfig
from LeafScan.Utils import stitch_images_vertically

leafscan_instance = None

def init_leafscan(view_config=None, separator_config=None):
    """Initialize and store a LeafScan instance."""
    if not view_config:
        view_config = ViewExtractorConfig()
        view_config.tool_bounds = (np.array([0, 138, 115]), np.array([255, 255, 255]))

    global leafscan_instance
    leafscan_instance = LeafScan(
        view_config=view_config,
        leaf_config=separator_config,
        output_folder=SLICES_DIR,
        display=False,
        deep_display=False
    )
    return leafscan_instance


def run_leafscan(video_name, video_path, output_path, length):
    """Runs the LeafScan instance on a video and stitches the result."""
    global leafscan_instance
    if leafscan_instance is None:
        leafscan_instance = init_leafscan()
        
    stacked_slices_path = output_path.with_suffix(".jpg")

    if SLICES_DIR.exists():
        shutil.rmtree(SLICES_DIR)
    SLICES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"▶️ Running LeafScan on: {video_name}")
    pred_simulated_area = leafscan_instance.scanVideo(
        remaining_leaf_length=length,
        video_path=str(video_path),
        #output_path=str(output_path)
    )

    stitch_images_vertically(SLICES_DIR, stacked_slices_path)
    return pred_simulated_area
