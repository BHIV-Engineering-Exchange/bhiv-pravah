
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.all_models import User, Summary as DBSummary
from app.services.ems_sync import ems_sync
from typing import Optional
from app.schemas.summary import (
    PDFSummarizerResponse, DOCSummarizerResponse,
    SummarizerRequest, SummarizerResponse
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Import specific summarizers
try:
    from app.services.doc_summarizer import DOCSummarizer
    DOC_SUMMARIZER_SUPPORT = True
except ImportError:
    DOC_SUMMARIZER_SUPPORT = False

from app.services.pdf_summarizer import PDFSummarizer, extract_pages_from_pdf

router = APIRouter()

# Global instance for caching the model
_pdf_summarizer_instance = None

def get_pdf_summarizer():
    global _pdf_summarizer_instance
    if _pdf_summarizer_instance is None:
        print("[Router] Initializing Global PDFSummarizer instance...")
        _pdf_summarizer_instance = PDFSummarizer()
    return _pdf_summarizer_instance

@router.post("/summarize-pdf", response_model=PDFSummarizerResponse)
async def summarize_pdf(
    file: UploadFile = File(...),
    summary_type: str = Form("detailed"),
    improve_grammar: bool = Form(False),
    save_summary: bool = Form(False),
    summary_title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Summarize an uploaded PDF file using local transformer model.
    """
    print(f"\n[API] Received /summarize-pdf request for file: {file.filename}")

    if not settings.PDF_SUMMARIZER_SUPPORT and False: # Force True for now as config has False by default but user had it working?
         # logic in original main.py seemed to check import. 
         pass
    
    # 1. Extract Text
    try:
        pages = await extract_pages_from_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
        
    if not pages:
        raise HTTPException(status_code=400, detail="No text could be extracted from this PDF.")

    # 2. Initialize Summarizer
    try:
        # Use cached global instance
        summarizer = get_pdf_summarizer()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize summarizer model: {str(e)}")

    # 3. Generate Summary
    try:
        result = summarizer.summarize_all_pages(pages, summary_type=summary_type, improve_grammar=improve_grammar)
        
        # Add success flag if not present
        if "success" not in result:
            result["success"] = True
            
        # Always save summary to DB (enable sync to EMS)
        summary_title_final = summary_title or f"PDF Summary - {file.filename}"
        summary_content = result.get("overall_summary", "")
        
        new_summary = DBSummary(
            user_id=current_user.id,
            title=summary_title_final,
            content=summary_content,
            source=file.filename,
            source_type="pdf"
        )
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)
        
        # Sync to EMS asynchronously (don't block response)
        try:
            # Get school_id from user if available
            school_id = getattr(current_user, 'school_id', None)

            ems_sync_result = await ems_sync.sync_summary(
                gurukul_id=new_summary.id,
                student_email=current_user.email,
                school_id=school_id,
                title=summary_title_final,
                content=summary_content,
                source=file.filename,
                source_type="pdf"
            )
            
            if ems_sync_result:
                # Store EMS sync ID in metadata if needed
                new_summary.metadata_ = new_summary.metadata_ or {}
                new_summary.metadata_["ems_sync_id"] = ems_sync_result.get("id")
                db.commit()
                logger.info(f"Synced summary {new_summary.id} to EMS")
        except Exception as e:
            logger.error(f"Failed to sync summary {new_summary.id} to EMS: {str(e)}")
            # Don't fail the request if sync fails
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
