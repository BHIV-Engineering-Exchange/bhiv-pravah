import Decimal from 'decimal.js';

export const GST_VALIDATION_ERROR_CODE = 'GST_VALIDATION_ERROR';

const ALLOWED_RATES = [0, 5, 12, 18, 28];

const normalizeState = (state) => String(state || '').trim().toUpperCase();

const isAllowedRate = (rate) => {
  if (rate === null || rate === undefined || rate === '') return false;
  const rateDecimal = new Decimal(rate);
  return ALLOWED_RATES.some((allowed) => rateDecimal.equals(new Decimal(allowed)));
};

export const buildGSTValidationError = (message, details = {}) => {
  const error = new Error(message);
  error.code = GST_VALIDATION_ERROR_CODE;
  error.details = details;
  return error;
};

export const calculateGSTBreakdown = (input) => {
  const {
    transaction_type,
    amount,
    gst_rate,
    supplier_state,
    company_state,
  } = input || {};

  if (!transaction_type || !['sale', 'purchase'].includes(transaction_type)) {
    throw buildGSTValidationError('Invalid transaction type for GST', {
      field: 'transaction_type',
      value: transaction_type,
    });
  }

  if (amount === null || amount === undefined || amount === '') {
    throw buildGSTValidationError('GST amount is required', {
      field: 'amount',
      value: amount,
    });
  }

  if (!isAllowedRate(gst_rate)) {
    throw buildGSTValidationError('Invalid GST rate', {
      field: 'gst_rate',
      value: gst_rate,
      allowed: ALLOWED_RATES,
    });
  }

  const supplierState = normalizeState(supplier_state);
  const companyState = normalizeState(company_state);

  if (!supplierState || !companyState) {
    throw buildGSTValidationError('GST state values are required', {
      supplier_state,
      company_state,
    });
  }

  const taxableValue = new Decimal(amount);

  if (taxableValue.isNegative()) {
    throw buildGSTValidationError('GST amount cannot be negative', {
      field: 'amount',
      value: amount,
    });
  }

  const rateDecimal = new Decimal(gst_rate);
  const gstAmount = taxableValue.times(rateDecimal).dividedBy(100).toDecimalPlaces(2);
  const isInterstate = supplierState !== companyState;

  let cgst = new Decimal(0);
  let sgst = new Decimal(0);
  let igst = new Decimal(0);

  if (isInterstate) {
    igst = gstAmount;
  } else {
    cgst = gstAmount.dividedBy(2).toDecimalPlaces(2);
    sgst = gstAmount.minus(cgst);
  }

  const totalAmount = taxableValue.plus(gstAmount).toDecimalPlaces(2);

  return {
    taxable_value: taxableValue.toDecimalPlaces(2).toString(),
    cgst: cgst.toString(),
    sgst: sgst.toString(),
    igst: igst.toString(),
    total_amount: totalAmount.toString(),
    transaction_type,
    gst_rate: rateDecimal.toNumber(),
    supplier_state: supplierState,
    company_state: companyState,
    is_interstate: isInterstate,
  };
};

export const validateGSTDetailShape = (detail) => {
  if (!detail || typeof detail !== 'object') {
    throw buildGSTValidationError('GST detail is missing', {
      field: 'gstDetails',
    });
  }

  const requiredFields = [
    'transaction_type',
    'gst_rate',
    'supplier_state',
    'company_state',
    'taxable_value',
    'cgst',
    'sgst',
    'igst',
  ];

  const missingFields = requiredFields.filter((field) => detail[field] === undefined || detail[field] === null);
  if (missingFields.length) {
    throw buildGSTValidationError('GST detail has missing fields', {
      missingFields,
    });
  }

  if (!isAllowedRate(detail.gst_rate)) {
    throw buildGSTValidationError('Invalid GST rate in detail', {
      field: 'gst_rate',
      value: detail.gst_rate,
      allowed: ALLOWED_RATES,
    });
  }

  return true;
};

export const GST_ENGINE = {
  calculateGSTBreakdown,
  validateGSTDetailShape,
  normalizeState,
  isAllowedRate,
  allowedRates: () => [...ALLOWED_RATES],
};
