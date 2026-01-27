# ---- Field Names ----

class JobTypes:
    VIDEO = "video"
    PARAMS = "params"
    ORIGINAL_AREA = "original_area"
    SIMULATED_AREA = "simulated_area"
    DEFOLIATION = "defoliation"

class JobFields:
    IN_VIDEO = "video"
    IN_LENGTH = "length"
    IN_LEAF = "leafNumber"
    IN_WIDTHS = "leafWidths"

    OUT_ORIGINAL = "out_original"
    OUT_SIMULATED = "out_simulated"
    OUT_DEFOLIATION = "out_defoliation"

    UP_VIDEO = "up_video"
    UP_ORIGINAL = "up_original"
    UP_SIMULATED = "up_simulated"
    UP_DEFOLIATION = "up_defoliation"

    RESULT_DEFOLIATION = "defoliation_result"
    RESULT_FETCHED = "result_fetched"

    BYTES = "bytes"
    CREATED_AT = "created_at"
    LAST_UPDATED = "last_updated"
    ARTIFACTS_PURGED = "artifacts_purged"

# ---- Job Schema ----

JOB_SCHEMA = {
    # inputs
    JobFields.IN_VIDEO: 0,
    JobFields.IN_LENGTH: 0,
    JobFields.IN_LEAF: 0,
    JobFields.IN_WIDTHS: 0,

    # outputs
    JobFields.OUT_ORIGINAL: 0,
    JobFields.OUT_SIMULATED: 0,
    JobFields.OUT_DEFOLIATION: 0,

    # uploads
    JobFields.UP_VIDEO: 0,
    JobFields.UP_ORIGINAL: 0,
    JobFields.UP_SIMULATED: 0,
    JobFields.UP_DEFOLIATION: 0,

    # result
    JobFields.RESULT_DEFOLIATION: -1,
    JobFields.RESULT_FETCHED: 0,

    # bookkeeping
    JobFields.BYTES: 0,
    JobFields.ARTIFACTS_PURGED: 0,
    # timestamps filled at runtime
}