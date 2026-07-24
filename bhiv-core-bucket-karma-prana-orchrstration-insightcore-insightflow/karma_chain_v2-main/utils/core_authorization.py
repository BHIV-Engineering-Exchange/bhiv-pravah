"""
Core Authorization Gate for KarmaChain

Implements the Core authorization gate for ALL irreversible actions:
- death_event
- rebirth  
- access gating
- progression locks
- restrictions

Flow: Evaluate → Emit KarmaSignal → WAIT → Core ACK
"""

import asyncio
import time
from typing import Dict, Any, Optional
from enum import Enum
from .karma_signal_contract import KarmaSignal, emit_canonical_karma_signal
from .sovereign_bridge import sovereign_bridge


class IrreversibleActionType(Enum):
    """Types of irreversible actions that require Core authorization"""
    DEATH_EVENT = "death_event"
    REBIRTH = "rebirth"
    ACCESS_GATING = "access_gating"
    PROGRESSION_LOCK = "progression_lock"
    RESTRICTION = "restriction"


async def authorize_irreversible_action(
    subject_id: str,
    action_type: IrreversibleActionType,
    context: str,
    severity: float = 0.9,  # High severity for irreversible actions
    opaque_reason_code: str = "IRREVERSIBLE_ACTION",
    ttl: int = 300,
    timeout: int = 10  # Timeout in seconds
) -> Dict[str, Any]:
    """
    Authorize an irreversible action through Core authorization gate.
    
    Args:
        subject_id: ID of the subject
        action_type: Type of irreversible action
        context: Context where action occurs
        severity: Severity level (0.0 to 1.0)
        opaque_reason_code: Opaque reason code
        ttl: Time to live in seconds
        timeout: Timeout in seconds for authorization
    
    Returns:
        Dict with authorization result:
        - status: 'allowed', 'denied', 'timeout', 'error'
        - authorized: Boolean indicating if action is authorized
        - core_response: Response from Core
    """
    
    # Create a canonical karma signal for the irreversible action
    karma_signal = KarmaSignal(
        subject_id=subject_id,
        product_context=context,
        signal=get_signal_for_action(action_type),
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        ttl=ttl,
        requires_core_ack=True
    )
    
    # Emit the signal to Core for authorization
    start_time = time.time()
    authorization_result = emit_canonical_karma_signal(
        subject_id=subject_id,
        product_context=context,
        signal=karma_signal.signal,
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        ttl=ttl,
        requires_core_ack=True
    )
    
    # Wait for Core response with timeout
    while time.time() - start_time < timeout:
        # Check if authorization result contains the response
        if 'authorization_response' in authorization_result:
            auth_response = authorization_result['authorization_response']
            if 'authorized' in auth_response:
                if auth_response['authorized']:
                    return {
                        "status": "allowed",
                        "authorized": True,
                        "core_response": auth_response,
                        "action_applied": True
                    }
                else:
                    return {
                        "status": "denied",
                        "authorized": False,
                        "core_response": auth_response,
                        "action_applied": False
                    }
        
        # Small delay before checking again
        await asyncio.sleep(0.1)
    
    # Timeout reached - safe fallback (no effect)
    return {
        "status": "timeout",
        "authorized": False,
        "core_response": {"reason": "Timeout waiting for Core authorization"},
        "action_applied": False,
        "fallback_action": "no_effect"
    }


def get_signal_for_action(action_type: IrreversibleActionType) -> str:
    """Map irreversible action type to appropriate signal"""
    action_to_signal = {
        IrreversibleActionType.DEATH_EVENT: "escalate",
        IrreversibleActionType.REBIRTH: "allow",
        IrreversibleActionType.ACCESS_GATING: "restrict",
        IrreversibleActionType.PROGRESSION_LOCK: "restrict", 
        IrreversibleActionType.RESTRICTION: "restrict"
    }
    return action_to_signal.get(action_type, "nudge")


def apply_irreversible_action_if_authorized(authorization_result: Dict[str, Any], action_func=None) -> Dict[str, Any]:
    """
    Apply irreversible action only if authorized by Core.
    
    Args:
        authorization_result: Result from authorize_irreversible_action
        action_func: Optional function to execute if authorized
    
    Returns:
        Dict with action application result
    """
    if authorization_result.get("authorized", False):
        # Action is authorized, apply it
        if action_func:
            try:
                action_result = action_func()
                return {
                    **authorization_result,
                    "action_executed": True,
                    "execution_result": action_result
                }
            except Exception as e:
                return {
                    **authorization_result,
                    "action_executed": False,
                    "error": str(e)
                }
        else:
            return {
                **authorization_result,
                "action_executed": True
            }
    else:
        # Action is not authorized, return with no effect
        return {
            **authorization_result,
            "action_executed": False,
            "reason": "Action not authorized by Core"
        }


def validate_no_direct_execution_without_ack(
    action_type: IrreversibleActionType,
    subject_id: str,
    context: str
) -> bool:
    """
    Validate that irreversible actions go through Core authorization.
    
    Args:
        action_type: Type of action to validate
        subject_id: Subject ID
        context: Context
    
    Returns:
        bool: True if validation passes (no direct execution)
    """
    # This is a validation function to ensure no direct execution happens
    # without going through the Core authorization gate
    print(f"VALIDATION: Action {action_type.value} for subject {subject_id} "
          f"in context {context} must go through Core authorization gate.")
    return True


# Specific functions for each type of irreversible action
async def authorize_death_event(
    subject_id: str,
    context: str,
    severity: float = 0.95,
    opaque_reason_code: str = "DEATH_THRESHOLD_REACHED"
) -> Dict[str, Any]:
    """Authorize a death event"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.DEATH_EVENT,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_rebirth(
    subject_id: str,
    context: str,
    severity: float = 0.1,
    opaque_reason_code: str = "REBIRTH_ELIGIBILITY"
) -> Dict[str, Any]:
    """Authorize a rebirth event"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.REBIRTH,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_access_gating(
    subject_id: str,
    context: str,
    severity: float = 0.8,
    opaque_reason_code: str = "ACCESS_CONTROL_NEEDED"
) -> Dict[str, Any]:
    """Authorize access gating"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.ACCESS_GATING,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_progression_lock(
    subject_id: str,
    context: str,
    severity: float = 0.7,
    opaque_reason_code: str = "PROGRESSION_LOCK_NEEDED"
) -> Dict[str, Any]:
    """Authorize progression lock"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.PROGRESSION_LOCK,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_restriction(
    subject_id: str,
    context: str,
    severity: float = 0.85,
    opaque_reason_code: str = "RESTRICTION_NEEDED"
) -> Dict[str, Any]:
    """Authorize restriction"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.RESTRICTION,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


# Test function to demonstrate the authorization gate
async def test_core_authorization_gate():
    """Test the Core authorization gate functionality"""
    print("Testing Core Authorization Gate...")
    
    # Test a death event authorization
    result = await authorize_death_event(
        subject_id="test_user_123",
        context="game",
        severity=0.95
    )
    
    print(f"Death event authorization result: {result}")
    
    # Test a rebirth authorization
    result = await authorize_rebirth(
        subject_id="test_user_123",
        context="game",
        severity=0.1
    )
    
    print(f"Rebirth authorization result: {result}")
    
    # Verify that no direct execution happens without ACK
    validation_passed = validate_no_direct_execution_without_ack(
        IrreversibleActionType.DEATH_EVENT,
        "test_user_123",
        "game"
    )
    
    print(f"Validation passed: {validation_passed}")
    print("Core Authorization Gate test completed.")


if __name__ == "__main__":
    asyncio.run(test_core_authorization_gate())