def validate_rajya(state_event):

    risk_level = state_event.get("risk_level") 
 
    # =====================================================
    # REJECT CASE
    # =====================================================
 
    if risk_level == "HIGH": 

        return {
            "status": "REJECTED",
            "reason": "High risk anomaly detected"
        }

    # =====================================================
    # APPROVED CASE
    # =====================================================

    elif risk_level == "LOW":

        return {
            "status": "APPROVED",
            "reason": "Validation successful"
        }

    # =====================================================
    # UNKNOWN / INVALID STATE
    # =====================================================

    return {
        "status": "REJECTED",
        "reason": "Invalid or unknown risk level"
    }
