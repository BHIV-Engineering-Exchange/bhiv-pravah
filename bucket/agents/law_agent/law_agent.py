"""
Law Agent - AI-Powered Legal Assistance System

This module provides legal assistance through multiple AI agents:
- Basic Agent: Core legal domain classification and route recommendation
- Adaptive Agent: Self-learning agent that improves from feedback
- Enhanced Agent: Advanced agent with constitutional backing and crime data insights

Can be run as:
1. Individual FastAPI server: python law_agent.py
2. Part of basket system: through the process() function
"""

import os
import sys
import time
import logging
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import json
import aiohttp
import requests

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add parent directory to access utils and other modules
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import project dependencies
try:
    from utils.logger import logger
except ImportError:
    # Fallback logging if utils not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models for FastAPI (if FastAPI available)
# ============================================================================

try:
    from pydantic import BaseModel, Field
    from typing import Union

    # Request Models
    class BasicLegalQueryRequest(BaseModel):
        user_input: str = Field(..., description="Legal query text")
        feedback: Optional[str] = Field(None, description="User feedback")
        session_id: Optional[str] = Field(None, description="Session ID")

    class AdaptiveLegalQueryRequest(BaseModel):
        user_input: str = Field(..., description="Legal query text")
        enable_learning: bool = Field(True, description="Enable learning from feedback")
        feedback: Optional[str] = Field(None, description="User feedback")
        session_id: Optional[str] = Field(None, description="Session ID")

    class EnhancedLegalQueryRequest(BaseModel):
        user_input: str = Field(..., description="Legal query text")
        location: Optional[str] = Field(None, description="Location for jurisdiction")
        feedback: Optional[str] = Field(None, description="User feedback")
        session_id: Optional[str] = Field(None, description="Session ID")

    class FeedbackRequest(BaseModel):
        session_id: str = Field(..., description="Session ID")
        rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
        feedback_text: Optional[str] = Field(None, description="Feedback text")

    # Response Models
    class BasicLegalResponse(BaseModel):
        session_id: str
        timestamp: str
        domain: str
        confidence: float
        legal_route: str
        timeline: str
        outcome: str
        process_steps: List[str]
        glossary: Dict[str, str]
        raw_query: str

    class AdaptiveLegalResponse(BaseModel):
        session_id: str
        timestamp: str
        domain: str
        confidence: float
        legal_route: str
        timeline: str
        outcome: str
        process_steps: List[str]
        glossary: Dict[str, str]
        raw_query: str
        learning_applied: bool
        confidence_improvement: Optional[float]
        alternative_domains: Optional[List[str]]

    class EnhancedLegalResponse(BaseModel):
        session_id: str
        timestamp: str
        agent_type: str
        domain: str
        confidence: float
        legal_route: str
        timeline: str
        outcome: str
        process_steps: List[str]
        glossary: Dict[str, str]
        raw_query: str
        location_insights: Optional[str]
        jurisdiction: str
        constitutional_backing: List[str]
        constitutional_articles: List[str]
        risk_assessment: Optional[str]
        estimated_cost: str
        success_rate: float
        alternative_routes: List[str]
        required_documents: List[str]
        crime_data_insights: Optional[str]

    class FeedbackResponse(BaseModel):
        success: bool
        message: str
        feedback_id: str
        timestamp: datetime

    class StatsResponse(BaseModel):
        total_queries: int
        queries_by_agent: Dict[str, int]
        average_confidence: float
        top_domains: List[Dict[str, Any]]
        feedback_stats: Dict[str, Any]
        uptime: str
        last_updated: datetime

    class HealthResponse(BaseModel):
        timestamp: datetime
        agents_available: List[str]

    class APIInfo(BaseModel):
        available_agents: List[Dict[str, Any]]
        endpoints: List[str]

    class AgentInfo(BaseModel):
        name: str
        description: str
        features: List[str]
        recommended_for: List[str]

    class ErrorResponse(BaseModel):
        error: str
        message: str
        timestamp: str
        path: str

    FASTAPI_AVAILABLE = True
