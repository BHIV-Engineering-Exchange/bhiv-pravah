import PDFDocument from 'pdfkit';
import ledgerService from './ledger.service.js';
import Decimal from 'decimal.js';

class PDFService {
  /**
   * Generate Invoice PDF
   */
  async generateInvoicePDF(invoice, companyInfo = {}) {
    const doc = new PDFDocument({ margin: 50, size: 'A4' });

    // Company Header
    doc.fontSize(20).font('Helvetica-Bold').text(companyInfo.name || 'ARTHA Finance', 50, 50);
    doc.fontSize(10).font('Helvetica');
    if (companyInfo.address) doc.text(companyInfo.address, 50, 75);
    if (companyInfo.gstin) doc.text(`GSTIN: ${companyInfo.gstin}`, 50, 90);
    if (companyInfo.phone) doc.text(`Phone: ${companyInfo.phone}`, 50, 105);

    // Invoice Title
    doc.fontSize(24).font('Helvetica-Bold').text('INVOICE', 400, 50, { align: 'right' });
    doc.fontSize(12).font('Helvetica');
    doc.text(`Invoice #: ${invoice.invoiceNumber}`, 400, 80, { align: 'right' });
    doc.text(`Date: ${new Date(invoice.invoiceDate).toLocaleDateString()}`, 400, 95, { align: 'right' });
    doc.text(`Due: ${new Date(invoice.dueDate).toLocaleDateString()}`, 400, 110, { align: 'right' });

    // Status badge
    const statusColors = {
      draft: '#6B7280',
      sent: '#3B82F6',
      paid: '#10B981',
      partial: '#F59E0B',
      overdue: '#EF4444',
      cancelled: '#6B7280',
    };
    doc.fillColor(statusColors[invoice.status] || '#6B7280')
      .text(`Status: ${(invoice.status || 'draft').toUpperCase()}`, 400, 125, { align: 'right' });
    doc.fillColor('black');

    // Divider
    doc.moveTo(50, 150).lineTo(550, 150).stroke();

    // Bill To section
    doc.fontSize(12).font('Helvetica-Bold').text('Bill To:', 50, 170);
    doc.fontSize(10).font('Helvetica');
    doc.text(invoice.customerName || 'N/A', 50, 190);
    if (invoice.customerEmail) doc.text(invoice.customerEmail, 50, 205);
    if (invoice.customerAddress) doc.text(invoice.customerAddress, 50, 220);
    if (invoice.customerGSTIN) doc.text(`GSTIN: ${invoice.customerGSTIN}`, 50, 235);

    // Table header
    const tableTop = 280;
    const col1 = 50; // Description
    const col2 = 280; // HSN/SAC
    const col3 = 350; // Qty
    const col4 = 400; // Rate
    const col5 = 480; // Amount

    doc.fontSize(10).font('Helvetica-Bold');
    doc.text('Description', col1, tableTop);
    doc.text('HSN/SAC', col2, tableTop);
    doc.text('Qty', col3, tableTop);
    doc.text('Rate', col4, tableTop);
    doc.text('Amount', col5, tableTop);

    doc.moveTo(50, tableTop + 15).lineTo(550, tableTop + 15).stroke();

    // Line items
    let y = tableTop + 25;
    doc.font('Helvetica');
    const items = invoice.items || invoice.lines || [];
    
    items.forEach((item) => {
      const amount = new Decimal(item.quantity || 1).times(new Decimal(item.unitPrice || item.rate || 0));
      
      doc.text(item.description || item.name || 'Item', col1, y, { width: 220 });
      doc.text(item.hsnCode || item.sacCode || '-', col2, y);
      doc.text(String(item.quantity || 1), col3, y);
      doc.text(this.formatCurrency(item.unitPrice || item.rate || 0), col4, y);
      doc.text(this.formatCurrency(amount.toString()), col5, y);
      
      y += 20;
      
      // Add new page if needed
      if (y > 700) {
        doc.addPage();
        y = 50;
      }
    });

    // Totals section
    y += 20;
    doc.moveTo(350, y).lineTo(550, y).stroke();
    y += 10;

    doc.font('Helvetica');
    doc.text('Subtotal:', 350, y);
    doc.text(this.formatCurrency(invoice.subtotal || 0), col5, y);
    y += 20;

    if (invoice.cgst || invoice.cgstAmount) {
      const cgstRateLabel = invoice.cgstRate !== undefined && invoice.cgstRate !== null
        ? ` (${invoice.cgstRate}%)`
        : '';
      doc.text(`CGST${cgstRateLabel}:`, 350, y);
      doc.text(this.formatCurrency(invoice.cgst || invoice.cgstAmount || 0), col5, y);
      y += 15;
    }

    if (invoice.sgst || invoice.sgstAmount) {
      const sgstRateLabel = invoice.sgstRate !== undefined && invoice.sgstRate !== null
        ? ` (${invoice.sgstRate}%)`
        : '';
      doc.text(`SGST${sgstRateLabel}:`, 350, y);
      doc.text(this.formatCurrency(invoice.sgst || invoice.sgstAmount || 0), col5, y);
      y += 15;
    }

    if (invoice.igst || invoice.igstAmount) {
      const igstRateLabel = invoice.igstRate !== undefined && invoice.igstRate !== null
        ? ` (${invoice.igstRate}%)`
        : '';
      doc.text(`IGST${igstRateLabel}:`, 350, y);
      doc.text(this.formatCurrency(invoice.igst || invoice.igstAmount || 0), col5, y);
      y += 15;
    }

    if (invoice.taxAmount && !invoice.cgst && !invoice.sgst && !invoice.igst) {
      doc.text('Tax:', 350, y);
      doc.text(this.formatCurrency(invoice.taxAmount), col5, y);
      y += 15;
    }

    y += 5;
    doc.moveTo(350, y).lineTo(550, y).stroke();
    y += 10;

    doc.font('Helvetica-Bold').fontSize(12);
    doc.text('TOTAL:', 350, y);
    doc.text(`₹ ${this.formatCurrency(invoice.totalAmount || invoice.total || 0)}`, col5, y);

    // Payment info
    if (invoice.amountPaid && parseFloat(invoice.amountPaid) > 0) {
      y += 25;
      doc.font('Helvetica').fontSize(10);
      doc.text(`Amount Paid: ₹ ${this.formatCurrency(invoice.amountPaid)}`, 350, y);
      y += 15;
      doc.font('Helvetica-Bold');
      doc.text(`Balance Due: ₹ ${this.formatCurrency(invoice.balanceDue || 0)}`, 350, y);
    }

    // Notes
    if (invoice.notes) {
      doc.font('Helvetica').fontSize(10);
      doc.text('Notes:', 50, y + 40);
      doc.text(invoice.notes, 50, y + 55, { width: 300 });
    }

    // Terms
    if (invoice.terms) {
      doc.text('Terms & Conditions:', 50, y + 100);
      doc.fontSize(9).text(invoice.terms, 50, y + 115, { width: 500 });
    }

    // Footer
    doc.fontSize(8).fillColor('gray');
    doc.text('Generated by ARTHA Finance', 50, doc.page.height - 50, { align: 'center' });

    doc.end();
    return doc;
  }

