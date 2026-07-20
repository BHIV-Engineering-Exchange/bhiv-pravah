import gstFilingService from '../services/gstFiling.service.js';
import logger from '../config/logger.js';
import fs from 'fs';
import path from 'path';

// @desc    Get GST summary for period
// @route   GET /api/v1/gst/summary?period=YYYY-MM
// @access  Private
export const getGSTSummary = async (req, res) => {
  try {
    const { period } = req.query;

    if (!period || !/^\d{4}-\d{2}$/.test(period)) {
      return res.status(400).json({
        success: false,
        message: 'Period must be in YYYY-MM format',
      });
    }

    const summary = await gstFilingService.getGSTSummary(period);

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    logger.error('Get GST summary error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get GSTR-1 filing packet
// @route   GET /api/v1/gst/filing-packet/gstr-1?period=YYYY-MM
// @access  Private
export const getGSTR1FilingPacket = async (req, res) => {
  try {
    const { period } = req.query;

    if (!period || !/^\d{4}-\d{2}$/.test(period)) {
      return res.status(400).json({
        success: false,
        message: 'Period must be in YYYY-MM format',
      });
    }

    const packet = await gstFilingService.generateGSTR1FilingPacket(period);

    res.json({
      success: true,
      data: packet,
    });
  } catch (error) {
    logger.error('Get GSTR-1 packet error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get GSTR-3B filing packet
// @route   GET /api/v1/gst/filing-packet/gstr-3b?period=YYYY-MM
// @access  Private
export const getGSTR3BFilingPacket = async (req, res) => {
  try {
    const { period } = req.query;

    if (!period || !/^\d{4}-\d{2}$/.test(period)) {
      return res.status(400).json({
        success: false,
        message: 'Period must be in YYYY-MM format',
      });
    }

    const packet = await gstFilingService.generateGSTR3BFilingPacket(period);

    res.json({
      success: true,
      data: packet,
    });
  } catch (error) {
    logger.error('Get GSTR-3B packet error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Export filing packet as CSV
// @route   GET /api/v1/gst/filing-packet/export?type=gstr-1&period=YYYY-MM
// @access  Private
export const exportFilingPacket = async (req, res) => {
  try {
    const { type, period } = req.query;

    if (!period || !/^\d{4}-\d{2}$/.test(period)) {
      return res.status(400).json({
        success: false,
        message: 'Period must be in YYYY-MM format',
      });
    }

    if (!['gstr-1', 'gstr-3b'].includes(type)) {
      return res.status(400).json({
        success: false,
        message: 'Type must be gstr-1 or gstr-3b',
      });
    }

    let packet;
    if (type === 'gstr-1') {
      packet = await gstFilingService.generateGSTR1FilingPacket(period);
    } else {
      packet = await gstFilingService.generateGSTR3BFilingPacket(period);
    }

    const fileName = `${type}-${period}.csv`;
    const filePath = path.join(process.cwd(), 'uploads', fileName);

    await gstFilingService.exportFilingPacketAsCSV(packet, filePath);

    res.download(filePath, fileName, (err) => {
      if (err) {
        logger.error('Download error:', err);
      }
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    });
  } catch (error) {
    logger.error('Export filing packet error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
