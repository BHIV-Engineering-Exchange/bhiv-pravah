import datetime
import numpy as np
import logging
from app.core.karma_database import qtable_col, users_col
from app.core.karma_config import ACTIONS, ROLE_SEQUENCE, ALPHA, GAMMA, REWARD_MAP, CHEAT_PUNISHMENT_LEVELS, ATONEMENT_REWARDS
from app.utils.karma.merit import determine_role_from_merit

logger = logging.getLogger("QLearning")

states = ROLE_SEQUENCE[:]
n_states = len(states)
n_actions = len(ACTIONS)
Q = np.zeros((n_states, n_actions))

# Initial bootstrap load
def load_q_table():
    global Q
    try:
        q_doc = qtable_col.find_one({})
        if q_doc and "q" in q_doc:
            Q = np.array(q_doc["q"])
            if Q.shape != (n_states, n_actions):
                logger.warning(f"Q-table shape mismatch. Expected {(n_states, n_actions)}, got {Q.shape}. Resetting.")
                Q = np.zeros((n_states, n_actions))
        else:
            logger.info("No Q-table found in DB during bootstrap. Initializing zeros.")
            Q = np.zeros((n_states, n_actions))
    except Exception as e:
        logger.error(f"Error loading Q-table on bootstrap: {e}")
        Q = np.zeros((n_states, n_actions))

load_q_table()

