import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Upload, X, FileText, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { bankStatementService } from '../../services';
import { PageHeader, Card, Button, Input, Label } from '../../components/common';

const uploadSchema = z.object({
  accountNumber: z.string().min(1, 'Account number is required'),
  bankName: z.string().min(1, 'Bank name is required'),
  accountHolderName: z.string().min(1, 'Account holder name is required'),
  startDate: z.string().min(1, 'Start date is required'),
  endDate: z.string().min(1, 'End date is required'),
  openingBalance: z.string().min(1, 'Opening balance is required'),
  closingBalance: z.string().min(1, 'Closing balance is required'),
});

const StatementsUpload = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(uploadSchema),
  });

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/pdf'];
    const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
    const validExtensions = ['csv', 'xls', 'xlsx', 'pdf'];

    if (!validTypes.includes(selectedFile.type) && !validExtensions.includes(fileExtension)) {
      toast.error('Invalid file type. Please upload CSV, Excel (XLS/XLSX), or PDF.');
      return;
    }

    if (selectedFile.size > 25 * 1024 * 1024) {
      toast.error('File size must be less than 25MB');
      return;
    }

    setFile(selectedFile);
  };

  const removeFile = () => {
    setFile(null);
  };

  const onSubmit = async (data) => {
    if (!file) {
      toast.error('Please select a file to upload');
      return;
    }

    setUploading(true);
    try {
      await bankStatementService.upload(file, data);
      toast.success('Bank statement uploaded! Auto-processing & reconciliation started.');
      navigate('/statements');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.message || 'Failed to upload statement');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Bank Statement"
        description="Upload your statement — transactions are auto-extracted, matched to invoices & expenses, and posted to the ledger"
        actions={
          <Button variant="outline" onClick={() => navigate('/statements')}>
            Back to Statements
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* File Upload */}
              <div>
                <Label>Statement File *</Label>
                <div
                  className={`mt-2 border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-300 hover:border-primary'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {file ? (
                    <div className="relative inline-block">
                      <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-lg border border-gray-200">
                        <FileText className="w-8 h-8 text-primary" />
                        <div className="text-left">
                          <p className="text-sm font-medium text-gray-900">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={removeFile}
                          className="ml-2 text-gray-400 hover:text-red-600"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-sm text-gray-600 mb-2">
                        Drag and drop your file here, or{' '}
                        <label className="text-primary font-medium cursor-pointer hover:underline">
                          browse
                          <input
                            type="file"
                            className="hidden"
                            accept=".csv,.xls,.xlsx,.pdf"
                            onChange={handleFileChange}
                          />
                        </label>
                      </p>
                      <p className="text-xs text-gray-500">
                        Supported formats: CSV, Excel (XLS/XLSX), PDF (Max 25MB)
                      </p>
                    </div>
                  )}
                </div>
                {!file && (
                  <div className="mt-2 flex items-start gap-2 text-xs text-amber-600">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <p>
                      For best results, export your bank statement as CSV with columns:
                      Date, Description, Debit, Credit, Balance
                    </p>
                  </div>
                )}
              </div>

              {/* Account Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="bankName">Bank Name *</Label>
                  <Input
                    id="bankName"
                    {...register('bankName')}
                    placeholder="e.g., HDFC Bank"
                  />
                  {errors.bankName && (
                    <p className="mt-1 text-sm text-red-600">{errors.bankName.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="accountNumber">Account Number *</Label>
                  <Input
                    id="accountNumber"
                    {...register('accountNumber')}
                    placeholder="e.g., 1234567890"
                  />
                  {errors.accountNumber && (
                    <p className="mt-1 text-sm text-red-600">{errors.accountNumber.message}</p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="accountHolderName">Account Holder Name *</Label>
                <Input
                  id="accountHolderName"
                  {...register('accountHolderName')}
                  placeholder="e.g., ABC Company Pvt Ltd"
                />
                {errors.accountHolderName && (
                  <p className="mt-1 text-sm text-red-600">{errors.accountHolderName.message}</p>
                )}
              </div>

              {/* Statement Period */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="startDate">Statement Start Date *</Label>
                  <Input
                    id="startDate"
                    type="date"
                    {...register('startDate')}
                  />
                  {errors.startDate && (
                    <p className="mt-1 text-sm text-red-600">{errors.startDate.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="endDate">Statement End Date *</Label>
                  <Input
                    id="endDate"
                    type="date"
                    {...register('endDate')}
                  />
                  {errors.endDate && (
                    <p className="mt-1 text-sm text-red-600">{errors.endDate.message}</p>
                  )}
                </div>
              </div>

              {/* Balances */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="openingBalance">Opening Balance *</Label>
                  <Input
                    id="openingBalance"
                    {...register('openingBalance')}
                    placeholder="0.00"
                    type="number"
                    step="0.01"
                  />
                  {errors.openingBalance && (
                    <p className="mt-1 text-sm text-red-600">{errors.openingBalance.message}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="closingBalance">Closing Balance *</Label>
                  <Input
                    id="closingBalance"
                    {...register('closingBalance')}
                    placeholder="0.00"
                    type="number"
                    step="0.01"
                  />
                  {errors.closingBalance && (
                    <p className="mt-1 text-sm text-red-600">{errors.closingBalance.message}</p>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex gap-3">
                <Button
                  type="submit"
                  disabled={uploading || !file}
                  className="flex-1"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Statement
                    </>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/statements')}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* Instructions */}
        <div>
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              How to Export Bank Statement
            </h3>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">HDFC Bank</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                  <li>Login to net banking</li>
                  <li>Go to Accounts → Download Statement</li>
                  <li>Select date range and account</li>
                  <li>Choose CSV format and download</li>
                </ol>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">ICICI Bank</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                  <li>Login to internet banking</li>
                  <li>Click on Accounts & Save</li>
                  <li>Select "Download Transaction History"</li>
                  <li>Choose CSV format</li>
                </ol>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-2">SBI</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                  <li>Login to Yono or internet banking</li>
                  <li>Go to Accounts → Transaction History</li>
                  <li>Select period and download</li>
                  <li>Export as CSV if in Excel</li>
                </ol>
              </div>

              <div className="pt-4 border-t">
                <h4 className="font-medium text-gray-700 mb-2">Required Columns</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>Transaction Date</li>
                  <li>Description / Particulars</li>
                  <li>Debit Amount</li>
                  <li>Credit Amount</li>
                  <li>Running Balance (optional)</li>
                </ul>
              </div>

              <div className="pt-4 border-t">
                <h4 className="font-medium text-gray-700 mb-2">Auto-Reconciliation</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  <li>CSV, Excel (XLS/XLSX), and PDF are all supported</li>
                  <li>Transactions are automatically matched to existing expenses</li>
                  <li>Credits are auto-matched to outstanding invoices</li>
                  <li>Unmatched debits auto-create new expense entries</li>
                  <li>Journal entries are posted automatically</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StatementsUpload;
