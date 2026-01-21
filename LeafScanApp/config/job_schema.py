JOB_SCHEMA = {
    # inference stage
    "stage": "RECEIVING",

    # input readiness
    "in_video": 0,
    "in_original": 0,
    "in_simulated": 0,

    # upload completion
    "up_video": 0,
    "up_original": 0,
    "up_simulated": 0,
    "up_defoliation": 0,

    # result
    "defoliation_result": -1,

    # bookkeeping
    "bytes": 0,
    "created_at": None,
    "last_updated": None,
}
