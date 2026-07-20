import ocrService from './ocr.service.js';
import bankStatementService from './bankStatement.service.js';
import expenseService from './expense.service.js';
import logger from '../config/logger.js';
import path from 'path';

class SmartUploadService {
  detectDocumentType(file) {
    const ext = path.extname(file.originalname).toLowerCase();
    const name = file.originalname.toLowerCase();
    const mime = file.mimetype;

    if (['.csv', '.xls', '.xlsx'].includes(ext)) return 'bank_statement';
    if (name.includes('statement') || name.includes('passbook') || name.includes('txn')) return 'bank_statement';
    if (name.includes('invoice') || name.includes('inv-') || name.includes('inv_')) return 'bill';
    if (name.includes('bill') || name.includes('receipt') || name.includes('expense')) return 'receipt';
    if (mime.startsWith('image/')) return 'receipt';
    if (mime === 'application/pdf') return 'auto_detect_pdf';
    return 'receipt';
  }

  async refinePdfType(filePath, password) {
    try {
      const extraction = await ocrService.extractText(filePath, { password });
      const text = (extraction.text || '').toLowerCase();

      if (text.length < 10) return 'bill';

      const keywords = [
        'account statement', 'bank statement', 'transaction history',
        'opening balance', 'closing balance', 'passbook',
        'account number', 'account no', 'statement of account',
        'debit', 'credit', 'running balance',
      ];
      const score = keywords.reduce((s, kw) => s + (text.includes(kw) ? 1 : 0), 0);
      return score >= 3 ? 'bank_statement' : 'bill';
    } catch (err) {
      logger.warn(`PDF type detection failed: ${err.message}`);
      return 'bill';
    }
  }

  async processUpload(file, userId, metadata = {}) {
    let docType = metadata.documentType || this.detectDocumentType(file);
    if (docType === 'auto_detect_pdf') docType = await this.refinePdfType(file.path, metadata.password);

    logger.info(`Smart upload: type=${docType}, file=${file.originalname}`);

    const result = {
      documentType: docType,
      fileName: file.originalname,
      fileSize: file.size,
      actions: [],
      summary: {},
    };

    switch (docType) {
      case 'bank_statement':
        return await this._processBankStatement(file, userId, metadata, result);
      default:
        return await this._processReceipt(file, userId, metadata, result);
    }
  }

  async _processBankStatement(file, userId, metadata, result) {
    try {
      const statementData = {
        accountNumber: metadata.accountNumber || 'Auto-detected',
        bankName: metadata.bankName || 'Auto-detected',
        accountHolderName: metadata.accountHolderName || 'Auto-detected',
        startDate: metadata.startDate ? new Date(metadata.startDate) : new Date(),
        endDate: metadata.endDate ? new Date(metadata.endDate) : new Date(),
        openingBalance: metadata.openingBalance || '0',
        closingBalance: metadata.closingBalance || '0',
      };

      const statement = await bankStatementService.uploadBankStatement(statementData, userId, file);

      result.actions.push({
        type: 'bank_statement_created',
        message: `Bank statement ${statement.statementNumber} created & processing started`,
        id: statement._id,
        statementNumber: statement.statementNumber,
      });
      result.summary = {
        statementId: statement._id,
        statementNumber: statement.statementNumber,
        status: 'processing',
        message: 'Statement uploaded. Auto-reconciliation running in background.',
      };
      return result;
    } catch (err) {
      logger.error('Smart upload bank statement error:', err);
      result.actions.push({ type: 'error', message: `Bank statement failed: ${err.message}` });
      result.summary = { status: 'failed', message: err.message };
      return result;
    }
  }

