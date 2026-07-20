const escapeCsv = (value) => {
  if (value === null || value === undefined) return '';
  const stringValue = String(value);
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  return stringValue;
};

export const toCsv = (rows, headers) => {
  const headerRow = headers.map(escapeCsv).join(',');
  const body = rows.map((row) => headers.map((key) => escapeCsv(row[key])).join(',')).join('\n');
  return [headerRow, body].filter(Boolean).join('\n');
};

export const flattenGSTR1Rows = (filing) => {
  const rows = [];
  const sections = ['b2b', 'b2cl', 'b2cs', 'cdnr', 'exp', 'nil'];
  sections.forEach((section) => {
    const items = filing?.sections?.[section] || [];
    items.forEach((item) => {
      rows.push({
        section,
        ...item,
      });
    });
  });
  return rows;
};

export const flattenGSTR3BRows = (filing) => [
  {
    section: 'outward_taxable',
    ...filing.outwardTaxable,
  },
  {
    section: 'zero_rated',
    ...filing.zeroRated,
  },
  {
    section: 'exempt',
    ...filing.exempt,
  },
  {
    section: 'reverse_charge',
    ...filing.reverseCharge,
  },
  {
    section: 'itc',
    ...filing.itc,
  },
  {
    section: 'tax_liability',
    ...filing.taxLiability,
  },
];

export const flattenTdsRows = (filing, type) => {
  if (type === 'FORM-26Q') {
    const rows = [];
    (filing.deductees || []).forEach((deductee) => {
      (deductee.entries || []).forEach((entry) => {
        rows.push({
          pan: deductee.pan,
          name: deductee.name,
          section: deductee.section,
          amount_paid: deductee.amount_paid,
          tds_deducted: deductee.tds_deducted,
          entry_number: entry.entry_number,
          transaction_date: entry.transaction_date,
          challan_number: entry.challan_number,
          challan_date: entry.challan_date,
          bank_bsr: entry.bank_bsr,
        });
      });
    });
    return rows;
  }
  return (filing.employees || []).map((employee) => ({
    employee_pan: employee.employee_pan,
    employee_name: employee.employee_name,
    employee_id: employee.employee_id,
    salary_basic: employee.salary_basic,
    salary_hra: employee.salary_hra,
    perquisites: employee.perquisites,
    other_allowances: employee.other_allowances,
    deductions: employee.deductions,
    employer_deductions: employee.employer_deductions,
    taxable_salary: employee.taxable_salary,
    tds_deducted: employee.tds_deducted,
    transaction_date: employee.transaction_date,
    challan_number: employee.challan_number,
    challan_date: employee.challan_date,
    bank_bsr: employee.bank_bsr,
  }));
};
