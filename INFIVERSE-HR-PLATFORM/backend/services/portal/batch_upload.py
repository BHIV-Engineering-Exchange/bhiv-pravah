import streamlit as st
import os
from pathlib import Path
import zipfile
import tempfile
import httpx
import json
import logging
# from werkzeug.utils import secure_filename
# Use simple filename sanitization instead
def secure_filename(filename):
    """Simple filename sanitization"""
    import re
    filename = re.sub(r'[^\w\s-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_BATCH = 50

def validate_file(uploaded_file):
    """Validate uploaded file for security and size"""
    if not uploaded_file:
        return False
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False
    
    # Check file extension
    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True

def is_safe_path(path):
    """Check if path is safe (no path traversal)"""
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    
    # Check for path traversal patterns
    if '..' in normalized or normalized.startswith('/') or ':' in normalized:
        return False
    
    return True

def show_batch_upload():
    """Batch resume upload interface"""
    st.header("📁 Batch Resume Upload")
    
    upload_method = st.radio("Upload Method", ["Individual Files", "Zip Archive", "Folder Scan"])
    
    if upload_method == "Individual Files":
        uploaded_files = st.file_uploader(
            "Choose resume files",
            type=['pdf', 'docx', 'doc', 'txt'],
            accept_multiple_files=True,
            help="Select multiple resume files to upload"
        )
        
        if uploaded_files:
            st.success(f"Selected {len(uploaded_files)} files")
            
            if st.button("Process All Resumes"):
                process_uploaded_files(uploaded_files)
    
    elif upload_method == "Zip Archive":
        zip_file = st.file_uploader("Upload ZIP file containing resumes", type=['zip'])
        
        if zip_file:
            if st.button("Extract and Process"):
                process_zip_file(zip_file)
    
    elif upload_method == "Folder Scan":
        st.info("📂 Folder Scan Mode")
        st.write("This will scan the resume/ folder for new files")
        
        if st.button("Scan Resume Folder"):
            scan_resume_folder()

def process_uploaded_files(uploaded_files):
    """Process individual uploaded files"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Ensure resume folder exists with proper permissions
        resume_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resume")
        resume_folder = Path(resume_dir)
        resume_folder.mkdir(parents=True, exist_ok=True)
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Validate and secure file handling
            if not validate_file(uploaded_file):
                st.error(f"❌ Invalid file: {uploaded_file.name}")
                continue
            
            # Secure filename and save
            secure_name = secure_filename(uploaded_file.name)
            if not secure_name:
                secure_name = f"resume_{i}_{hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8]}.pdf"
            
            resume_path = resume_folder / secure_name
            
            # Ensure path is within resume folder (prevent path traversal)
            if not str(resume_path.resolve()).startswith(str(resume_folder.resolve())):
                st.error(f"❌ Invalid file path: {uploaded_file.name}")
                continue
            
            try:
                with open(resume_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                logger.info(f"Saved file: {secure_name}")
            except Exception as e:
                logger.error(f"Failed to save file {secure_name}: {e}")
                st.error(f"❌ Failed to save: {uploaded_file.name}")
                continue
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Files uploaded successfully!")
        st.success(f"Uploaded {len(uploaded_files)} files to resume folder")
        
        # Auto-trigger processing
        if st.button("Extract Data and Upload to Database", width='stretch'):
            trigger_resume_processing()
            
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        st.info("Try using smaller files or check file permissions")

def process_zip_file(zip_file):
    """Process ZIP file containing resumes"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Secure ZIP extraction
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Validate ZIP contents before extraction
                for member in zip_ref.namelist():
                    if not is_safe_path(member):
                        st.error(f"❌ Unsafe path in ZIP: {member}")
                        return
                
                # Safe extraction
                for member in zip_ref.namelist():
                    if member.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
                        zip_ref.extract(member, temp_dir)
            
            # Find resume files
            resume_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
                        resume_files.append(os.path.join(root, file))
            
            if resume_files:
                st.success(f"Found {len(resume_files)} resume files in ZIP")
                
                # Ensure resume folder exists
                resume_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resume")
                resume_folder = Path(resume_dir)
                resume_folder.mkdir(parents=True, exist_ok=True)
                
                # Copy to resume folder
                for file_path in resume_files:
                    filename = os.path.basename(file_path)
                    dest_path = resume_folder / filename
                    
                    with open(file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                        dst.write(src.read())
                
                st.success(f"Extracted {len(resume_files)} files to resume folder")
                
                if st.button("Extract Data and Upload to Database", width='stretch'):
                    trigger_resume_processing()
            else:
                st.error("No resume files found in ZIP archive")
                
    except Exception as e:
        st.error(f"ZIP processing failed: {str(e)}")

def scan_resume_folder():
    """Scan resume folder for new files"""
    resume_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resume")
    resume_folder = Path(resume_dir)
    
    try:
        resume_folder.mkdir(parents=True, exist_ok=True)
        resume_files = list(resume_folder.glob("*.pdf")) + list(resume_folder.glob("*.docx")) + list(resume_folder.glob("*.txt"))
        
        st.info(f"Found {len(resume_files)} resume files in folder")
        
        for file in resume_files[:10]:  # Show first 10
            st.write(f"📄 {file.name}")
        
        if len(resume_files) > 10:
            st.write(f"... and {len(resume_files) - 10} more files")
        
        if st.button("Extract Data and Upload All Files", width='stretch'):
            trigger_resume_processing()
            
    except Exception as e:
        st.error(f"Folder scan failed: {str(e)}")

def trigger_resume_processing():
    """Trigger resume processing and upload to API"""
    import httpx
    import os
    
    API_BASE = os.getenv("GATEWAY_URL")
    if not API_BASE:
        raise ValueError("GATEWAY_URL environment variable is required")
    
    API_KEY = os.getenv("API_KEY_SECRET")
    if not API_KEY:
        raise ValueError("API_KEY_SECRET environment variable is required")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    with st.spinner("Processing resumes and uploading to database..."):
        try:
            # First run resume extraction
            import subprocess
            tools_path = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "comprehensive_resume_extractor.py")
            result = subprocess.run(
                ["python", tools_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                st.success("✅ Resume extraction completed!")
                
                # Now read the extracted data and upload via API
                import json
                from pathlib import Path
                
                # Check if extracted data file exists
                data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
                data_file = Path(data_dir) / "extracted_candidates.json"
                if data_file.exists():
                    with open(data_file, 'r') as f:
                        candidates_data = json.load(f)
                    
                    if candidates_data:
                        # Upload to API
                        response = httpx.post(
                            f"{API_BASE}/v1/candidates/bulk",
                            json={"candidates": candidates_data},
                            headers=headers,
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            result_data = response.json()
                            st.success(f"✅ Successfully uploaded {result_data.get('candidates_inserted', 0)} candidates to database!")
                            st.info("📊 Candidates are now available for AI matching and search")
                        else:
                            st.error(f"❌ API upload failed: {response.text}")
                    else:
                        st.warning("⚠️ No candidate data extracted from resumes")
                else:
                    st.warning("⚠️ No extracted data file found. Please check resume extraction process.")
            else:
                st.error("❌ Resume processing failed")
                st.code(result.stderr)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
