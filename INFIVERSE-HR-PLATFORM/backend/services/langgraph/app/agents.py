from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from .state import CandidateApplicationState
from .tools import *
from .rl_engine import rl_engine, feedback_processor
from .rl_database import rl_db_manager
from .rl_performance_monitor import rl_performance_monitor
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Initialize LLM
try:
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=0.7,
        google_api_key=settings.gemini_api_key
    )
    logger.info(f"✅ LLM initialized: {settings.gemini_model}")
except Exception as e:
    logger.error(f"❌ Failed to initialize LLM: {e}")
    llm = None

async def application_screener_agent(state: CandidateApplicationState) -> dict:
    """Agent that screens candidate applications using RL-enhanced AI matching"""
    logger.info(f"🔍 RL-enhanced screening for application {state['application_id']}")
    
    try:
        start_time = time.time()
        
        if not llm:
            logger.error("LLM not initialized")
            return {
                "application_status": "pending",
                "next_action": "error",
                "error": "LLM not available"
            }
        
        # Get base AI matching score
        matching_result = await get_ai_matching_score.ainvoke({
            "candidate_id": state['candidate_id'],
            "job_id": state['job_id']
        })
        
        base_score = matching_result.get('score', 0)
        
        # Get feedback history for RL enhancement
        feedback_history = rl_db_manager.get_feedback_history(limit=50)
        
        # Prepare candidate and job features for RL
        candidate_features = {
            "skills": state.get('candidate_skills', []),
            "experience": state.get('candidate_experience', []),
            "education": state.get('candidate_education', [])
        }
        
        job_features = {
            "requirements": state.get('job_requirements', []),
            "title": state['job_title'],
            "description": state.get('job_description', '')
        }
        
        # Calculate RL-enhanced score
        rl_result = rl_engine.calculate_rl_score(
            candidate_features, job_features, feedback_history
        )
        
        rl_score = rl_result.get('rl_score', base_score)
        confidence = rl_result.get('confidence_level', 50)
        decision_type = rl_result.get('decision_type', 'review')
        
        # Record prediction time
        prediction_time = (time.time() - start_time) * 1000
        rl_performance_monitor.record_prediction(prediction_time, rl_score)
        
        logger.info(f"RL Score: {rl_score}/100 (Base: {base_score}, Confidence: {confidence}%)")
        
        # Store RL prediction in database
        prediction_data = {
            "candidate_id": state['candidate_id'],
            "job_id": state['job_id'],
            "rl_score": rl_score,
            "confidence_level": confidence,
            "decision_type": decision_type,
            "features_used": rl_result.get('features_used', {}),
            "model_version": rl_result.get('model_version', 'v1.0.0')
        }
        
        prediction_id = rl_db_manager.store_rl_prediction(prediction_data)
        
        # Prepare LLM for decision with RL context
        system_prompt = f"""You are an RL-enhanced AI recruiter for BHIV HR Platform.

Candidate: {state['candidate_name']}
Email: {state['candidate_email']}
Job Title: {state['job_title']}
Base AI Score: {base_score}/100
RL-Enhanced Score: {rl_score}/100
Confidence Level: {confidence}%
RL Decision: {decision_type}

RL Scoring Decision:
- ≥ 75: SHORTLIST (strong fit, recommend interview)
- 50-74: REVIEW (moderate fit, needs HR decision)
- < 50: REJECT (not suitable)

The RL system has learned from {len(feedback_history)} previous cases.
Provide brief reasoning considering both base and RL-enhanced scores."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="What is your RL-enhanced recommendation?")
        ]
        
        response = await llm.ainvoke(messages)
        recommendation = response.content
        
        # Make decision based on RL score
        if rl_score >= 75:
            next_action = "notify_shortlist"
            status = "shortlisted"
        elif rl_score >= 50:
            next_action = "manual_review"
            status = "pending"
        else:
            next_action = "notify_reject"
            status = "rejected"
        
        logger.info(f"✅ RL Decision: {status} (RL Score: {rl_score}, Confidence: {confidence}%)")
        
        return {
            "application_status": status,
            "next_action": next_action,
            "matching_score": float(rl_score),
            "base_score": float(base_score),
            "rl_adjustment": float(rl_score - base_score),
            "confidence_level": float(confidence),
            "decision_type": decision_type,
            "prediction_id": prediction_id,
            "ai_recommendation": recommendation,
            "workflow_stage": "notification",
            "messages": state["messages"] + [
                HumanMessage(content="Screen this application with RL enhancement"),
                response
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ RL Screening error: {str(e)}")
        return {
            "next_action": "error",
            "error": str(e),
            "workflow_stage": "screening"
        }

async def notification_agent(state: CandidateApplicationState) -> dict:
    """Agent that sends multi-channel notifications"""
    logger.info(f"📢 Sending notifications for application {state['application_id']}")
    
    try:
        status = state["application_status"]
        
        if status == "shortlisted":
            message = f"""🎉 Congratulations {state['candidate_name']}!

You have been shortlisted for the position of {state['job_title']}!

Our HR team will contact you within 24-48 hours with the next steps.

AI Matching Score: {state.get('matching_score', 0)}/100

Best regards,
BHIV HR Team"""
            
        elif status == "rejected":
            message = f"""Thank you for your interest in {state['job_title']} at BHIV.

After careful review, we've decided to move forward with other candidates at this time.

Don't worry! We'll keep your profile in our system and notify you about future opportunities that match your profile.

Your Matching Score: {state.get('matching_score', 0)}/100

