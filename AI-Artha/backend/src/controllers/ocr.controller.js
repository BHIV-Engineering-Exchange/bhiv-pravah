import ocrService from '../services/ocr.service.js';
import logger from '../config/logger.js';
import fs from 'fs';

// @desc    Process receipt OCR
// @route   POST /api/v1/expenses/ocr
// @access  Private
export const processReceiptOCR = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No receipt file uploaded',
      });
    }

    const allowedMimes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'application/pdf'];
    if (!allowedMimes.includes(req.file.mimetype)) {
      fs.unlinkSync(req.file.path);
      return res.status(400).json({
        success: false,
        message: 'Only image files (JPEG, PNG, WebP) and PDFs are supported',
      });
    }

    const result = await ocrService.processReceiptFile(req.file.path);

    if (!result.success) {
      fs.unlinkSync(req.file.path);
      return res.status(400).json({
        success: false,
        message: 'Failed to process receipt',
        error: result.error,
      });
    }

    if (result.data.confidence < 50) {
      logger.warn('Low confidence OCR result, deleting file', {
        file: req.file.filename,
        confidence: result.data.confidence,
      });
      fs.unlinkSync(req.file.path);
    }

    res.json({
      success: true,
      message: 'Receipt processed successfully',
      data: {
        ...result.data,
        gstAmount: result.data.taxAmount,
        fileName: req.file.filename,
        filePath: req.file.path,
      },
    });
  } catch (error) {
    logger.error('Process receipt OCR error:', error);

    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get OCR status/health
// @route   GET /api/v1/expenses/ocr/status
// @access  Private
export const getOCRStatus = async (req, res) => {
  try {
    res.json({
      success: true,
      data: {
        ocrEnabled: true,
        status: 'ready',
        message: 'OCR service active — PDF text extraction via pdf-parse, image OCR via Tesseract.js',
      },
    });
  } catch (error) {
    logger.error('Get OCR status error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
