# BHIV HR Platform - AI Agent Service Package
# Version: 3.0.0-phase3-production
# Updated: October 13, 2025
# Status: Offline (Production deployment issues)

"""
BHIV HR Platform AI Agent Service

Advanced AI-powered candidate matching with:
- Phase 3 semantic engine with sentence transformers
- Company preference learning and optimization
- Cultural fit analysis and scoring
- Enhanced batch processing (50 candidates/chunk)
- Real-time AI matching (<0.02s with caching)

Production Status: OFFLINE
Issue: Heavy ML dependencies (torch ~755MB) exceed Render free tier
Fallback: Gateway provides database-based matching
Endpoints: 6 total (when operational)
"""

__version__ = "3.0.0-phase3-production"
__status__ = "Offline"
__updated__ = "2025-10-13"
__issue__ = "ML dependencies exceed platform limits"