except ImportError:
    logger.warning("Pydantic not available, FastAPI models will not be used")
    FASTAPI_AVAILABLE = False

# ============================================================================
# Core Agent Classes
# ============================================================================

class LegalQueryInput:
    """Input class for legal queries"""
    def __init__(self, user_input: str, feedback: Optional[str] = None, session_id: Optional[str] = None):
        self.user_input = user_input
        self.feedback = feedback
        self.session_id = session_id or self._generate_session_id()

    @staticmethod
    def _generate_session_id() -> str:
        return f"session_{uuid.uuid4().hex[:12]}"


class BasicLegalAgent:
    """Basic legal agent for domain classification and guidance"""

    def __init__(self):
        self.domains = {
            "tenant_rights": ["rent", "landlord", "tenant", "eviction", "lease"],
            "employment_law": ["job", "termination", "fired", "workplace", "salary", "contract"],
            "family_law": ["divorce", "child custody", "marriage", "alimony", "adoption"],
            "consumer_protection": ["warranty", "refund", "consumer", "purchase", "defective"],
            "criminal_law": ["arrest", "police", "criminal", "charge", "court"],
            "civil_rights": ["discrimination", "rights", "constitution", "freedom"],
            "immigration_law": ["visa", "immigration", "citizenship", "green card"],
            "business_law": ["contract", "business", "partnership", "corporation"],
            "intellectual_property": ["copyright", "patent", "trademark", "IP"],
            "environmental_law": ["environment", "pollution", "regulation", "compliance"],
            "tax_law": ["tax", "IRS", "income tax", "deduction"],
            "bankruptcy_law": ["bankruptcy", "debt", "creditor", "chapter"]
        }

    def process_query(self, query_input: LegalQueryInput) -> Dict[str, Any]:
        """Process a legal query using basic analysis"""
        try:
            query = query_input.user_input.lower()
            domain = self._classify_domain(query)
            confidence = self._calculate_confidence(query, domain)

            response = {
                "session_id": query_input.session_id,
                "timestamp": datetime.now().isoformat(),
                "domain": domain,
                "confidence": confidence,
                "legal_route": self._get_legal_route(domain),
                "timeline": self._get_timeline(domain),
                "outcome": self._get_outcome_prediction(domain, confidence),
                "process_steps": self._get_process_steps(domain),
                "glossary": self._get_glossary_terms(domain),
                "raw_query": query_input.user_input
            }

            logger.info(f"Basic agent processed query for domain: {domain}")
            return response

        except Exception as e:
            logger.error(f"Basic agent error: {e}")
            raise


class AdaptiveLegalAgent(BasicLegalAgent):
    """Adaptive legal agent with learning capabilities"""

    def __init__(self):
        super().__init__()
        self.learning_data = {}
        self.confidence_history = []

    def process_query_with_learning(self, query_input: LegalQueryInput) -> Dict[str, Any]:
        """Process query with adaptive learning"""
        try:
            # Get basic response first
            response = self.process_query(query_input)

            # Apply learning if feedback is available
            if query_input.feedback:
                self._learn_from_feedback(query_input, response)

            # Enhance response with learning data
            response["learning_applied"] = True
            response["confidence_improvement"] = self._calculate_confidence_improvement(response["domain"])
            response["alternative_domains"] = self._get_alternative_domains(response["domain"])

            logger.info(f"Adaptive agent processed query with learning for domain: {response['domain']}")
            return response

        except Exception as e:
            logger.error(f"Adaptive agent error: {e}")
            raise


