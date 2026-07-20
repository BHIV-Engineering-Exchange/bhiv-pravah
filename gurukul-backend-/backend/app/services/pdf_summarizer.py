"""
Multi-Page PDF Summarizer using LED (Longformer Encoder-Decoder)
Uses 'pszemraj/led-base-book-summary' for long-context summarization.
Supports loading from pickle files (quantized) for deployment.

NOTE: This module is DISABLED in lightweight deployments (no torch/transformers).
"""

import os
import pickle
import gzip
from typing import List, Dict
from pathlib import Path

# Optional ML imports - may not be installed in lightweight deployment
try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    torch = None
    print("[PDF Summarizer] torch/transformers not installed. Summarizer disabled.")

class PDFSummarizer:
    """PDF summarizer using LED-Base-Book-Summary (Supports long context)"""
    
    def __init__(self, model_name: str = "pszemraj/led-base-book-summary", use_pickle: bool = True):
        if not ML_AVAILABLE:
            print("[PDF Summarizer] DISABLED - torch/transformers not installed")
            self.model = None
            self.tokenizer = None
            self.pipe = None
            return
            
        print("\n" + "!"*60)
        print("!!! INITIALIZING LOCAL PDF SUMMARIZER (LED MODEL) !!!")
        print("!!! This runs on your GPU/CPU. NO API KEY USED. !!!")
        print("!"*60 + "\n")
        
        self.model_name = model_name
        self.use_pickle = use_pickle
        
        # Check for GPU availability
        if torch.cuda.is_available():
            self.device = 0
            self.dtype = torch.float16
            print(f"[PDF Summarizer] GPU Detected: {torch.cuda.get_device_name(0)}")
        else:
            self.device = -1
            self.dtype = torch.float32
            print("[PDF Summarizer] No GPU detected. Running on CPU.")

        # Try loading from pickle first
        if self.use_pickle:
            # Models are in backend/models (2 dirs up from services/pdf_summarizer.py -> app -> backend)
            # Actually __file__ is app/services/pdf_summarizer.py. Parent is app/services.
            # We need to go up to backend root? 
            # Original: backend/models.
            # New structure: backend/app/services. 
            # So ../../models from here?
            # Path(__file__).parent is .../app/services
            # .parent.parent is .../app
            # .parent.parent.parent is .../backend
            pickle_path = Path(__file__).parent.parent.parent / "models" / "led_model_quantized.pkl.gz"
            if pickle_path.exists():
                print(f"[PDF Summarizer] Loading from pickle file: {pickle_path}")
                try:
                    self._load_from_pickle(pickle_path)
                    print("[PDF Summarizer] ✓ Model loaded from pickle successfully!")
                    return
                except Exception as e:
                    print(f"[PDF Summarizer] Failed to load from pickle: {e}")
                    print("[PDF Summarizer] Falling back to HuggingFace download...")
            else:
                print(f"[PDF Summarizer] Pickle file not found: {pickle_path}")
                print("[PDF Summarizer] Falling back to HuggingFace download...")

        # Fallback: Load from HuggingFace
        print(f"[PDF Summarizer] Loading model from HuggingFace: {model_name}...")
        try:
            # 1. Load Tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            # 2. Load Model
            try:
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name, 
                    torch_dtype=self.dtype,
                    weights_only=False
                ).to("cuda:0" if self.device == 0 else "cpu")
            except Exception as e:
                print(f"[PDF Summarizer] Primary load failed, retrying: {e}")
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name, 
                    torch_dtype=self.dtype
                ).to("cuda:0" if self.device == 0 else "cpu")

            # 3. Create Pipeline
            self.summarizer = pipeline(
                "summarization", 
                model=model,
                tokenizer=tokenizer,
                device=self.device
            )
            print("[PDF Summarizer] LED Model loaded successfully!")
        except Exception as e:
            print(f"[PDF Summarizer] Error loading model: {e}")
            self.summarizer = None
    
    def _load_from_pickle(self, pickle_path: Path):
        """Load model and tokenizer from compressed pickle file"""
        print("[PDF Summarizer] Decompressing and loading pickle file...")
        
        with gzip.open(pickle_path, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        tokenizer = model_data['tokenizer']
        
        # Move model to appropriate device
        if self.device == 0 and torch.cuda.is_available():
            model = model.cuda()
        else:
            model = model.cpu()
        
        # Create pipeline
        self.summarizer = pipeline(
            "summarization",
            model=model,
            tokenizer=tokenizer,
            device=self.device
        )

    def summarize_text(self, text: str, summary_type: str = "detailed") -> str:
        """Summarize a large chunk of text using LED's 32k context window."""
        if not text or not text.strip():
            return ""
            
        # Define parameters based on summary type
        # LED produces longer, more detailed summaries naturally
        if summary_type == "concise":
            max_len = 128
            min_len = 32
        elif summary_type == "detailed":
            max_len = 512
            min_len = 128
        elif summary_type == "comprehensive":
            max_len = 1024
            min_len = 256
        else:
            max_len = 512
            min_len = 64
            
        try:
            # LED Context Window is 16k/32k tokens
            # We'll use a safe large limit
            max_input_chars = 30000 
            
            # Prepend instruction to encourage bullet points or structure
            # Note: LED is trained on books, so it prefers paragraphs. 
            # We will use post-processing to ensure bullet points if the model generates prose.
            input_text = "Summarize the following content in detailed key points:\n\n" + text[:max_input_chars]
            
            # Generate summary
            summary_output = self.summarizer(
                input_text, 
                max_length=max_len, 
                min_length=min_len, 
                do_sample=False, 
                truncation=True,
                num_beams=2,
                repetition_penalty=3.0,
                no_repeat_ngram_size=3,
                encoder_no_repeat_ngram_size=3,
                length_penalty=0.8
            )
            
            raw_summary = summary_output[0]['summary_text']
            
            # Post-processing: If user wants points but model gave paragraph, try to split sentences
            if summary_type in ['detailed', 'comprehensive'] and not raw_summary.strip().startswith("-"):
                # Split by periods followed by space to create points
                sentences = raw_summary.replace(". ", ".\n- ").split("\n")
                # Ensure starts with dash
                if not sentences[0].strip().startswith("-"):
                    sentences[0] = "- " + sentences[0]
                return "\n".join(sentences)
                
            return raw_summary
        except Exception as e:
            print(f"[PDF Summarizer] Error generating summary: {e}")
            return f"Error: {str(e)}"

    def summarize_all_pages(self, pages: List[str], summary_type: str = "detailed", improve_grammar: bool = False) -> Dict:
        """
        Summarize pages individually and create an overall summary.
        """
        if not self.summarizer:
             return {
                "page_summaries": [],
                "overall_summary": "Error: Model not initialized.",
                "total_pages": len(pages),
                "pages_summarized": 0,
                "summary_type": summary_type,
                "provider": "local/led-large"
            }

        print(f"[PDF Summarizer] Summarizing {len(pages)} pages with LED (Type: {summary_type})...")
        
        formatted_page_summaries = []
        all_summaries_text = []

        # Summarize each page
        for i, page_text in enumerate(pages, 1):
            if not page_text:
                continue
                
            summary = self.summarize_text(page_text, summary_type)
            
            # Clean up potential artifacts
            summary = summary.replace(" .", ".").replace(" ,", ",")
            
            formatted_page_summaries.append({
                "page_number": i,
                "summary": summary,
                "original_length": len(page_text),
                "summary_length": len(summary)
            })
            all_summaries_text.append(summary)

        # Overall Summary
        # For overall, we combine the page summaries. 
        # Since LED has a huge context, we can likely fit ALL 5-10 pages of summaries easily.
        combined_text = " ".join(all_summaries_text)
        overall_summary = self.summarize_text(combined_text, "comprehensive" if summary_type == "comprehensive" else "detailed")

        print("[PDF Summarizer] LED processing complete!")
        
        return {
            "page_summaries": formatted_page_summaries,
            "overall_summary": overall_summary,
            "total_pages": len(pages),
            "pages_summarized": len(formatted_page_summaries),
            "summary_type": summary_type,
            "provider": "local/led-large-32k",
            "success": True
        }

import io
from fastapi import UploadFile
import PyPDF2

async def extract_pages_from_pdf(file: UploadFile) -> List[str]:
    # Extract text from uploaded PDF file, page by page.
    pages_text = []
    
    try:
        # Read file content
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        # Reset cursor
        await file.seek(0)
        
        reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(reader.pages)
        
        print(f'[PDF Extract] PDF has {num_pages} pages.')
        
        for i in range(num_pages):
            page = reader.pages[i]
            text = page.extract_text()
            if text:
                pages_text.append(text)
            else:
                pages_text.append('') # Keep index alignment
                
        return pages_text
        
    except Exception as e:
        print(f'[PDF Extract] Error extracting text: {e}')
        raise e

