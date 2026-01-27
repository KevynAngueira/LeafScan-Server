from storage import get_meta_store, JobFields, JobTypes

UPSTREAM_DEPENDENCY_SCHEMA = {    
    # OUTPUTS
    JobFields.OUT_ORIGINAL: [JobFields.IN_LEAF, JobFields.IN_WIDTHS],
    JobFields.OUT_SIMULATED: [JobFields.IN_VIDEO, JobFields.IN_LENGTH],
    JobFields.OUT_DEFOLIATION: [JobFields.OUT_ORIGINAL, JobFields.OUT_SIMULATED],

    # UPLOADS
    JobFields.UP_ORIGINAL: [JobFields.OUT_ORIGINAL],
    JobFields.UP_SIMULATED: [JobFields.OUT_SIMULATED],
    JobFields.UP_DEFOLIATION: [JobFields.OUT_DEFOLIATION],
}

DOWNSTREAM_DEPENDENCY_SCHEMA = {
    # INPUTS
    JobFields.IN_LEAF: [JobFields.OUT_ORIGINAL],
    JobFields.IN_WIDTHS: [JobFields.OUT_ORIGINAL],
    JobFields.IN_VIDEO: [JobFields.OUT_SIMULATED],
    JobFields.IN_LENGTH: [JobFields.OUT_SIMULATED],
    
    # OUTPUTS + UPLOADS
    JobFields.OUT_ORIGINAL: [JobFields.OUT_DEFOLIATION, JobFields.UP_ORIGINAL],
    JobFields.OUT_SIMULATED: [JobFields.OUT_DEFOLIATION, JobFields.UP_SIMULATED],
    JobFields.OUT_DEFOLIATION: [JobFields.UP_DEFOLIATION],

    # Job To Dependency
    JobTypes.ORIGINAL_AREA: [JobFields.OUT_DEFOLIATION, JobFields.UP_ORIGINAL],
    JobTypes.SIMULATED_AREA: [JobFields.OUT_DEFOLIATION, JobFields.UP_SIMULATED],
    JobTypes.DEFOLIATION: [JobFields.UP_DEFOLIATION],
}

def check_dependencies(entry_id: str, stage: str, missing_params):
    """
    Recursively check upstream inputs.
    """
    meta = get_meta_store()
    required_params = UPSTREAM_DEPENDENCY_SCHEMA.get(stage, [])

    all_satisfied = True
    jobs_to_reschedule = []
    for r in required_params:
        value = meta.get_field(entry_id, r)
        is_present = bool(int(value))

        sub_satisfied = True
        if not is_present:
            if r in UPSTREAM_DEPENDENCY_SCHEMA:
                sub_satisfied = check_dependencies(entry_id, r, missing_params)

                if sub_satisfied:
                    jobs_to_reschedule.append(r)
            else:
                missing_params.append(r)
                sub_satisfied = False
        
        all_satisfied = all_satisfied and sub_satisfied
    
    return all_satisfied, jobs_to_reschedule

def get_dependents(entry_id: str, changed_field: str, visited=None):
    if visited is None:
        visited = set()

    for dep in DOWNSTREAM_DEPENDENCY_SCHEMA.get(changed_field, []):
        if dep not in visited:
            visited.add(dep)
            get_dependents(entry_id, dep, visited)

    return visited
