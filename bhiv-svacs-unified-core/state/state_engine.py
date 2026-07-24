def generate_state(intelligence_event):

    state_event = {
        "state": "ALERT",
        "risk_level": intelligence_event["risk_level"]
    }
 
    return state_event 
 
 