class EnhancedLegalAgent(AdaptiveLegalAgent):
    """Enhanced legal agent with constitutional backing and advanced features"""

    def __init__(self):
        super().__init__()
        self.constitutional_backing = {
            "employment_law": ["Due Process Clause", "Equal Protection Clause"],
            "civil_rights": ["First Amendment", "Fourteenth Amendment"],
            "criminal_law": ["Fourth Amendment", "Fifth Amendment", "Sixth Amendment"],
            "family_law": ["Due Process Clause", "Equal Protection Clause"]
        }

    def process_enhanced_query(self, user_query: str, location: Optional[str] = None,
                             collect_feedback: bool = False) -> Dict[str, Any]:
        """Process enhanced legal query"""
        try:
            # Create query input
            query_input = LegalQueryInput(
                user_input=user_query,
                feedback=None,
                session_id=f"enhanced_{uuid.uuid4().hex[:12]}"
            )

            # Get basic response
            response = self.process_query(query_input)

            # Add enhanced features
            domain = response["domain"]
            response.update({
                "jurisdiction": location or "General",
                "constitutional_backing": self.constitutional_backing.get(domain, []),
                "constitutional_articles": self._get_constitutional_articles(domain),
                "estimated_cost": self._calculate_cost_estimate(domain, response["confidence"]),
                "success_rate": self._calculate_success_rate(domain),
                "alternative_routes": self._get_alternative_routes(domain),
                "required_documents": self._get_required_documents(domain),
                "timeline_range": self._get_timeline_range(domain)
            })

            logger.info(f"Enhanced agent processed query for domain: {domain}")
            return response

        except Exception as e:
            logger.error(f"Enhanced agent error: {e}")
            raise


# ============================================================================
# Agent Factory Functions
# ============================================================================

def create_legal_agent() -> BasicLegalAgent:
    """Create and return basic legal agent"""
    return BasicLegalAgent()


def create_adaptive_legal_agent() -> AdaptiveLegalAgent:
    """Create and return adaptive legal agent"""
    return AdaptiveLegalAgent()


def create_enhanced_legal_agent() -> EnhancedLegalAgent:
    """Create and return enhanced legal agent"""
    return EnhancedLegalAgent()


# ============================================================================
# Basket System Integration
# ============================================================================