  /**
   * Single extraction call that reads the REAL file content,
   * then parses structured fields from it.
   */
  async _processReceipt(file, userId, metadata, result) {
    try {
      const ocrOpts = {};
      if (metadata.password) ocrOpts.password = metadata.password;

      const ocrResult = await ocrService.processReceiptFile(file.path, ocrOpts);
      const ocrData = ocrResult.success ? ocrResult.data : null;
      const rawText = ocrData?.rawText || '';

      if (ocrData?.pdfError === 'password_required') {
        result.actions.push({
          type: 'password_required',
          message: 'PDF is password-protected. Re-upload with the PDF password to extract data.',
        });
        result.pdfError = 'password_required';
      } else if (ocrData?.pdfError) {
        result.actions.push({
          type: 'extraction_error',
          message: ocrData.pdfErrorMessage || 'Failed to read PDF',
        });
      } else if (ocrResult.success && rawText.length > 0) {
        result.actions.push({
          type: 'extraction_completed',
          message: `Extracted ${rawText.length} chars — vendor: ${ocrData.vendor}, amount: ₹${ocrData.amount}, date: ${ocrData.date}`,
          confidence: ocrData.confidence,
        });
      } else if (ocrResult.success && rawText.length === 0) {
        result.actions.push({
          type: 'no_text_found',
          message: 'No readable text found — PDF may be a scanned image or password-protected',
        });
      } else {
        result.actions.push({
          type: 'extraction_failed',
          message: ocrResult.error
            ? `Extraction error: ${ocrResult.error}`
            : 'Could not extract text from file',
        });
      }

      if (ocrData?.pages > 0) {
        result.pdfInfo = {
          pages: ocrData.pages,
          title: ocrData.pdfInfo?.title || null,
          author: ocrData.pdfInfo?.author || null,
          creator: ocrData.pdfInfo?.creator || null,
        };
      }

      if (ocrData?.items?.length) {
        result.actions.push({
          type: 'line_items_found',
          message: `Found ${ocrData.items.length} line item(s) in document`,
        });
      }

      const expenseData = {
        vendor: ocrData?.vendor || metadata.vendor || 'Unknown Vendor',
        description: ocrData?.description?.substring(0, 200) || metadata.description || `Auto-uploaded: ${file.originalname}`,
        category: metadata.category || 'other',
        date: ocrData?.date || metadata.date || new Date().toISOString().split('T')[0],
        amount: ocrData?.amount || metadata.amount || '0',
        taxAmount: ocrData?.taxAmount || metadata.taxAmount || '0',
        totalAmount: ocrData?.amount || metadata.amount || '0',
        paymentMethod: metadata.paymentMethod || 'other',
        notes: `Auto-created via Smart Upload from: ${file.originalname}`,
      };

      const expense = await expenseService.createExpense(expenseData, userId, [file]);

      result.actions.push({
        type: 'expense_created',
        message: `Expense ${expense.expenseNumber} created: ₹${expenseData.totalAmount} — ${expenseData.vendor}`,
        id: expense._id,
        expenseNumber: expense.expenseNumber,
      });

      result.extractedContent = rawText || null;

      result.summary = {
        expenseId: expense._id,
        expenseNumber: expense.expenseNumber,
        vendor: expenseData.vendor,
        description: expenseData.description,
        category: expenseData.category,
        amount: expenseData.totalAmount,
        date: expenseData.date,
        taxAmount: expenseData.taxAmount,
        paymentMethod: expenseData.paymentMethod,
        invoiceNumber: ocrData?.invoiceNumber || null,
        lineItems: ocrData?.items || [],
        status: 'created',
        ocrConfidence: ocrData?.confidence ?? null,
        message: 'Expense auto-created. Review data below and approve.',
      };

      return result;
    } catch (err) {
      logger.error('Smart upload receipt error:', err);
      result.actions.push({ type: 'error', message: `Processing failed: ${err.message}` });
      result.summary = { status: 'failed', message: err.message };
      return result;
    }
  }

  async processBatchUpload(files, userId, metadata = {}) {
    const results = [];
    for (const file of files) {
      try {
        results.push(await this.processUpload(file, userId, metadata));
      } catch (err) {
        results.push({
          documentType: 'unknown',
          fileName: file.originalname,
          fileSize: file.size,
          actions: [{ type: 'error', message: err.message }],
          summary: { status: 'failed', message: err.message },
        });
      }
    }
    return {
      totalFiles: files.length,
      processed: results.filter(r => r.summary?.status !== 'failed').length,
      failed: results.filter(r => r.summary?.status === 'failed').length,
      results,
    };
  }
}

export default new SmartUploadService();
