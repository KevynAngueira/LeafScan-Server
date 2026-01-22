# ---- Field Names ----

class JobFields:
    IN_VIDEO = "in_video"
    IN_PARAMS = "in_params"

    OUT_ORIGINAL = "out_original"
    OUT_SIMULATED = "out_simulated"
    OUT_DEFOLIATION = "out_defoliation"

    UP_VIDEO = "up_video"
    UP_ORIGINAL = "up_original"
    UP_SIMULATED = "up_simulated"
    UP_DEFOLIATION = "up_defoliation"

    RESULT_DEFOLIATION = "defoliation_result"

    BYTES = "bytes"
    CREATED_AT = "created_at"
    LAST_UPDATED = "last_updated"

# ---- Job Schema ----

JOB_SCHEMA = {
    # inputs
    JobFields.IN_VIDEO: 0,
    JobFields.IN_PARAMS: 0,

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

    # bookkeeping
    JobFields.BYTES: 0,
    # timestamps filled at runtime
}