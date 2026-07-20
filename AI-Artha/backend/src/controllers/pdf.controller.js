import pdfService from '../services/pdf.service.js';
import logger from '../config/logger.js';

// @desc    Export General Ledger as PDF
// @route   GET /api/v1/reports/general-ledger
// @access  Private
export const exportGeneralLedger = async (req, res) => {
  try {
    const filters = {
      status: 'POSTED', // Only posted entries
      dateFrom: req.query.dateFrom,
      dateTo: req.query.dateTo,
      account: req.query.account,
    };

    const pdfDoc = await pdfService.generateGeneralLedger(filters);

    // Set response headers
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename=general-ledger-${Date.now()}.pdf`
    );

    // Pipe PDF to response
    pdfDoc.pipe(res);
  } catch (error) {
    logger.error('Export general ledger error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};