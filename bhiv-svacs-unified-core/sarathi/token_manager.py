import secrets

 
# =========================================================
# GENERATE TOKEN
# =========================================================
 
def generate_token(execution_request):
 
    token = secrets.token_hex(16)

    return {
        "sarathi_token": {
            "token": token
        }
    }


# =========================================================
# VALIDATE TOKEN
# =========================================================

def validate_token(execution_request):

    # -----------------------------------------------------
    # safe extraction
    # -----------------------------------------------------

    sarathi_token = execution_request.get(
        "sarathi_token",
        {}
    )

    token = sarathi_token.get(
        "token"
    )

    # -----------------------------------------------------
    # validation
    # -----------------------------------------------------

    if (
        not token
        or token == "fake_token"
    ):

        raise Exception(
            "Invalid token detected"
        )

    return True
