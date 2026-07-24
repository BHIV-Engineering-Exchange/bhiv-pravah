import hashlib
import json


def calculate_hash(data):

    return hashlib.sha256(
        json.dumps( 
            data,
            sort_keys=True 
        ).encode()
    ).hexdigest()
 
