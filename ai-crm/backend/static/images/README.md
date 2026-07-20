# Product Images Directory Structure

This directory contains product images for the AI Logistics System.

## Directory Structure:
```
static/images/
├── products/     # Main product images
├── thumbnails/   # Optimized thumbnails (150x150)
├── gallery/      # Additional product gallery images
└── temp/         # Temporary upload directory
```

## Image Naming Convention:
- **Primary Images**: `{product_id}_primary.{ext}` (e.g., `USR001_primary.jpg`)
- **Thumbnails**: `{product_id}_thumb.{ext}` (e.g., `USR001_thumb.jpg`)
- **Gallery Images**: `{product_id}_gallery_{index}.{ext}` (e.g., `USR001_gallery_1.jpg`)

## Supported Formats:
- JPG/JPEG
- PNG
- WEBP

## Image Requirements:
- **Primary Images**: Recommended 800x800px, max 2MB
- **Thumbnails**: Automatically generated 150x150px
- **Gallery Images**: Recommended 600x600px, max 1MB each

## Usage:
Images are served through the FastAPI static files endpoint:
- URL pattern: `/static/images/products/{filename}`
- Access via: `http://localhost:8002/static/images/products/USR001_primary.jpg`