def save_q_table():
    """Fallback legacy save function, now with version support."""
    try:
        q_doc = qtable_col.find_one({})
        version = q_doc.get("version", 0) if q_doc else 0
        qtable_col.replace_one(
            {},
            {
                "q": Q.tolist(),
                "version": version + 1,
                "updated_at": datetime.datetime.now(datetime.timezone.utc)
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error in legacy save_q_table: {e}")

def q_learning_step(user_id: str, state: str, action: str, reward: float):
    logger.info(f"q_learning_step: user_id={user_id}, state={state}, action={action}, reward={reward}")
    
    # Ensure state is valid
    if state not in states:
        state = states[0]
    s = states.index(state)
    
    # Ensure action is valid
    if action not in ACTIONS:
        logger.warning(f"Action {action} not in ACTIONS")
        return reward, state
    a = ACTIONS.index(action)

    user_doc = users_col.find_one({"user_id": user_id})
    if not user_doc:
        logger.warning(f"User {user_id} not found")
        return reward, state

    temp_balances = user_doc["balances"].copy()
    
    # Get the appropriate token for the action
    if action == "cheat":
        token = "DharmaPoints"
    else:
        if action in REWARD_MAP:
            token = REWARD_MAP[action]["token"]
        else:
            token = "DharmaPoints"
    
    # Update the correct token balance
    current_balance = temp_balances.get(token, 0)
    if isinstance(current_balance, dict):
        current_balance = 0
    temp_balances[token] = current_balance + reward

    estimated_merit = temp_balances.get("DharmaPoints", 0) * 1.0 + temp_balances.get("SevaPoints", 0) * 1.2 + temp_balances.get("PunyaTokens", 0) * 3.0
    next_role = determine_role_from_merit(estimated_merit)
    
    if next_role not in states:
        next_state = 0
    else:
        next_state = states.index(next_role)
    
    # --- Distributed Optimistic Concurrency Control Loop ---
    max_retries = 5
    for attempt in range(max_retries):
        try:
            q_doc = qtable_col.find_one({})
            current_version = q_doc.get("version", 0) if q_doc else 0
            
            if q_doc and "q" in q_doc:
                local_Q = np.array(q_doc["q"])
                if local_Q.shape != (n_states, n_actions):
                    local_Q = np.zeros((n_states, n_actions))
            else:
                local_Q = np.zeros((n_states, n_actions))
            
            # Perform math on reloaded fresh Q-state
            local_Q[s, a] = local_Q[s, a] + ALPHA * (reward + GAMMA * float(np.max(local_Q[next_state])) - local_Q[s, a])
            
            # Atomic update with version match
            if q_doc:
                res = qtable_col.update_one(
                    {"_id": q_doc["_id"], "version": current_version},
                    {
                        "$set": {
                            "q": local_Q.tolist(),
                            "updated_at": datetime.datetime.now(datetime.timezone.utc)
                        },
                        "$inc": {"version": 1}
                    }
                )
                if res.modified_count > 0:
                    global Q
                    Q = local_Q
                    logger.info(f"Q-learning update succeeded on attempt {attempt+1}")
                    break
            else:
                # Insert initial with version 1
                try:
                    qtable_col.insert_one({
                        "q": local_Q.tolist(),
                        "version": 1,
                        "updated_at": datetime.datetime.now(datetime.timezone.utc)
                    })
                    global Q
                    Q = local_Q
                    logger.info("Successfully bootstrapped initial Q-table in DB.")
                    break
                except Exception:
                    # Race during insert, let loop retry
                    pass
        except Exception as e:
            logger.error(f"Error during optimistic Q-table update attempt {attempt+1}: {e}")
            if attempt == max_retries - 1:
                # Final attempt failed, update local cache anyway to not halt
                global Q
                Q[s, a] = Q[s, a] + ALPHA * (reward + GAMMA * float(np.max(Q[next_state])) - Q[s, a])
                save_q_table()
    
    return reward, next_role

def atonement_q_learning_step(user_id: str, severity_class: str):
    logger.info(f"atonement_q_learning_step: user_id={user_id}, severity={severity_class}")
    user_doc = users_col.find_one({"user_id": user_id})
    if not user_doc:
        return 0, None
    
    state = user_doc.get("role", states[0])
    if state not in states:
        state = states[0]
    
    s = states.index(state)
    
    if severity_class not in ATONEMENT_REWARDS:
        return 0, state
    
    reward_info = ATONEMENT_REWARDS[severity_class]
    reward_value = reward_info["value"]
    token = reward_info["token"]
    
    temp_balances = user_doc["balances"].copy()
    
    if token.startswith("PaapTokens."):
        paap_severity = token.split(".")[1]
        if "PaapTokens" not in temp_balances:
            temp_balances["PaapTokens"] = {}
        if paap_severity not in temp_balances["PaapTokens"]:
            temp_balances["PaapTokens"][paap_severity] = 0
        temp_balances["PaapTokens"][paap_severity] += reward_value
    else:
        temp_balances[token] = temp_balances.get(token, 0) + reward_value
    
    estimated_merit = temp_balances.get("DharmaPoints", 0) * 1.0 + temp_balances.get("SevaPoints", 0) * 1.2 + temp_balances.get("PunyaTokens", 0) * 3.0
    next_role = determine_role_from_merit(estimated_merit)
    next_state = states.index(next_role)
    
    atonement_action = "helping_peers"
    if atonement_action in ACTIONS:
        a = ACTIONS.index(atonement_action)
        
        # --- Distributed Optimistic Concurrency Control Loop ---
        max_retries = 5
        for attempt in range(max_retries):
            try:
                q_doc = qtable_col.find_one({})
                current_version = q_doc.get("version", 0) if q_doc else 0
                
                if q_doc and "q" in q_doc:
                    local_Q = np.array(q_doc["q"])
                    if local_Q.shape != (n_states, n_actions):
                        local_Q = np.zeros((n_states, n_actions))
                else:
                    local_Q = np.zeros((n_states, n_actions))
                
                local_Q[s, a] = local_Q[s, a] + ALPHA * (reward_value + GAMMA * float(np.max(local_Q[next_state])) - local_Q[s, a])
                
                if q_doc:
                    res = qtable_col.update_one(
                        {"_id": q_doc["_id"], "version": current_version},
                        {
                            "$set": {
                                "q": local_Q.tolist(),
                                "updated_at": datetime.datetime.now(datetime.timezone.utc)
                            },
                            "$inc": {"version": 1}
                        }
                    )
                    if res.modified_count > 0:
                        global Q
                        Q = local_Q
                        logger.info(f"Atonement Q-learning update succeeded on attempt {attempt+1}")
                        break
                else:
                    try:
                        qtable_col.insert_one({
                            "q": local_Q.tolist(),
                            "version": 1,
                            "updated_at": datetime.datetime.now(datetime.timezone.utc)
                        })
                        global Q
                        Q = local_Q
                        break
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error in optimistic atonement Q-table update attempt {attempt+1}: {e}")
                if attempt == max_retries - 1:
                    global Q
                    Q[s, a] = Q[s, a] + ALPHA * (reward_value + GAMMA * float(np.max(Q[next_state])) - Q[s, a])
                    save_q_table()
    
    # Save the user balances update in DB
    if token.startswith("PaapTokens."):
        paap_severity = token.split(".")[1]
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {f"balances.PaapTokens.{paap_severity}": reward_value}}
        )
    else:
        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {f"balances.{token}": reward_value}}
        )
    
    return reward_value, next_role