  /**
   * Generate General Ledger PDF
   */
  async generateGeneralLedger(filters = {}) {
    const doc = new PDFDocument({ margin: 50, size: 'A4' });

    // Get data
    const { entries } = await ledgerService.getJournalEntries(filters, {
      page: 1,
      limit: 10000,
      sortBy: 'date',
      sortOrder: 'asc',
    });

    const summary = await ledgerService.getLedgerSummary();

    // Header
    doc.fontSize(20).text('General Ledger Report', { align: 'center' });
    doc.moveDown();

    // Date range
    doc.fontSize(10);
    if (filters.dateFrom || filters.dateTo) {
      const fromDate = filters.dateFrom
        ? new Date(filters.dateFrom).toLocaleDateString()
        : 'Beginning';
      const toDate = filters.dateTo
        ? new Date(filters.dateTo).toLocaleDateString()
        : 'Present';
      doc.text(`Period: ${fromDate} to ${toDate}`, { align: 'center' });
    }
    doc.text(`Generated: ${new Date().toLocaleString()}`, { align: 'center' });
    doc.moveDown(2);

    // Summary section
    doc.fontSize(14).text('Financial Summary', { underline: true });
    doc.moveDown(0.5);
    doc.fontSize(10);

    const summaryData = [
      ['Total Assets:', this.formatCurrency(summary.assets)],
      ['Total Liabilities:', this.formatCurrency(summary.liabilities)],
      ['Total Equity:', this.formatCurrency(summary.equity)],
      ['Total Income:', this.formatCurrency(summary.income)],
      ['Total Expenses:', this.formatCurrency(summary.expenses)],
      ['Net Income:', this.formatCurrency(summary.netIncome)],
    ];

    summaryData.forEach(([label, value]) => {
      doc.text(label, 50, doc.y, { continued: true, width: 200 });
      doc.text(value, 300, doc.y, { align: 'right' });
      doc.moveDown(0.3);
    });

    doc.moveDown(1);

    // Check if accounting equation is balanced
    if (summary.isBalanced) {
      doc.fillColor('green').text('✓ Accounting equation balanced', { align: 'center' });
    } else {
      doc
        .fillColor('red')
        .text(
          `⚠ Accounting equation unbalanced (Difference: ${this.formatCurrency(
            summary.balanceDifference
          )})`,
          { align: 'center' }
        );
    }

    doc.fillColor('black');
    doc.moveDown(2);

    // Journal Entries section
    doc.fontSize(14).text('Journal Entries', { underline: true });
    doc.moveDown(1);

    if (entries.length === 0) {
      doc.fontSize(10).text('No entries found for the specified period.');
    } else {
      // Table headers
      doc.fontSize(9);
      const tableTop = doc.y;
      const col1 = 50;
      const col2 = 130;
      const col3 = 250;
      const col4 = 370;
      const col5 = 450;

      doc
        .text('Entry #', col1, tableTop, { width: 70 })
        .text('Date', col2, tableTop, { width: 110 })
        .text('Account', col3, tableTop, { width: 110 })
        .text('Debit', col4, tableTop, { width: 70, align: 'right' })
        .text('Credit', col5, tableTop, { width: 70, align: 'right' });

      doc
        .moveTo(col1, doc.y + 2)
        .lineTo(550, doc.y + 2)
        .stroke();

      doc.moveDown(0.5);

      // Entries
      let totalDebits = new Decimal(0);
      let totalCredits = new Decimal(0);

      entries.forEach((entry) => {
        const startY = doc.y;

        // Check if we need a new page
        if (doc.y > 700) {
          doc.addPage();
          doc.fontSize(9);
        }

        // Entry number and date
        doc.text(entry.entryNumber, col1, doc.y, { width: 70 });
        doc.text(new Date(entry.date).toLocaleDateString(), col2, startY, {
          width: 110,
        });

        // Lines
        let lineY = startY;
        entry.lines.forEach((line) => {
          const accountName = line.account.name || 'Unknown';
          const debit = line.debit !== '0' ? this.formatCurrency(line.debit) : '-';
          const credit = line.credit !== '0' ? this.formatCurrency(line.credit) : '-';

          doc.text(accountName, col3, lineY, { width: 110 });
          doc.text(debit, col4, lineY, { width: 70, align: 'right' });
          doc.text(credit, col5, lineY, { width: 70, align: 'right' });

          totalDebits = totalDebits.plus(new Decimal(line.debit || 0));
          totalCredits = totalCredits.plus(new Decimal(line.credit || 0));

          lineY += 15;
        });

        doc.y = lineY;

        // Description
        doc.fontSize(8).fillColor('gray');
        doc.text(`  ${entry.description}`, col1, doc.y, { width: 500 });
        doc.fontSize(9).fillColor('black');

        doc.moveDown(0.8);
      });

      // Totals
      doc
        .moveTo(col1, doc.y)
        .lineTo(550, doc.y)
        .stroke();

      doc.moveDown(0.3);
      doc.fontSize(10).font('Helvetica-Bold');
      doc.text('TOTALS', col1, doc.y, { width: 290 });
      doc.text(this.formatCurrency(totalDebits.toString()), col4, doc.y, {
        width: 70,
        align: 'right',
      });
      doc.text(this.formatCurrency(totalCredits.toString()), col5, doc.y, {
        width: 70,
        align: 'right',
      });

      // Verify totals match
      if (totalDebits.equals(totalCredits)) {
        doc.moveDown(1);
        doc
          .fontSize(9)
          .font('Helvetica')
          .fillColor('green')
          .text('✓ Debits equal Credits', { align: 'center' });
      }
    }

    // Footer
    doc
      .fontSize(8)
      .fillColor('gray')
      .text(
        'ARTHA Finance v0.1 - Confidential',
        50,
        doc.page.height - 50,
        { align: 'center' }
      );

    doc.end();
    return doc;
  }

  /**
   * Format currency for display
   */
  formatCurrency(amount) {
    const num = new Decimal(amount);
    return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }
}

export default new PDFService();