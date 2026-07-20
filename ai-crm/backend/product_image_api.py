#!/usr/bin/env python3
"""
Product Image Management API
Handles image upload, processing, and management for products
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from PIL import Image
import os
import uuid
import json
from typing import List, Optional
from datetime import datetime
import shutil
from pathlib import Path
from database.service import DatabaseService
from database.models import Product, SessionLocal
from auth_system import get_current_user, User

# Image configuration
UPLOAD_DIR = "static/images"
PRODUCTS_DIR = f"{UPLOAD_DIR}/products"
THUMBNAILS_DIR = f"{UPLOAD_DIR}/thumbnails"
GALLERY_DIR = f"{UPLOAD_DIR}/gallery"
TEMP_DIR = f"{UPLOAD_DIR}/temp"

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
THUMBNAIL_SIZE = (150, 150)
MAX_IMAGE_SIZE = (1200, 1200)

def ensure_directories():
    """Ensure all required directories exist"""
    for directory in [PRODUCTS_DIR, THUMBNAILS_DIR, GALLERY_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)

def validate_image(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    if not file.filename:
        return False
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size (this is approximate, actual check happens during processing)
    return True

def generate_filename(product_id: str, image_type: str, original_filename: str) -> str:
    """Generate standardized filename for product images"""
    file_ext = Path(original_filename).suffix.lower()
    
    if image_type == "primary":
        return f"{product_id}_primary{file_ext}"
    elif image_type == "thumbnail":
        return f"{product_id}_thumb{file_ext}"
    elif image_type == "gallery":
        timestamp = int(datetime.now().timestamp())
        return f"{product_id}_gallery_{timestamp}{file_ext}"
    else:
        return f"{product_id}_{uuid.uuid4().hex[:8]}{file_ext}"

def process_image(image_path: str, output_path: str, size: Optional[tuple] = None) -> bool:
    """Process and resize image"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            if size:
                # Resize maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create square image with white background if needed
                if size[0] == size[1]:  # Square thumbnail
                    square_img = Image.new('RGB', size, (255, 255, 255))
                    paste_x = (size[0] - img.width) // 2
                    paste_y = (size[1] - img.height) // 2
                    square_img.paste(img, (paste_x, paste_y))
                    img = square_img
            else:
                # Resize to max dimensions while maintaining aspect ratio
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save processed image
            img.save(output_path, optimize=True, quality=85)
            return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def save_uploaded_file(upload_file: UploadFile, filepath: str) -> bool:
    """Save uploaded file to disk"""
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

def update_product_image_urls(product_id: str, image_type: str, filename: str):
    """Update product image URLs in database"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        
        if not product:
            # Create new product record if it doesn't exist
            from user_product_models import get_user_product_by_id
            user_product = get_user_product_by_id(product_id)
            if user_product:
                product = Product(
                    product_id=product_id,
                    name=user_product.name,
                    category=user_product.category.value,
                    description=user_product.description,
                    unit_price=user_product.unit_price,
                    weight_kg=user_product.weight_kg,
                    dimensions=user_product.dimensions,
                    supplier_id=user_product.supplier_id,
                    reorder_point=user_product.reorder_point,
                    max_stock=user_product.max_stock
                )
                db.add(product)
        
        if product:
            base_url = "/static/images"
            if image_type == "primary":
                product.primary_image_url = f"{base_url}/products/{filename}"
                product.thumbnail_url = f"{base_url}/thumbnails/{filename.replace('_primary', '_thumb')}"
            elif image_type == "gallery":
                if product.gallery_images:
                    gallery_list = json.loads(product.gallery_images)
                else:
                    gallery_list = []
                gallery_list.append(f"{base_url}/gallery/{filename}")
                product.gallery_images = json.dumps(gallery_list)
        
        db.commit()
        db.close()
        return True
    except Exception as e:
        print(f"Error updating product image URLs: {e}")
        return False

# FastAPI app for image management
image_app = FastAPI(title="Product Image Management API", version="1.0.0")

# Mount static files
image_app.mount("/static", StaticFiles(directory="static"), name="static")

@image_app.on_event("startup")
async def startup_event():
    """Initialize directories on startup"""
    ensure_directories()

@image_app.post("/upload/primary/{product_id}")
async def upload_primary_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload primary product image"""
    
    # Validate file
    if not validate_image(file):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    try:
        # Generate filenames
        primary_filename = generate_filename(product_id, "primary", file.filename)
        thumbnail_filename = generate_filename(product_id, "thumbnail", file.filename)
        
        # Save to temp first
        temp_filepath = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}.tmp")
        if not save_uploaded_file(file, temp_filepath):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # Process and save primary image
        primary_filepath = os.path.join(PRODUCTS_DIR, primary_filename)
        if not process_image(temp_filepath, primary_filepath):
            os.remove(temp_filepath)
            raise HTTPException(status_code=500, detail="Failed to process primary image")
        
        # Create thumbnail
        thumbnail_filepath = os.path.join(THUMBNAILS_DIR, thumbnail_filename)
        if not process_image(temp_filepath, thumbnail_filepath, THUMBNAIL_SIZE):
            os.remove(temp_filepath)
            raise HTTPException(status_code=500, detail="Failed to create thumbnail")
        
        # Clean up temp file
        os.remove(temp_filepath)
        
        # Update database
        update_product_image_urls(product_id, "primary", primary_filename)
        
        return {
            "success": True,
            "message": "Primary image uploaded successfully",
            "product_id": product_id,
            "primary_image_url": f"/static/images/products/{primary_filename}",
            "thumbnail_url": f"/static/images/thumbnails/{thumbnail_filename}"
        }
        
    except Exception as e:
        # Clean up on error
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@image_app.post("/upload/gallery/{product_id}")
async def upload_gallery_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload gallery image for product"""
    
    # Validate file
    if not validate_image(file):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    try:
        # Generate filename
        gallery_filename = generate_filename(product_id, "gallery", file.filename)
        
        # Save to temp first
        temp_filepath = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}.tmp")
        if not save_uploaded_file(file, temp_filepath):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        # Process and save gallery image
        gallery_filepath = os.path.join(GALLERY_DIR, gallery_filename)
        if not process_image(temp_filepath, gallery_filepath):
            os.remove(temp_filepath)
            raise HTTPException(status_code=500, detail="Failed to process gallery image")
        
        # Clean up temp file
        os.remove(temp_filepath)
        
        # Update database
        update_product_image_urls(product_id, "gallery", gallery_filename)
        
        return {
            "success": True,
            "message": "Gallery image uploaded successfully",
            "product_id": product_id,
            "gallery_image_url": f"/static/images/gallery/{gallery_filename}"
        }
        
    except Exception as e:
        # Clean up on error
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@image_app.post("/upload/bulk/{product_id}")
async def upload_bulk_images(
    product_id: str,
    primary_image: Optional[UploadFile] = File(None),
    gallery_images: List[UploadFile] = File([]),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple images for a product"""
    
    results = {"success": True, "uploads": [], "errors": []}
    
    # Upload primary image if provided
    if primary_image:
        try:
            primary_result = await upload_primary_image(product_id, primary_image, current_user)
            results["uploads"].append({"type": "primary", "result": primary_result})
        except Exception as e:
            results["errors"].append({"type": "primary", "error": str(e)})
    
    # Upload gallery images
    for i, gallery_image in enumerate(gallery_images):
        try:
            gallery_result = await upload_gallery_image(product_id, gallery_image, current_user)
            results["uploads"].append({"type": f"gallery_{i+1}", "result": gallery_result})
        except Exception as e:
            results["errors"].append({"type": f"gallery_{i+1}", "error": str(e)})
    
    if results["errors"]:
        results["success"] = False
    
    return results

