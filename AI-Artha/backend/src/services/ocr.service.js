import logger from '../config/logger.js';
import fs from 'fs';
import fsPromises from 'fs/promises';
import path from 'path';
import { pathToFileURL } from 'url';
import { createRequire } from 'module';

class OCRService {
  /**
   * @param {string} filePath
   * @param {object} opts - { password?: string }
   */
  async extractText(filePath, opts = {}) {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }
    const ext = path.extname(filePath).toLowerCase();
    logger.info(`OCR extractText: ${filePath} (ext=${ext})`);

    if (ext === '.pdf') return await this._extractFromPdf(filePath, opts.password);
    return await this._extractFromImage(filePath);
  }

  /**
   * Try pdf-parse v2 first, fall back to pdfjs-dist directly.
   */
  async _extractFromPdf(filePath, password) {
    const buffer = await fsPromises.readFile(filePath);

    // --- Attempt 1: pdf-parse v2 wrapper ---
    try {
      const { PDFParse } = await import('pdf-parse');
      const opts = { data: new Uint8Array(buffer) };
      if (password) opts.password = password;

      const parser = new PDFParse(opts);
      const textResult = await parser.getText();
      let info = {};
      try {
        const ir = await parser.getInfo();
        info = { title: ir.info?.Title, author: ir.info?.Author, creator: ir.info?.Creator };
      } catch {}
      await parser.destroy().catch(() => {});

      const text = textResult.text || '';
      logger.info(`pdf-parse v2 OK: ${textResult.total} pages, ${text.length} chars`);
      return { text, pages: textResult.total || 0, info };
    } catch (err1) {
      const pwErr = /password/i.test(err1.message) || err1.name === 'PasswordException';
      if (pwErr) {
        logger.warn('PDF password-protected');
        return { text: '', pages: 0, info: {}, error: 'password_required',
          errorMessage: 'PDF is password-protected. Provide the password to extract data.' };
      }
      logger.warn(`pdf-parse v2 failed (${err1.message}), trying pdfjs-dist directly...`);
    }

    // --- Attempt 2: pdfjs-dist directly with proper worker ---
    try {
      const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs');

      const require = createRequire(import.meta.url);
      const pkgDir = path.dirname(require.resolve('pdfjs-dist/package.json'));
      const workerPath = path.join(pkgDir, 'legacy', 'build', 'pdf.worker.mjs');
      pdfjs.GlobalWorkerOptions.workerSrc = pathToFileURL(workerPath).href;

      const loadOpts = { data: new Uint8Array(buffer) };
      if (password) loadOpts.password = password;

      const doc = await pdfjs.getDocument(loadOpts).promise;
      let allText = '';

      for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i);
        const content = await page.getTextContent();
        const pageText = content.items.map(item => item.str).join(' ');
        allText += pageText + '\n\n';
        page.cleanup();
      }

      let info = {};
      try {
        const meta = await doc.getMetadata();
        info = { title: meta.info?.Title, author: meta.info?.Author, creator: meta.info?.Creator };
      } catch {}

      const pages = doc.numPages;
      await doc.destroy();

      logger.info(`pdfjs-dist direct OK: ${pages} pages, ${allText.length} chars`);
      return { text: allText, pages, info };
    } catch (err2) {
      const pwErr2 = /password/i.test(err2.message) || err2.name === 'PasswordException';
      if (pwErr2) {
        return { text: '', pages: 0, info: {}, error: 'password_required',
          errorMessage: 'PDF is password-protected. Provide the password to extract data.' };
      }
      logger.error(`pdfjs-dist direct also failed: ${err2.message}`);
      return { text: '', pages: 0, info: {}, error: 'extraction_failed',
        errorMessage: `PDF read failed: ${err2.message}` };
    }
  }

  async _extractFromImage(filePath) {
    try {
      const Tesseract = await import('tesseract.js');
      const { data: { text, confidence } } = await Tesseract.recognize(filePath, 'eng');
      logger.info(`Tesseract OCR: ${text.length} chars, confidence=${confidence}`);
      return { text, pages: 1, info: {}, ocrConfidence: confidence };
    } catch (err) {
      logger.warn(`Tesseract unavailable (${err.message})`);
      return { text: '', pages: 1, info: {}, ocrConfidence: 0 };
    }
  }

  parseText(rawText) {
    return {
      vendor: this._extractVendor(rawText),
      date: this._extractDate(rawText),
      amount: this._extractAmount(rawText),
      taxAmount: this._extractTax(rawText),
      invoiceNumber: this._extractInvoiceNumber(rawText),
      items: this._extractLineItems(rawText),
      description: rawText.trim().substring(0, 300),
      confidence: this._calcConfidence(rawText, {
        vendor: this._extractVendor(rawText),
        amount: this._extractAmount(rawText),
        date: this._extractDate(rawText),
        invoiceNumber: this._extractInvoiceNumber(rawText),
        taxAmount: this._extractTax(rawText),
      }),
    };
  }

  async processReceiptFile(filePath, opts = {}) {
    try {
      logger.info(`Processing receipt: ${filePath}`);
      const extraction = await this.extractText(filePath, opts);

      if (extraction.error === 'password_required') {
        return {
          success: true,
          data: {
            vendor: 'Unknown', date: new Date().toISOString().split('T')[0],
            amount: '0.00', taxAmount: '0.00', invoiceNumber: '', items: [],
            description: extraction.errorMessage, rawText: '', confidence: 0,
            pages: 0, pdfInfo: {}, pdfError: 'password_required',
            pdfErrorMessage: extraction.errorMessage,
            processedAt: new Date().toISOString(),
          },
        };
      }

      if (extraction.error) {
        return {
          success: true,
          data: {
            vendor: 'Unknown', date: new Date().toISOString().split('T')[0],
            amount: '0.00', taxAmount: '0.00', invoiceNumber: '', items: [],
            description: extraction.errorMessage || 'Failed to read document',
            rawText: '', confidence: 0, pages: 0, pdfInfo: {},
            pdfError: extraction.error, pdfErrorMessage: extraction.errorMessage,
            processedAt: new Date().toISOString(),
          },
        };
      }

      const rawText = extraction.text;
      if (!rawText || rawText.trim().length < 5) {
        return {
          success: true,
          data: {
            vendor: 'Unknown', date: new Date().toISOString().split('T')[0],
            amount: '0.00', taxAmount: '0.00', invoiceNumber: '', items: [],
            description: '(No readable text — may be a scanned image PDF)',
            rawText: '', confidence: 0, pages: extraction.pages,
            pdfInfo: extraction.info, processedAt: new Date().toISOString(),
          },
        };
      }

      const parsed = this.parseText(rawText);
      return {
        success: true,
        data: {
          ...parsed, rawText, pages: extraction.pages, pdfInfo: extraction.info,
          ocrConfidence: extraction.ocrConfidence || null,
          processedAt: new Date().toISOString(),
        },
      };
    } catch (error) {
      logger.error('processReceiptFile error:', error);
      return { success: false, error: error.message, data: null };
    }
  }

  /* ── Extraction helpers ────────────────────────────── */

  _extractVendor(text) {
    const patterns = [
      /(?:from|vendor|merchant|seller|billed by|company|issued by|shop|store)[\s:]+([^\n,;]+)/i,
      /(?:M\/s\.?|Messrs\.?)[\s:]+([^\n,;]+)/i,
    ];
    for (const p of patterns) {
      const m = text.match(p);
      if (m?.[1]) {
        const v = m[1].trim();
        if (v.length >= 2 && v.length <= 100 && !/^\d+$/.test(v)) return v;
      }
    }
    const lines = text.trim().split('\n').map(l => l.trim()).filter(l => l.length >= 3);
    for (const line of lines.slice(0, 5)) {
      if (line.length >= 3 && line.length <= 80 && /[A-Za-z]/.test(line) && !/^\d/.test(line)) return line;
    }
    return 'Unknown Vendor';
  }

  _extractDate(text) {
    const patterns = [
      /(?:date|invoice date|bill date|dated|dt)[\s.:]*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})/i,
      /(?:date|invoice date|bill date|dated|dt)[\s.:]*(\d{4}[\/-]\d{1,2}[\/-]\d{1,2})/i,
      /(?:date|invoice date|bill date|dated|dt)[\s.:]*(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{2,4})/i,
      /(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})/,
      /(\d{4}[\/-]\d{1,2}[\/-]\d{1,2})/,
      /(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{2,4})/i,
    ];
    for (const p of patterns) {
      const m = text.match(p);
      if (m?.[1]) {
        try {
          const d = new Date(m[1]);
          if (!isNaN(d) && d.getFullYear() > 2000 && d.getFullYear() < 2100) return d.toISOString().split('T')[0];
        } catch {}
      }
    }
    return new Date().toISOString().split('T')[0];
  }

  _extractAmount(text) {
    const totalPatterns = [
      /(?:grand\s*total|net\s*total|total\s*amount|total\s*due|total\s*payable|amount\s*due|balance\s*due)[\s:]*(?:rs\.?|₹|inr)?\s*([0-9,]+\.?\d{0,2})/i,
      /(?:total)[\s:]*(?:rs\.?|₹|inr)?\s*([0-9,]+\.?\d{0,2})/i,
      /(?:amount|bill\s*amount|invoice\s*amount)[\s:]*(?:rs\.?|₹|inr)?\s*([0-9,]+\.?\d{0,2})/i,
    ];
    for (const p of totalPatterns) {
      const m = text.match(p);
      if (m?.[1]) {
        const val = parseFloat(m[1].replace(/,/g, ''));
        if (!isNaN(val) && val > 0) return val.toFixed(2);
      }
    }
    const amounts = [];
    for (const m of text.matchAll(/(?:rs\.?|₹|inr)\s*([0-9,]+\.?\d{0,2})/gi)) {
      const val = parseFloat(m[1].replace(/,/g, ''));
      if (!isNaN(val) && val > 0) amounts.push(val);
    }
    if (amounts.length) return Math.max(...amounts).toFixed(2);
    return '0.00';
  }

  _extractTax(text) {
    let total = 0;
    for (const line of text.split('\n')) {
      if (/cgst|sgst|igst|gst|tax|vat/i.test(line)) {
        const m = line.match(/(?:rs\.?|₹|inr)\s*([0-9,]+\.\d{2})/i) || line.match(/([0-9,]+\.\d{2})\s*$/);
        if (m?.[1]) {
          const val = parseFloat(m[1].replace(/,/g, ''));
          if (!isNaN(val) && val > 0) total += val;
        }
      }
    }
    if (total === 0) {
      const m = text.match(/(?:tax\s*amount|gst\s*amount|total\s*tax)[\s:]*(?:rs\.?|₹|inr)?\s*([0-9,]+\.?\d{0,2})/i);
      if (m?.[1]) { const v = parseFloat(m[1].replace(/,/g, '')); if (!isNaN(v) && v > 0) total = v; }
    }
    return total.toFixed(2);
  }

  _extractInvoiceNumber(text) {
    const patterns = [
      /(?:invoice\s*(?:no|number|#|num)\.?)[\s:]*([A-Z0-9][\w\-\/]{2,30})/i,
      /(?:bill\s*(?:no|number|#)\.?)[\s:]*([A-Z0-9][\w\-\/]{2,30})/i,
      /(?:receipt\s*(?:no|number|#)\.?)[\s:]*([A-Z0-9][\w\-\/]{2,30})/i,
      /(?:reference\s*(?:no|number|#)\.?)[\s:]*([A-Z0-9][\w\-\/]{2,30})/i,
      /(?:inv|INV)[\s\-:#]*([A-Z0-9][\w\-\/]{2,30})/i,
    ];
    for (const p of patterns) {
      const m = text.match(p);
      if (m?.[1]) return m[1].trim();
    }
    return '';
  }

  _extractLineItems(text) {
    const items = [];
    for (const line of text.split('\n')) {
      const t = line.trim();
      if (t.length < 5) continue;
      const m = t.match(/^(.+?)\s+[₹$]?\s?([0-9,]+\.?\d{0,2})\s*$/);
      if (m) {
        const desc = m[1].trim();
        const amt = parseFloat(m[2].replace(/,/g, ''));
        if (desc.length >= 2 && !isNaN(amt) && amt > 0) {
          const l = desc.toLowerCase();
          if (!l.includes('total') && !l.includes('balance') && !l.includes('subtotal'))
            items.push({ description: desc, amount: amt.toFixed(2) });
        }
      }
    }
    return items.slice(0, 50);
  }

  _calcConfidence(rawText, f) {
    let s = 30;
    if (rawText.length > 50) s += 10;
    if (rawText.length > 200) s += 10;
    if (f.vendor !== 'Unknown Vendor') s += 15;
    if (f.amount !== '0.00') s += 15;
    if (f.date !== new Date().toISOString().split('T')[0]) s += 10;
    if (f.invoiceNumber) s += 10;
    if (f.taxAmount !== '0.00') s += 5;
    return Math.min(Math.max(s, 0), 100);
  }
}

export default new OCRService();