async def process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main processing function for basket system integration
    Now makes HTTP requests to Render API instead of local processing

    Args:
        input_data: Dictionary containing query parameters

    Returns:
        Dictionary containing legal analysis results from Render API
    """
    try:
        logger.info("Law Agent forwarding request to Render API")

        # Extract parameters
        query = input_data.get("query", "")
        agent_type = input_data.get("agent_type", "basic")
        location = input_data.get("location")
        feedback = input_data.get("feedback", False)

        if not query:
            return {"error": "No query provided"}

        # Render API base URL
        base_url = "https://legal-agent-api-3yqg.onrender.com"
        
        # Determine endpoint based on agent type
        if agent_type == "enhanced":
            endpoint = f"{base_url}/enhanced-query"
            payload = {
                "user_input": query,
                "location": location,
                "feedback": str(feedback) if feedback else None,
                "session_id": f"basket_{uuid.uuid4().hex[:12]}"
            }
        elif agent_type == "adaptive":
            endpoint = f"{base_url}/adaptive-query"
            payload = {
                "user_input": query,
                "enable_learning": True,
                "feedback": str(feedback) if feedback else None,
                "session_id": f"basket_{uuid.uuid4().hex[:12]}"
            }
        else:  # basic
            endpoint = f"{base_url}/basic-query"
            payload = {
                "user_input": query,
                "feedback": str(feedback) if feedback else None,
                "session_id": f"basket_{uuid.uuid4().hex[:12]}"
            }

        # Make HTTP request to Render API
        logger.info(f"Making request to {endpoint} with payload: {payload}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully received response from Render API for {agent_type} agent")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Render API error {response.status}: {error_text}")
                    return {
                        "error": f"Render API error: {response.status}",
                        "details": error_text,
                        "agent_type": "law_agent"
                    }

    except aiohttp.ClientTimeout:
        logger.error("Timeout connecting to Render API")
        return {"error": "Timeout connecting to legal service", "agent_type": "law_agent"}
    except Exception as e:
        logger.error(f"Law Agent API forwarding error: {e}")
        return {"error": str(e), "agent_type": "law_agent"}


# ============================================================================
# FastAPI Integration (if available)
# ============================================================================

# Global variables for FastAPI
_basic_agent = None
_adaptive_agent = None
_enhanced_agent = None

_stats = {
    "total_queries": 0,
    "queries_by_agent": {"basic": 0, "adaptive": 0, "enhanced": 0},
    "start_time": datetime.now(),
    "feedback_count": 0,
    "error_count": 0
}

def get_basic_agent():
    """Get or create basic agent instance"""
    global _basic_agent
    if _basic_agent is None:
        try:
            _basic_agent = create_legal_agent()
            logger.info("Basic agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize basic agent: {e}")
            raise
    return _basic_agent

def get_adaptive_agent():
    """Get or create adaptive agent instance"""
    global _adaptive_agent
    if _adaptive_agent is None:
        try:
            _adaptive_agent = create_adaptive_legal_agent()
            logger.info("Adaptive agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize adaptive agent: {e}")
            raise
    return _adaptive_agent

def get_enhanced_agent():
    """Get or create enhanced agent instance"""
    global _enhanced_agent
    if _enhanced_agent is None:
        try:
            _enhanced_agent = create_enhanced_legal_agent()
            logger.info("Enhanced agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced agent: {e}")
            raise
    return _enhanced_agent

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{uuid.uuid4().hex[:12]}"

def update_stats(agent_type: str):
    """Update usage statistics"""
    _stats["total_queries"] += 1
    _stats["queries_by_agent"][agent_type] += 1

# ============================================================================
# Standalone FastAPI Server (if FastAPI available)
# ============================================================================

if FASTAPI_AVAILABLE:
    try:
        from fastapi import FastAPI, HTTPException, Request, status
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        import uvicorn

        # Create FastAPI app
        app = FastAPI(
            title="Law Agent API",
            description="AI-Powered Legal Assistance API",
            version="1.0.0",
        )

        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # API Endpoints
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return HealthResponse(
                timestamp=datetime.now(),
                agents_available=["basic", "adaptive", "enhanced"]
            )

        @app.post("/basic-query", response_model=BasicLegalResponse)
        async def process_basic_query(request: BasicLegalQueryRequest):
            """Process a legal query using the basic agent"""
            try:
                agent = get_basic_agent()
                update_stats("basic")

                session_id = request.session_id or generate_session_id()
                query_input = LegalQueryInput(
                    user_input=request.user_input,
                    feedback=request.feedback,
                    session_id=session_id
                )

                response = agent.process_query(query_input)
                return BasicLegalResponse(**response)

            except Exception as e:
                logger.error(f"Basic query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/adaptive-query", response_model=AdaptiveLegalResponse)
        async def process_adaptive_query(request: AdaptiveLegalQueryRequest):
            """Process a legal query using the adaptive agent"""
            try:
                agent = get_adaptive_agent()
                update_stats("adaptive")

                session_id = request.session_id or generate_session_id()
                query_input = LegalQueryInput(
                    user_input=request.user_input,
                    feedback=request.feedback,
                    session_id=session_id
                )

                response = agent.process_query_with_learning(query_input)
                return AdaptiveLegalResponse(**response)

            except Exception as e:
                logger.error(f"Adaptive query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/enhanced-query", response_model=EnhancedLegalResponse)
        async def process_enhanced_query(request: EnhancedLegalQueryRequest):
            """Process a legal query using the enhanced agent"""
            try:
                agent = get_enhanced_agent()
                update_stats("enhanced")

                response = agent.process_enhanced_query(
                    user_query=request.user_input,
                    location=request.location,
                    collect_feedback=bool(request.feedback)
                )

                # Convert response to API format
                api_response = {
                    "session_id": response["session_id"],
                    "timestamp": response["timestamp"],
                    "agent_type": "enhanced",
                    "domain": response["domain"],
                    "confidence": response["confidence"],
                    "legal_route": response["legal_route"],
                    "timeline": f"{response['timeline_range'][0]}-{response['timeline_range'][1]} days",
                    "outcome": response["outcome"],
                    "process_steps": response["process_steps"],
                    "glossary": response["glossary"],
                    "raw_query": response["raw_query"],
                    "location_insights": f"Jurisdiction-specific guidance for {response['jurisdiction']}",
                    "jurisdiction": response["jurisdiction"],
                    "constitutional_backing": response["constitutional_backing"],
                    "constitutional_articles": response["constitutional_articles"],
                    "risk_assessment": f"Risk level based on case complexity and success rate: {response['success_rate']:.0%}",
                    "estimated_cost": f"₹{response['estimated_cost'][0]:,} - ₹{response['estimated_cost'][1]:,}",
                    "success_rate": response["success_rate"],
                    "alternative_routes": response["alternative_routes"],
                    "required_documents": response["required_documents"],
                    "crime_data_insights": "No crime data applicable for this case type"
                }

                return EnhancedLegalResponse(**api_response)

            except Exception as e:
                logger.error(f"Enhanced query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/stats", response_model=StatsResponse)
        async def get_statistics():
            """Get API usage statistics"""
            uptime_seconds = (datetime.now() - _stats["start_time"]).total_seconds()
            uptime_hours = uptime_seconds / 3600
            uptime_str = f"{uptime_hours:.1f} hours"

            return StatsResponse(
                total_queries=_stats["total_queries"],
                queries_by_agent=_stats["queries_by_agent"],
                average_confidence=0.75,
                top_domains=[],
                feedback_stats={"total_feedback": _stats["feedback_count"]},
                uptime=uptime_str,
                last_updated=datetime.now()
            )

        logger.info("FastAPI endpoints configured for Law Agent")

    except ImportError:
        logger.warning("FastAPI not available, web server functionality disabled")
        app = None

else:
    logger.warning("FastAPI dependencies not available")
    app = None


# ============================================================================
# Helper Methods for Agent Classes
# ============================================================================

# Add helper methods to BasicLegalAgent
def _classify_domain(self, query: str) -> str:
    """Classify the legal domain based on query content"""
    max_score = 0
    best_domain = "general_law"

    for domain, keywords in self.domains.items():
        score = sum(1 for keyword in keywords if keyword in query)
        if score > max_score:
            max_score = score
            best_domain = domain

    return best_domain

def _calculate_confidence(self, query: str, domain: str) -> float:
    """Calculate confidence score for domain classification"""
    keywords = self.domains.get(domain, [])
    matched_keywords = sum(1 for keyword in keywords if keyword in query)
    total_keywords = len(keywords)

    if total_keywords == 0:
        return 0.5

    confidence = min(matched_keywords / total_keywords, 1.0)
    return max(confidence, 0.3)  # Minimum confidence of 0.3

def _get_legal_route(self, domain: str) -> str:
    """Get recommended legal route for domain"""
    routes = {
        "tenant_rights": "File complaint with housing authority or small claims court",
        "employment_law": "File complaint with labor department or EEOC",
        "family_law": "Consult family law attorney or file petition in family court",
        "criminal_law": "Contact criminal defense attorney immediately",
        "civil_rights": "File complaint with civil rights commission",
        "business_law": "Consult business attorney for contract review",
        "tax_law": "Consult tax professional or file appeal with IRS"
    }
    return routes.get(domain, "Consult with legal professional")

def _get_timeline(self, domain: str) -> str:
    """Get typical timeline for legal process"""
    timelines = {
        "tenant_rights": "30-90 days",
        "employment_law": "60-180 days",
        "family_law": "90-365 days",
        "criminal_law": "30-365 days",
        "civil_rights": "90-365 days",
        "business_law": "30-180 days",
        "tax_law": "60-365 days"
    }
    return timelines.get(domain, "Varies by case complexity")

def _get_outcome_prediction(self, domain: str, confidence: float) -> str:
    """Predict possible outcomes based on domain and confidence"""
    if confidence > 0.8:
        return "High likelihood of favorable outcome"
    elif confidence > 0.6:
        return "Moderate chance of success"
    else:
        return "Case depends on specific circumstances"

def _get_process_steps(self, domain: str) -> List[str]:
    """Get typical process steps for domain"""
    steps = {
        "tenant_rights": ["Gather evidence", "Document communications", "File complaint", "Attend hearing", "Follow up"],
        "employment_law": ["Document incidents", "File complaint", "Mediation", "Investigation", "Resolution"],
        "family_law": ["Gather documents", "File petition", "Serve other party", "Discovery", "Trial/Settlement"],
        "criminal_law": ["Contact attorney", "Prepare defense", "Pre-trial motions", "Trial", "Sentencing"],
        "civil_rights": ["Document discrimination", "File complaint", "Investigation", "Mediation", "Resolution"]
    }
    return steps.get(domain, ["Consult legal professional", "Gather evidence", "File appropriate paperwork", "Follow legal process"])

def _get_glossary_terms(self, domain: str) -> Dict[str, str]:
    """Get relevant legal glossary terms for domain"""
    glossaries = {
        "tenant_rights": {
            "eviction": "Legal process to remove a tenant from rental property",
            "lease": "Contract between landlord and tenant",
            "security_deposit": "Money held by landlord as guarantee"
        },
        "employment_law": {
            "wrongful_termination": "Termination that violates employment laws",
            "at-will_employment": "Employment that can be terminated by either party",
            "constructive_discharge": "Work conditions so intolerable employee resigns"
        },
        "criminal_law": {
            "due_process": "Legal requirement for fair treatment through normal judicial system",
            "probable_cause": "Reasonable belief that crime has been committed",
            "arraignment": "First court appearance where charges are read"
        }
    }
    return glossaries.get(domain, {})

# Add methods to BasicLegalAgent class
BasicLegalAgent._classify_domain = _classify_domain
BasicLegalAgent._calculate_confidence = _calculate_confidence
BasicLegalAgent._get_legal_route = _get_legal_route
BasicLegalAgent._get_timeline = _get_timeline
BasicLegalAgent._get_outcome_prediction = _get_outcome_prediction
BasicLegalAgent._get_process_steps = _get_process_steps
BasicLegalAgent._get_glossary_terms = _get_glossary_terms

# Add adaptive methods
def _learn_from_feedback(self, query_input: LegalQueryInput, response: Dict[str, Any]):
    """Learn from user feedback to improve future responses"""
    domain = response["domain"]
    if domain not in self.learning_data:
        self.learning_data[domain] = {"feedback_count": 0, "avg_confidence": 0}

    self.learning_data[domain]["feedback_count"] += 1
    self.learning_data[domain]["avg_confidence"] = (
        (self.learning_data[domain]["avg_confidence"] * (self.learning_data[domain]["feedback_count"] - 1)) +
        response["confidence"]
    ) / self.learning_data[domain]["feedback_count"]

def _calculate_confidence_improvement(self, domain: str) -> Optional[float]:
    """Calculate confidence improvement from learning"""
    if domain in self.learning_data and self.learning_data[domain]["feedback_count"] > 1:
        return self.learning_data[domain]["avg_confidence"] - 0.5  # Compare to baseline
    return None

def _get_alternative_domains(self, domain: str) -> Optional[List[str]]:
    """Get alternative domains based on learning data"""
    alternatives = []
    for d, data in self.learning_data.items():
        if d != domain and data["feedback_count"] > 2:
            alternatives.append(d)
    return alternatives[:3] if alternatives else None

AdaptiveLegalAgent._learn_from_feedback = _learn_from_feedback
AdaptiveLegalAgent._calculate_confidence_improvement = _calculate_confidence_improvement
AdaptiveLegalAgent._get_alternative_domains = _get_alternative_domains

# Add enhanced methods
def _get_constitutional_articles(self, domain: str) -> List[str]:
    """Get constitutional articles relevant to domain"""
    articles = {
        "employment_law": ["Article I, Section 8", "Fourteenth Amendment"],
        "civil_rights": ["First Amendment", "Fourteenth Amendment", "Fifteenth Amendment"],
        "criminal_law": ["Fourth Amendment", "Fifth Amendment", "Sixth Amendment", "Eighth Amendment"],
        "family_law": ["Fourteenth Amendment", "Nineteenth Amendment"]
    }
    return articles.get(domain, [])

def _calculate_cost_estimate(self, domain: str, confidence: float) -> tuple:
    """Calculate estimated cost range for legal process"""
    base_costs = {
        "tenant_rights": (500, 2000),
        "employment_law": (2000, 10000),
        "family_law": (3000, 15000),
        "criminal_law": (5000, 25000),
        "civil_rights": (3000, 20000),
        "business_law": (2000, 50000),
        "tax_law": (1000, 10000)
    }

    base_range = base_costs.get(domain, (1000, 5000))
    # Adjust based on confidence (higher confidence might mean simpler cases)
    adjustment = 1 - (confidence - 0.5) * 0.4 if confidence > 0.5 else 1 + (0.5 - confidence) * 0.4

    return (
        int(base_range[0] * adjustment),
        int(base_range[1] * adjustment)
    )

def _calculate_success_rate(self, domain: str) -> float:
    """Calculate success rate for domain"""
    success_rates = {
        "tenant_rights": 0.7,
        "employment_law": 0.6,
        "family_law": 0.65,
        "criminal_law": 0.5,
        "civil_rights": 0.55,
        "business_law": 0.75,
        "tax_law": 0.8
    }
    return success_rates.get(domain, 0.6)

def _get_alternative_routes(self, domain: str) -> List[str]:
    """Get alternative legal routes for domain"""
    alternatives = {
        "tenant_rights": ["Mediation", "Rent escrow", "Repair and deduct", "Small claims court"],
        "employment_law": ["Direct negotiation", "Mediation", "Arbitration", "Class action lawsuit"],
        "family_law": ["Mediation", "Collaborative law", "Arbitration", "Litigation"],
        "criminal_law": ["Plea bargain", "Trial", "Appeal"],
        "civil_rights": ["Administrative complaint", "Federal lawsuit", "State court action"]
    }
    return alternatives.get(domain, ["Consult legal professional for options"])

def _get_required_documents(self, domain: str) -> List[str]:
    """Get required documents for legal process"""
    documents = {
        "tenant_rights": ["Lease agreement", "Rent payment records", "Correspondence with landlord", "Photos of issues"],
        "employment_law": ["Employment contract", "Pay stubs", "Performance reviews", "Termination letter", "Witness statements"],
        "family_law": ["Marriage certificate", "Financial statements", "Child custody agreements", "Property deeds"],
        "criminal_law": ["Police report", "Arrest warrant", "Witness statements", "Evidence documentation"],
        "business_law": ["Business contracts", "Financial records", "Partnership agreements", "Corporate documents"]
    }
    return documents.get(domain, ["Gather all relevant documentation and evidence"])

def _get_timeline_range(self, domain: str) -> tuple:
    """Get timeline range in days for domain"""
    timelines = {
        "tenant_rights": (30, 90),
        "employment_law": (60, 180),
        "family_law": (90, 365),
        "criminal_law": (30, 730),
        "civil_rights": (90, 365),
        "business_law": (30, 180),
        "tax_law": (60, 365)
    }
    return timelines.get(domain, (30, 180))

EnhancedLegalAgent._get_constitutional_articles = _get_constitutional_articles
EnhancedLegalAgent._calculate_cost_estimate = _calculate_cost_estimate
EnhancedLegalAgent._calculate_success_rate = _calculate_success_rate
EnhancedLegalAgent._get_alternative_routes = _get_alternative_routes
EnhancedLegalAgent._get_required_documents = _get_required_documents
EnhancedLegalAgent._get_timeline_range = _get_timeline_range


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run as standalone FastAPI server if available
    if app is not None:
        logger.info("Starting Law Agent as FastAPI server...")
        logger.info("API Documentation available at: http://localhost:8000/docs")

        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(
            "law_agent:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )
    else:
        logger.error("Cannot start FastAPI server - dependencies not available")
        logger.info("Law Agent available for basket system integration only")
