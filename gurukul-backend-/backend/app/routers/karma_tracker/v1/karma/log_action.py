from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.karma_database import users_col
from app.utils.karma.tokens import apply_decay_and_expiry, now_utc
from app.utils.karma.merit import compute_user_merit_score, determine_role_from_merit
from app.utils.karma.transactions import log_transaction
from app.utils.karma.qlearning import q_learning_step
from app.utils.karma.utils_user import create_user_if_missing
from app.utils.karma.paap import classify_paap_action, apply_paap_tokens
from app.utils.karma.atonement import create_atonement_plan
from app.utils.karma.rnanubandhan import rnanubandhan_manager  # Import Rnanubandhan manager
from app.core.karma_config import ROLE_SEQUENCE, ACTIONS, INTENT_MAP, REWARD_MAP, CHEAT_PUNISHMENT_LEVELS, CHEAT_PUNISHMENT_RESET_DAYS
from datetime import timedelta, datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class LogActionRequest(BaseModel):
    user_id: str
    action: str
    role: str
    note: Optional[str] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Add fields for Rnanubandhan relationships
    affected_user_id: Optional[str] = None
    relationship_description: Optional[str] = None

@router.post("/")
def log_action(req: LogActionRequest):
    try:
        if req.role not in ROLE_SEQUENCE:
            raise HTTPException(status_code=400, detail="Invalid role.")
        if req.action not in ACTIONS:
            raise HTTPException(status_code=400, detail="Invalid action.")

        # Ensure user exists
        user = users_col.find_one({"user_id": req.user_id})
        if not user:
            user = create_user_if_missing(req.user_id, req.role)

        # Apply decay/expiry
        user = apply_decay_and_expiry(user)

        # Handle cheat action with progressive punishment
        if req.action == "cheat":
            # Get user's cheat history or initialize if it doesn't exist
            cheat_history = user.get("cheat_history", [])
            current_time = now_utc()
            reset_period = timedelta(days=CHEAT_PUNISHMENT_RESET_DAYS)

            # Helper: normalize timestamps to timezone-aware UTC datetimes
            def _normalize_timestamp(ts):
                """
                Ensure timestamp is timezone-aware (UTC).
                Handles older records that may have naive datetimes.
                """
                if isinstance(ts, datetime):
                    # If naive, assume UTC
                    if ts.tzinfo is None:
                        return ts.replace(tzinfo=timezone.utc)
                    return ts
                # Fallback: try ISO string
                try:
                    parsed = datetime.fromisoformat(ts)
                    if parsed.tzinfo is None:
                        return parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except Exception:
                    # Treat unparseable timestamps as very old so they don't affect recent window
                    return current_time - reset_period - timedelta(days=1)

            # Filter out old cheat attempts beyond the reset period, normalizing timestamps safely
            recent_cheats = []
            for ch in cheat_history:
                ts = ch.get("timestamp")
                if not ts:
                    continue
                norm_ts = _normalize_timestamp(ts)
                try:
                    if current_time - norm_ts <= reset_period:
                        recent_cheats.append(ch)
                except TypeError:
                    # If we still somehow hit naive/aware issues, skip this record
                    continue
            
            # Determine cheat level (number of recent cheats + 1 for current cheat)
            cheat_level = len(recent_cheats) + 1
            
            # Get appropriate punishment
            punishment = CHEAT_PUNISHMENT_LEVELS.get(cheat_level, CHEAT_PUNISHMENT_LEVELS["default"])
            reward_value = punishment["value"]
            token = punishment["token"]
            punishment_name = punishment["name"]
            
            # Record current cheat attempt
            recent_cheats.append({"timestamp": current_time, "punishment_level": cheat_level, "value": reward_value})
            
            # Q-learning step with the determined punishment value
            _, predicted_next_role = q_learning_step(
                req.user_id, req.role, req.action, reward_value
            )
            
            # Update user's balances and cheat history
            users_col.update_one(
                {"user_id": req.user_id},
                {
                    "$inc": {f"balances.{token}": reward_value},
                    "$set": {"cheat_history": recent_cheats}
                }
            )
            
            # Recompute merit & role
            user_after = users_col.find_one({"user_id": req.user_id})
            merit_score = compute_user_merit_score(user_after)
            new_role = determine_role_from_merit(merit_score)
            users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
            
            # Log transaction
            try:
                log_transaction(req.user_id, req.action, reward_value, INTENT_MAP[req.action], "penalty", punishment_name)
            except Exception as e:
                logger.error(f"Failed to log transaction for cheat action: {str(e)}")
                # Continue with the response even if transaction logging fails
            
            # Create Rnanubandhan relationship if there's an affected user
            relationship = None
            if req.affected_user_id and req.affected_user_id != req.user_id:
                try:
                    relationship = rnanubandhan_manager.create_debt_relationship(
                        debtor_id=req.user_id,
                        receiver_id=req.affected_user_id,
                        action_type=req.action,
                        severity="medium",  # Cheat is generally considered medium severity
                        amount=abs(reward_value) * 0.5,  # Create debt proportional to punishment
                        description=req.relationship_description or f"Cheated, affecting user {req.affected_user_id}"
                    )
                except Exception as e:
                    # Log error but don't fail the main action
                    logger.warning(f"Failed to create Rnanubandhan relationship: {e}")
            
            response = {
                "user_id": req.user_id,
                "action": req.action,
                "current_role": new_role,
                "predicted_next_role": predicted_next_role,
                "merit_score": merit_score,
                "penalty_token": token,
                "penalty_value": reward_value,
                "penalty_level": cheat_level,
                "penalty_name": punishment_name,
                "cheats_in_period": len(recent_cheats),
                "action_flow": "action -> intent -> penalty_level -> punishment -> role_adjustment",
                "note": req.note
            }
            
            # Add relationship info if created
            if relationship:
                response["rnanubandhan_relationship"] = relationship
                
            return response
        
        # Handle non-cheat actions with standard reward system
        else:
            # Check if this action generates Paap
            paap_severity = classify_paap_action(req.action)
            
            # Q-learning step
            reward_value, predicted_next_role = q_learning_step(
                req.user_id, req.role, req.action, REWARD_MAP[req.action]["value"]
            )
        
            # Update token balances
            token = REWARD_MAP[req.action]["token"]
            users_col.update_one(
                {"user_id": req.user_id},
                {"$inc": {f"balances.{token}": reward_value}}
            )
            
            # Apply Paap tokens if applicable
            paap_applied = False
            paap_value = 0
            if paap_severity:
                user, severity, paap_value = apply_paap_tokens(user, req.action, 1.0)
                paap_applied = True
                
                # Update database
                users_col.update_one(
                    {"user_id": req.user_id},
                    {"$set": {"balances": user["balances"]}}
                )
                
                # Create an appeal stub if requested
                if req.note and "auto_appeal" in req.note.lower():
                    create_atonement_plan(req.user_id, req.action, paap_severity)
        
            # Recompute merit & role
            user_after = users_col.find_one({"user_id": req.user_id})
            merit_score = compute_user_merit_score(user_after)
            new_role = determine_role_from_merit(merit_score)
            users_col.update_one({"user_id": req.user_id}, {"$set": {"role": new_role}})
        
            # Log transaction
            reward_tier = "high" if token == "PunyaTokens" else "medium" if token == "SevaPoints" else "low"
            try:
                log_transaction(req.user_id, req.action, reward_value, INTENT_MAP[req.action], reward_tier)
            except Exception as e:
                logger.error(f"Failed to log transaction for action {req.action}: {str(e)}")
                # Continue with the response even if transaction logging fails
                
            # Create Rnanubandhan relationship if this is a harmful action affecting another user
            relationship = None
            if paap_applied and req.affected_user_id and req.affected_user_id != req.user_id:
                try:
                    relationship = rnanubandhan_manager.create_debt_relationship(
                        debtor_id=req.user_id,
                        receiver_id=req.affected_user_id,
                        action_type=req.action,
                        severity=paap_severity or "minor",  # Default to minor if severity is None
                        amount=paap_value * 0.3,  # Create debt proportional to Paap value
                        description=req.relationship_description or f"Action '{req.action}' affected user {req.affected_user_id}"
                    )
                except Exception as e:
                    # Log error but don't fail the main action
                    logger.warning(f"Failed to create Rnanubandhan relationship: {e}")
            
            response = {
                "user_id": req.user_id,
                "action": req.action,
                "current_role": new_role,
                "predicted_next_role": predicted_next_role,
                "merit_score": merit_score,
                "reward_token": token,
                "reward_tier": reward_tier,
                "action_flow": "action -> intent -> merit -> reward_tier -> redemption",
                "note": req.note
            }
            
            # Add Paap information if applicable
            if paap_applied:
                response["paap_generated"] = True
                response["paap_severity"] = paap_severity
                response["paap_value"] = paap_value
                response["appeal_created"] = "auto_appeal" in (req.note or "").lower()
                
            # Add relationship info if created
            if relationship:
                response["rnanubandhan_relationship"] = relationship
                
            return response
    except Exception as e:
        logger.error(f"Error processing log_action request for user {req.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")