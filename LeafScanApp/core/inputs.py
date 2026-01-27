from storage import JobFields

ROUTES = ['video', 'params']

PARAMS_TO_ROUTES = {
    JobFields.IN_VIDEO: "video",
    JobFields.IN_LENGTH: "params",
    JobFields.IN_LEAF: "params",
    JobFields.IN_WIDTHS: "params",
}

def routes_to_rerun(missing_params):
    # Determine which routes are required based on missing params
    rerun_routes = set(PARAMS_TO_ROUTES[p] for p in missing_params if p in PARAMS_TO_ROUTES)
    # Build final dictionary with True/False
    return {route: (route in rerun_routes) for route in ROUTES}

'''
ROUTES = ['video', 'params']

ROUTES_TO_PARAMS = {
    "send/video": ["video"],
    "send/params": ["leafNumber", "leafWidths", "length"],
    "send/image": ["image"]
}

PARAMS_TO_ROUTES = {
    "video": "video",
    
    "leafNumber": "params",
    "leafWidths": "params",
    "length": "params",

    "image": 'image'
}

def routes_to_rerun(missing_params):
    # Determine which routes are required based on missing params
    rerun_routes = set(PARAMS_TO_ROUTES[p] for p in missing_params if p in PARAMS_TO_ROUTES)

    # Build final dictionary with True/False
    return {route: (route in rerun_routes) for route in ROUTES}
'''