import financialReportsService from '../services/financialReports.service.js';
import statutoryReportsService from '../services/statutoryReports.service.js';
import logger from '../config/logger.js';
import { randomUUID } from 'crypto';
import auditService from '../services/audit.service.js';
import evidenceAutomationService from '../services/evidenceAutomation.service.js';
import tantraService from '../services/tantra.service.js';

// @desc    Generate Profit & Loss
// @route   GET /api/v1/reports/profit-loss
// @access  Private
export const getProfitLoss = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: 'Start date and end date are required',
      });
    }

    const report = await financialReportsService.generateProfitLoss(startDate, endDate);
    
    const traceId = randomUUID();
    
    // Audit trail
    await auditService.recordEvent({
      eventType: 'PROFIT_LOSS_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      traceId,
      userId: req.user?._id,
      details: {
        reportType: 'Profit & Loss',
        startDate,
        endDate,
        netIncome: report.netIncome,
      },
    });
    
    // Capture evidence
    await evidenceAutomationService.captureAPIResponse({
      operation: 'generateProfitLoss',
      entityType: 'Report',
      entityId: randomUUID(),
      request: { startDate, endDate },
      response: { success: true, netIncome: report.netIncome },
      traceId,
    });
    
    // Emit TANTRA event
    await tantraService.emitEvent({
      event: 'PROFIT_LOSS_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      details: { startDate, endDate, netIncome: report.netIncome },
    });

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    logger.error('Get profit loss error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate Balance Sheet
// @route   GET /api/v1/reports/balance-sheet
// @access  Private
export const getBalanceSheet = async (req, res) => {
  try {
    const { asOfDate } = req.query;

    if (!asOfDate) {
      return res.status(400).json({
        success: false,
        message: 'As of date is required',
      });
    }

    const report = await financialReportsService.generateBalanceSheet(asOfDate);
    
    const traceId = randomUUID();
    
    // Audit trail
    await auditService.recordEvent({
      eventType: 'BALANCE_SHEET_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      traceId,
      userId: req.user?._id,
      details: {
        reportType: 'Balance Sheet',
        asOfDate,
        totalAssets: report.totalAssets,
        totalLiabilities: report.totalLiabilities,
        totalEquity: report.totalEquity,
      },
    });
    
    // Capture evidence
    await evidenceAutomationService.captureAPIResponse({
      operation: 'generateBalanceSheet',
      entityType: 'Report',
      entityId: randomUUID(),
      request: { asOfDate },
      response: { success: true, totalAssets: report.totalAssets },
      traceId,
    });
    
    // Emit TANTRA event
    await tantraService.emitEvent({
      event: 'BALANCE_SHEET_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      details: { asOfDate, totalAssets: report.totalAssets },
    });

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    logger.error('Get balance sheet error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate Cash Flow
// @route   GET /api/v1/reports/cash-flow
// @access  Private
export const getCashFlow = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: 'Start date and end date are required',
      });
    }

    const report = await financialReportsService.generateCashFlow(startDate, endDate);
    
    const traceId = randomUUID();
    
    // Audit trail
    await auditService.recordEvent({
      eventType: 'CASH_FLOW_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      traceId,
      userId: req.user?._id,
      details: {
        reportType: 'Cash Flow',
        startDate,
        endDate,
        netCashFlow: report.netCashFlow,
      },
    });
    
    // Capture evidence
    await evidenceAutomationService.captureAPIResponse({
      operation: 'generateCashFlow',
      entityType: 'Report',
      entityId: randomUUID(),
      request: { startDate, endDate },
      response: { success: true, netCashFlow: report.netCashFlow },
      traceId,
    });
    
    // Emit TANTRA event
    await tantraService.emitEvent({
      event: 'CASH_FLOW_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      details: { startDate, endDate, netCashFlow: report.netCashFlow },
    });

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    logger.error('Get cash flow error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate Trial Balance
// @route   GET /api/v1/reports/trial-balance
// @access  Private
export const getTrialBalance = async (req, res) => {
  try {
    const { asOfDate } = req.query;

    if (!asOfDate) {
      return res.status(400).json({
        success: false,
        message: 'As of date is required',
      });
    }

    const report = await financialReportsService.generateTrialBalance(asOfDate);
    
    const traceId = randomUUID();
    
    // Audit trail
    await auditService.recordEvent({
      eventType: 'TRIAL_BALANCE_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      traceId,
      userId: req.user?._id,
      details: {
        reportType: 'Trial Balance',
        asOfDate,
        totalDebits: report.totalDebits,
        totalCredits: report.totalCredits,
      },
    });
    
    // Capture evidence
    await evidenceAutomationService.captureAPIResponse({
      operation: 'generateTrialBalance',
      entityType: 'Report',
      entityId: randomUUID(),
      request: { asOfDate },
      response: { success: true, totalDebits: report.totalDebits, totalCredits: report.totalCredits },
      traceId,
    });
    
    // Emit TANTRA event
    await tantraService.emitEvent({
      event: 'TRIAL_BALANCE_GENERATED',
      entityType: 'Report',
      entityId: randomUUID(),
      details: { asOfDate, totalDebits: report.totalDebits },
    });

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    logger.error('Get trial balance error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate Aged Receivables
// @route   GET /api/v1/reports/aged-receivables
// @access  Private
export const getAgedReceivables = async (req, res) => {
  try {
    const { asOfDate } = req.query;

    if (!asOfDate) {
      return res.status(400).json({
        success: false,
        message: 'As of date is required',
      });
    }

    const report = await financialReportsService.generateAgedReceivables(asOfDate);

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    logger.error('Get aged receivables error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate Dashboard Summary
// @route   GET /api/v1/reports/dashboard
// @access  Private
export const getDashboardSummary = async (req, res) => {
  try {
    const summary = await financialReportsService.generateDashboardSummary();

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    logger.error('Get dashboard summary error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get statement-driven report period context
// @route   GET /api/v1/reports/period-context
// @access  Private
export const getReportPeriodContext = async (req, res) => {
  try {
    const context = await financialReportsService.getReportPeriodContext();

    res.json({
      success: true,
      data: context,
    });
  } catch (error) {
    logger.error('Get report period context error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get GST summary (ledger-only)
// @route   GET /api/v1/reports/gst-summary
// @access  Private
export const getGSTSummaryReport = async (req, res) => {
  try {
    const summary = await statutoryReportsService.getGSTSummary({
      startDate: req.query.startDate,
      endDate: req.query.endDate,
    });

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    logger.error('Get GST summary report error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get TDS summary (ledger-only)
// @route   GET /api/v1/reports/tds-summary
// @access  Private
export const getTDSSummaryReport = async (req, res) => {
  try {
    const summary = await statutoryReportsService.getTDSSummary({
      startDate: req.query.startDate,
      endDate: req.query.endDate,
    });

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    logger.error('Get TDS summary report error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get Revenue vs Expenses Chart
// @route   GET /api/v1/reports/revenue-expenses-chart
// @access  Private
export const getRevenueExpensesChart = async (req, res) => {
  try {
    const { year } = req.query;
    const chartData = await financialReportsService.generateRevenueExpensesChart(year);

    res.json({
      success: true,
      data: chartData,
    });
  } catch (error) {
    logger.error('Get revenue expenses chart error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get Expense Breakdown Chart
// @route   GET /api/v1/reports/expense-breakdown
// @access  Private
export const getExpenseBreakdown = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: 'Start date and end date are required',
      });
    }

    const breakdown = await financialReportsService.generateExpenseBreakdown(startDate, endDate);

    res.json({
      success: true,
      data: breakdown,
    });
  } catch (error) {
    logger.error('Get expense breakdown error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get Bank Transaction Timeline
// @route   GET /api/v1/reports/bank-transaction-timeline
// @access  Private
export const getBankTransactionTimeline = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    const timeline = await financialReportsService.generateBankTransactionTimeline(startDate, endDate);

    res.json({
      success: true,
      data: timeline,
    });
  } catch (error) {
    logger.error('Get bank transaction timeline error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Generate KPIs
// @route   GET /api/v1/reports/kpis
// @access  Private
export const getKPIs = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: 'Start date and end date are required',
      });
    }

    const kpis = await financialReportsService.generateKPIs(startDate, endDate);

    res.json({
      success: true,
      data: kpis,
    });
  } catch (error) {
    logger.error('Get KPIs error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Export Profit & Loss as PDF
// @route   GET /api/v1/reports/profit-loss/export
// @access  Private
export const exportProfitLossPDF = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    if (!startDate || !endDate) {
      return res.status(400).json({ success: false, message: 'Start date and end date are required' });
    }
    const exportService = (await import('../services/export.service.js')).default;
    const pdfDoc = await exportService.exportProfitLossPDF(startDate, endDate);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=profit-loss-${startDate}-to-${endDate}.pdf`);
    pdfDoc.pipe(res);
  } catch (error) {
    logger.error('Export P&L error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Export Balance Sheet as PDF
// @route   GET /api/v1/reports/balance-sheet/export
// @access  Private
export const exportBalanceSheetPDF = async (req, res) => {
  try {
    const { asOfDate } = req.query;
    if (!asOfDate) {
      return res.status(400).json({ success: false, message: 'As of date is required' });
    }
    const exportService = (await import('../services/export.service.js')).default;
    const pdfDoc = await exportService.exportBalanceSheetPDF(asOfDate);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=balance-sheet-${asOfDate}.pdf`);
    pdfDoc.pipe(res);
  } catch (error) {
    logger.error('Export balance sheet error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Export Cash Flow as PDF
// @route   GET /api/v1/reports/cash-flow/export
// @access  Private
export const exportCashFlowPDF = async (req, res) => {
  try {
    const { startDate, endDate } = req.query;
    if (!startDate || !endDate) {
      return res.status(400).json({ success: false, message: 'Start date and end date are required' });
    }
    const exportService = (await import('../services/export.service.js')).default;
    const pdfDoc = await exportService.exportCashFlowPDF(startDate, endDate);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=cash-flow-${startDate}-to-${endDate}.pdf`);
    pdfDoc.pipe(res);
  } catch (error) {
    logger.error('Export cash flow error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
};

// @desc    Export Trial Balance as PDF
// @route   GET /api/v1/reports/trial-balance/export
// @access  Private
export const exportTrialBalancePDF = async (req, res) => {
  try {
    const { asOfDate } = req.query;
    if (!asOfDate) {
      return res.status(400).json({ success: false, message: 'As of date is required' });
    }
    const exportService = (await import('../services/export.service.js')).default;
    const pdfDoc = await exportService.exportTrialBalancePDF(asOfDate);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=trial-balance-${asOfDate}.pdf`);
    pdfDoc.pipe(res);
  } catch (error) {
    logger.error('Export trial balance error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
};