Best regards,
BHIV HR Team"""
        else:
            logger.info(f"⏭️ No notification needed for status: {status}")
            return {"notifications_sent": []}
        
        # Send notifications
        notification_result = await send_multi_channel_notification.ainvoke({
            "candidate_id": state["candidate_id"],
            "candidate_email": state["candidate_email"],
            "candidate_phone": state["candidate_phone"],
            "candidate_name": state["candidate_name"],
            "job_title": state["job_title"],
            "application_status": status,
            "message": message,
            "channels": ["email", "whatsapp"]
        })
        
        success = notification_result.get('success_count', 0)
        failed = notification_result.get('failed_count', 0)
        logger.info(f"✅ Notifications sent: {success} success, {failed} failed")
        
        return {
            "notifications_sent": notification_result.get("notifications", []),
            "workflow_stage": "hr_update",
            "next_action": "update_dashboard"
        }
    
    except Exception as e:
        logger.error(f"❌ Notification error: {str(e)}")
        return {
            "error": str(e),
            "notifications_sent": [],
            "workflow_stage": "notification"
        }

async def hr_update_agent(state: CandidateApplicationState) -> dict:
    """Agent that updates HR portal and database"""
    logger.info(f"📊 Updating HR dashboard for application {state['application_id']}")
    
    try:
        # Update application status in database
        await update_application_status.ainvoke({
            "application_id": state["application_id"],
            "status": state["application_status"],
            "notes": f"AI: {state.get('ai_recommendation', 'N/A')}"
        })
        
        # Update dashboard
        await update_hr_dashboard.ainvoke({
            "application_id": state["application_id"],
            "update_data": {
                "candidate_name": state["candidate_name"],
                "job_title": state["job_title"],
                "status": state["application_status"],
                "matching_score": state.get("matching_score", 0),
                "updated_at": datetime.now().isoformat()
            }
        })
        
        logger.info(f"✅ Dashboard synced for application {state['application_id']}")
        
        return {
            "workflow_stage": "feedback",
            "next_action": "collect_feedback"
        }
    
    except Exception as e:
        logger.error(f"❌ Dashboard update error: {str(e)}")
        return {
            "error": str(e),
            "workflow_stage": "hr_update"
        }

async def feedback_collection_agent(state: CandidateApplicationState) -> dict:
    """Agent that collects feedback for RL optimization and learning"""
    logger.info(f"📝 RL Feedback collection for application {state['application_id']}")
    
    try:
        # Prepare feedback data for RL system
        prediction_id = state.get('prediction_id')
        actual_outcome = state["application_status"]
        
        # Map application status to feedback score
        status_to_score = {
            "shortlisted": 4,
            "interviewed": 5,
            "hired": 5,
            "rejected": 2,
            "withdrawn": 1,
            "pending": 3
        }
        
        feedback_score = status_to_score.get(actual_outcome, 3)
        
        # Process feedback through RL system
        rl_feedback_data = {
            "prediction_id": prediction_id,
            "candidate_id": state["candidate_id"],
            "actual_outcome": actual_outcome,
            "feedback_score": feedback_score,
            "feedback_source": "workflow_automation"
        }
        
        processed_feedback = feedback_processor.process_feedback(rl_feedback_data)
        
        # Store feedback in RL database
        if not processed_feedback.get('error'):
            feedback_id = rl_db_manager.store_rl_feedback(processed_feedback)
            
            # Record feedback metrics
            reward_signal = processed_feedback.get('reward_signal', 0)
            is_correct = reward_signal > 0
            rl_performance_monitor.record_feedback(is_correct, reward_signal)
            
            logger.info(f"✅ RL Feedback stored: ID {feedback_id}, Reward: {reward_signal}")
        
        # Generate training data for future model improvement
        candidate_features = {
            "skills": state.get('candidate_skills', []),
            "experience": state.get('candidate_experience', [])
        }
        
        job_features = {
            "requirements": state.get('job_requirements', []),
            "title": state['job_title']
        }
        
        training_data = feedback_processor.generate_training_data(
            candidate_features, job_features, 
            state.get('matching_score', 0), actual_outcome
        )
        
        if not training_data.get('error'):
            rl_db_manager.store_training_data(training_data)
        
        # Log audit event with RL context
        feedback_data = {
            "candidate_id": state["candidate_id"],
            "job_id": state["job_id"],
            "application_id": state["application_id"],
            "candidate_name": state["candidate_name"],
            "rl_matching_score": state.get("matching_score", 0),
            "base_score": state.get("base_score", 0),
            "rl_adjustment": state.get("rl_adjustment", 0),
            "confidence_level": state.get("confidence_level", 0),
            "final_status": actual_outcome,
            "reward_signal": processed_feedback.get('reward_signal', 0),
            "prediction_id": prediction_id,
            "feedback_id": feedback_id if 'feedback_id' in locals() else None,
            "ai_recommendation": state.get("ai_recommendation", ""),
            "notifications_sent": len(state.get("notifications_sent", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        await log_audit_event.ainvoke({
            "event_type": f"rl_application_{actual_outcome}",
            "details": feedback_data
        })
        
        logger.info(f"✅ RL Feedback collection completed with reward: {processed_feedback.get('reward_signal', 0)}")
        
        return {
            "workflow_stage": "completed",
            "sentiment": "positive" if actual_outcome == "shortlisted" else "negative" if actual_outcome == "rejected" else "neutral",
            "rl_feedback_processed": True,
            "reward_signal": processed_feedback.get('reward_signal', 0),
            "learning_data_stored": True
        }
    
    except Exception as e:
        logger.error(f"❌ RL Feedback collection error: {str(e)}")
        return {
            "error": str(e),
            "workflow_stage": "feedback",
            "rl_feedback_processed": False
        }