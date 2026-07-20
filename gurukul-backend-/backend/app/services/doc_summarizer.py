"""
Multi-Section DOC Summarizer using Google Gemini API
Replaces Groq to avoid Rate Limiting and leverage large context window.
"""

import os
import google.generativeai as genai
import json
from typing import List, Dict, Optional
import time
import warnings

# Suppress Google GenAI deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

class DOCSummarizer:
    """Cloud-based DOC summarizer using Google Gemini API"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("[DOC Summarizer] WARNING: GEMINI_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test model validity with a dummy call
                # self.model.generate_content("test") 
            except Exception as e:
                print(f"[DOC Summarizer] Warning: Failed to load model '{model_name}': {e}. Falling back to 'gemini-flash-latest'...")
                self.model = genai.GenerativeModel("gemini-flash-latest")

    def summarize_all_sections(self, sections: List[str], summary_type: str = "detailed") -> Dict:
        """
        Summarize ALL sections in a single API call using Gemini's large context window.
        Returns a dictionary matching the expected structure.
        """
        if not self.api_key:
            return {
                "section_summaries": [],
                "overall_summary": "Error: GEMINI_API_KEY not configured.",
                "total_sections": len(sections),
                "sections_summarized": 0,
                "summary_type": summary_type
            }

        print(f"[DOC Summarizer] Preparing to summarize {len(sections)} sections using Gemini...")

        # 1. Construct a single large prompt with all section content
        full_text_content = ""
        for i, section_text in enumerate(sections, 1):
            full_text_content += f"\n--- START OF SECTION {i} ---\n{section_text}\n--- END OF SECTION {i} ---\n"

        # 2. Define the prompt for structured JSON output
        prompt = f"""
        You are an expert document summarizer. 
        I will provide the text content of a Word document, separated by section markers.
        
        Your task is to:
        1. Create a detailed overall summary of the ENTIRE document.
        2. Create a brief summary for EACH individual section.
        
        Output format: JSON object with keys "overall_summary" (string) and "section_summaries" (list of strings, in section order).
        
        Summary requirements:
        - Overall summary should be comprehensive.
        - Section summaries should be concise (2-3 sentences max).
        - Maintain the original meaning and context.
        - Do not use markdown formatting in the JSON string values.
        
        Document Content:
        {full_text_content}
        """

        try:
            # 3. Call Gemini API
            # 3. Call Gemini API
            print("[DOC Summarizer] Sending request to Gemini...")
            try:
                response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            except Exception as e:
                # Dynamic fallback for "404 Model Not Found" errors during runtime
                if "404" in str(e) or "not found" in str(e).lower():
                    print("[DOC Summarizer] Primary model failed (404). Switching to fallback 'gemini-flash-latest' and retrying...")
                    self.model = genai.GenerativeModel("gemini-flash-latest")
                    response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                else:
                    raise e
            
            # 4. Parse Response
            try:
                result = json.loads(response.text)
                overall_summary = result.get("overall_summary", "Summary generation failed to return overall summary.")
                raw_section_summaries = result.get("section_summaries", [])
            except json.JSONDecodeError:
                # Fallback if valid JSON wasn't returned
                print("[DOC Summarizer] Failed to parse JSON response. Falling back to raw text.")
                overall_summary = response.text
                raw_section_summaries = []

            # 5. Format output for existing backend structure
            formatted_section_summaries = []
            
            # Map raw summaries back to sections
            for i, section_text in enumerate(sections, 1):
                raw_summary = raw_section_summaries[i-1] if i <= len(raw_section_summaries) else "Summary not generated for this section."
                
                formatted_section_summaries.append({
                    "section_number": i,
                    "summary": raw_summary,
                    "original_length": len(section_text) if section_text else 0,
                    "summary_length": len(raw_summary)
                })

            print("[DOC Summarizer] Gemini processing complete!")
            
            return {
                "section_summaries": formatted_section_summaries,
                "overall_summary": overall_summary,
                "total_sections": len(sections),
                "sections_summarized": len(formatted_section_summaries),
                "summary_type": summary_type
            }

        except Exception as e:
            print(f"[DOC Summarizer] Error calling Gemini: {str(e)}")
            return {
                "section_summaries": [],
                "overall_summary": f"Error during summarization: {str(e)}",
                "total_sections": len(sections),
                "sections_summarized": 0,
                "summary_type": summary_type
            }
