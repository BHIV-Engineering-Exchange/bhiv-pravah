"""
Script to append VANA governed abstention API endpoint to main.py
"""
import pathlib

f = pathlib.Path(__file__).parent / "control_plane" / "backend" / "app" / "main.py"
content = f.read_text(encoding="utf-8")

NEW_ENDPOINT = """

# ===========================================================================
# Phase 15 - VANA Governed Abstention Integration
# ===========================================================================

class VanaExecuteRequest(BaseModel):
    trace_id: Optional[str] = None
    execution_id: Optional[str] = None

@app.post("/vana/execute")
def vana_execute(request: VanaExecuteRequest):
    \"\"\"
    Endpoint to process Group 2 temporal applicability rulings for VANA.
    
    This fulfills the Phase 15 integration requirement to consume a real Group 2 
    GAP ruling, translate it into a DecisionContract, run it through ActionGovernance, 
    and record the governed abstention without executing any operational action.
    \"\"\"
    import json
    from pathlib import Path
    from fastapi import HTTPException
    from control_plane.decision_translation.contextual_result_adapter import ContextualResultAdapter
    from control_plane.core.action_governance import ActionGovernance
    from control_plane.decision_translation.governed_abstention_recorder import GovernedAbstentionRecorder

    # Load authoritative Group 2 ruling
    # Note: V2.2 observation timestamp conflict is a known open item for Group 2.
    # We consume the committed ruling as-is per the integration requirement.
    ruling_path = Path(__file__).resolve().parents[3] / "integration" / "group2" / "temporal_applicability_ruling.json"
    if not ruling_path.exists():
        raise HTTPException(status_code=500, detail="Group 2 ruling artifact not found")
        
    ruling = json.loads(ruling_path.read_text(encoding="utf-8"))
    
    # Merge optional runtime IDs if provided
    if request.trace_id:
        ruling["trace_id"] = request.trace_id
    if request.execution_id:
        ruling["execution_id"] = request.execution_id
        
    # Translate to DecisionContract
    adapter = ContextualResultAdapter()
    contract = adapter.translate(ruling)
    
    # Evaluate Governance (NOOP should always be allowed)
    governance = ActionGovernance(env=os.getenv("ENVIRONMENT", "dev"))
    gov_decision = governance.evaluate_contract(
        decision=contract, 
        context={"app_name": "vana", "env": os.getenv("ENVIRONMENT", "dev"), "source": "vana_execute"}
    )
    
    # Record Abstention (writes to AppendOnlyLog)
    recorder = GovernedAbstentionRecorder()
    evidence = recorder.record(contract=contract, governance_decision=gov_decision)
    
    return {
        "status": "governed_abstention",
        "evidence": evidence
    }
"""

if "vana_execute" not in content:
    f.write_text(content + NEW_ENDPOINT, encoding="utf-8")
    print("Endpoint appended.")
else:
    print("Endpoint already exists.")