@image_app.get("/product/{product_id}/images")
async def get_product_images(product_id: str):
    """Get all images for a product"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        db.close()
        
        if not product:
            return {"product_id": product_id, "images": {}}
        
        gallery_images = []
        if product.gallery_images:
            try:
                gallery_images = json.loads(product.gallery_images)
            except:
                gallery_images = []
        
        return {
            "product_id": product_id,
            "images": {
                "primary_image_url": product.primary_image_url,
                "thumbnail_url": product.thumbnail_url,
                "gallery_images": gallery_images
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product images: {str(e)}")

@image_app.delete("/product/{product_id}/image/{image_type}")
async def delete_product_image(
    product_id: str,
    image_type: str,  # primary, thumbnail, gallery
    image_url: Optional[str] = None,  # For gallery images
    current_user: User = Depends(get_current_user)
):
    """Delete product image"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if image_type == "primary":
            if product.primary_image_url:
                # Delete files
                primary_file = product.primary_image_url.replace("/static/images/", "static/images/")
                if os.path.exists(primary_file):
                    os.remove(primary_file)
                
                # Delete thumbnail
                if product.thumbnail_url:
                    thumb_file = product.thumbnail_url.replace("/static/images/", "static/images/")
                    if os.path.exists(thumb_file):
                        os.remove(thumb_file)
                
                # Update database
                product.primary_image_url = None
                product.thumbnail_url = None
        
        elif image_type == "gallery" and image_url:
            if product.gallery_images:
                gallery_list = json.loads(product.gallery_images)
                if image_url in gallery_list:
                    # Delete file
                    image_file = image_url.replace("/static/images/", "static/images/")
                    if os.path.exists(image_file):
                        os.remove(image_file)
                    
                    # Update database
                    gallery_list.remove(image_url)
                    product.gallery_images = json.dumps(gallery_list)
        
        db.commit()
        db.close()
        
        return {"success": True, "message": f"{image_type} image deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

@image_app.get("/")
async def image_api_info():
    """API information"""
    return {
        "service": "Product Image Management API",
        "version": "1.0.0",
        "endpoints": {
            "upload_primary": "POST /upload/primary/{product_id}",
            "upload_gallery": "POST /upload/gallery/{product_id}",
            "upload_bulk": "POST /upload/bulk/{product_id}",
            "get_images": "GET /product/{product_id}/images",
            "delete_image": "DELETE /product/{product_id}/image/{image_type}"
        },
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size": f"{MAX_FILE_SIZE / (1024*1024)}MB"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(image_app, host="0.0.0.0", port=8004)