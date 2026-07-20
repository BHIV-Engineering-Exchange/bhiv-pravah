from datetime import datetime
from human_review import review_system
from database.service import DatabaseService

try:
    from notification_service import send_info_alert, send_success_alert, send_warning_alert, send_critical_alert
    NOTIFICATIONS_ENABLED = True
except ImportError:
    NOTIFICATIONS_ENABLED = False
    def send_info_alert(*args, **kwargs): pass
    def send_success_alert(*args, **kwargs): pass
    def send_warning_alert(*args, **kwargs): pass
    def send_critical_alert(*args, **kwargs): pass

# === Config ===
THRESHOLD = 5

# === Step 1: Sense ===
def sense():
    print("🔍 Reading returns data from database...")
    with DatabaseService() as db_service:
        returns = db_service.get_returns(processed=False)
    return returns

# === Step 2: Plan ===
def plan(returns):
    print("🧠 Planning restock actions...")
    restocks = []
    for item in returns:
        qty = item.get("ReturnQuantity") or item.get("return_quantity")
        pid = item.get("ProductID") or item.get("product_id")
        if qty is not None and qty > THRESHOLD:
            restocks.append({
                "ProductID": pid,
                "RestockQuantity": qty
            })
    return restocks

# === Step 3: Act ===
def act(restocks):
    if restocks:
        # Send alert about restock processing
        send_info_alert("Restock Processing Started", 
                       f"Processing {len(restocks)} restock requests",
                       {"total_requests": len(restocks), "timestamp": datetime.now().isoformat()})
        
        approved_restocks = []
        review_items = []

        with DatabaseService() as db_service:
            for restock in restocks:
                action_data = {
                    "product_id": restock["ProductID"],
                    "quantity": restock["RestockQuantity"]
                }

                if review_system.requires_human_review("restock", action_data):
                    # Submit for human review
                    decision = f"Restock {restock['ProductID']} with quantity {restock['RestockQuantity']}"
                    review_id = review_system.submit_for_review("restock", action_data, decision)
                    print(f"⏳ Restock for {restock['ProductID']} pending human review (ID: {review_id})")
                    review_items.append(restock)

                    # Send warning alert for items requiring review
                    send_warning_alert("Human Review Required", 
                                     f"Restock for {restock['ProductID']} requires human review",
                                     {"product_id": restock["ProductID"], 
                                      "quantity": restock["RestockQuantity"],
                                      "review_id": review_id})
                else:
                    # Auto-approve high confidence decisions -> create DB restock request and log
                    confidence = review_system.calculate_confidence("restock", action_data)
                    created = db_service.create_restock_request(
                        restock["ProductID"], restock["RestockQuantity"], confidence
                    )
                    if created:
                        db_service.log_agent_action(
                            action="RestockRequest",
                            product_id=restock["ProductID"],
                            quantity=restock["RestockQuantity"],
                            confidence=confidence,
                            human_review=False,
                            details="Auto-approved restock request created"
                        )
                        # Mark related returns as processed for this product
                        try:
                            db_service.mark_returns_processed(restock["ProductID"])
                        except Exception:
                            pass
                        approved_restocks.append(restock)
                        print(f"✅ Auto-approved restock for {restock['ProductID']}")
                    else:
                        print(f"⚠️ Failed to create restock request for {restock['ProductID']}")

        # Send success alert for approved restocks
        if approved_restocks:
            send_success_alert("Restocks Approved", 
                             f"Successfully processed {len(approved_restocks)} automatic restocks",
                             {"approved_count": len(approved_restocks),
                              "products": [r["ProductID"] for r in approved_restocks]})

        if len(approved_restocks) < len(restocks):
            print(f"ℹ️ {len(restocks) - len(approved_restocks)} restock(s) pending human review")
    else:
        print("ℹ️ No restock needed.")
        send_info_alert("Restock Check Complete", "No restocks needed at this time")

# === Log actions ===
def log_actions(restocks):
    with DatabaseService() as db_service:
        for item in restocks:
            db_service.log_agent_action(
                action="RestockRequest",
                product_id=item["ProductID"],
                quantity=item["RestockQuantity"],
                confidence=review_system.calculate_confidence("restock", {"product_id": item["ProductID"], "quantity": item["RestockQuantity"]}),
                human_review=False,
                details="Auto-approved restock request created"
            )
    print("📜 Actions logged to database.")

# === Main Agent Flow ===
def run_agent():
    try:
        send_info_alert("Agent Cycle Started", "Restock agent beginning processing cycle")
        returns = sense()
        plan_result = plan(returns)
        act(plan_result)
        send_success_alert("Agent Cycle Complete", "Restock agent completed processing cycle successfully")
        return True
    except Exception as e:
        error_msg = f"Agent error: {str(e)}"
        print(f"⚠️  {error_msg}")
        
        # Send critical alert for agent errors
        send_critical_alert("Agent Error", error_msg, 
                           {"error_type": type(e).__name__,
                            "error_details": str(e),
                            "timestamp": datetime.now().isoformat()})
        
        # Log error but don't crash
        try:
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action='error',
                    product_id=None,
                    quantity=0,
                    confidence=0.0,
                    human_review=True,
                    details=f"Error: {str(e)}"
                )
        except Exception:
            pass
        return False

# === Run ===
if __name__ == "__main__":
    run_agent()
