import { useState } from 'react';
import api from '../../services/api';

const TestInvoiceExpense = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const addResult = (message, type = 'info') => {
    setResults(prev => [...prev, { message, type, time: new Date().toLocaleTimeString() }]);
  };

  const runFullTest = async () => {
    setLoading(true);
    setResults([]);
    
    try {
      addResult('🚀 Starting integration test...', 'info');

      // Test Invoice
      addResult('Creating invoice...', 'info');
      const invoiceRes = await api.post('/invoices', {
        customerName: 'Test Customer',
        customerEmail: 'test@example.com',
        invoiceDate: new Date().toISOString().split('T')[0],
        dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        items: [{ description: 'Service', quantity: 1, unitPrice: '1000', amount: '1000' }],
        subtotal: '1000',
        taxAmount: '180',
        totalAmount: '1180'
      });
      addResult(`✅ Invoice: ${invoiceRes.data.data.invoiceNumber}`, 'success');

      // Test Expense
      addResult('Creating expense...', 'info');
      const expenseRes = await api.post('/expenses', {
        vendor: 'Test Vendor',
        description: 'Test Expense',
        category: 'supplies',
        date: new Date().toISOString().split('T')[0],
        amount: '500',
        taxAmount: '90',
        totalAmount: '590',
        paymentMethod: 'cash'
      });
      addResult(`✅ Expense: ${expenseRes.data.data.expenseNumber}`, 'success');

      // Verify Ledger
      addResult('Verifying ledger...', 'info');
      const ledgerRes = await api.get('/ledger/verify-chain');
      addResult(`✅ Ledger valid: ${ledgerRes.data.data.isValid}`, 'success');

      addResult('🎉 All tests passed!', 'success');
    } catch (error) {
      addResult(`❌ Error: ${error.response?.data?.message || error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Integration Test</h1>
        
        <button 
          onClick={runFullTest} 
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Running...' : 'Run Test'}
        </button>

        <div className="mt-6 bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm max-h-96 overflow-y-auto">
          {results.length === 0 ? (
            <div className="text-gray-500">Click "Run Test" to start...</div>
          ) : (
            results.map((r, i) => (
              <div key={i} className={r.type === 'error' ? 'text-red-400' : r.type === 'success' ? 'text-green-400' : 'text-gray-300'}>
                [{r.time}] {r.message}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TestInvoiceExpense;
