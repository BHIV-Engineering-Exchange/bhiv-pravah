import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, User, Calendar, Save, X } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { useSalary } from '../../hooks/use-salary';

const SalaryForm = ({ isOpen, onClose, employee, onSuccess }) => {
  const { setSalaryInfo, addSalaryAdjustment, loading } = useSalary();
  
  const [formData, setFormData] = useState({
    baseSalary: '',
    currency: 'USD',
    salaryType: 'Monthly',
    payGrade: '',
    joiningDate: '',
    allowances: {
      housing: '',
      transport: '',
      medical: '',
      other: ''
    },
    deductions: {
      tax: '',
      insurance: '',
      other: ''
    },
    bankDetails: {
      accountNumber: '',
      bankName: '',
      routingNumber: ''
    },
    probationPeriod: {
      duration: 3,
      isCompleted: false
    }
  });

  const [mode, setMode] = useState('salary'); // 'salary' or 'adjustment'
  const [adjustmentData, setAdjustmentData] = useState({
    type: 'Bonus',
    amount: '',
    percentage: '',
    reason: '',
    isRecurring: false,
    frequency: 'One-time',
    effectiveDate: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    if (employee) {
      // Pre-fill form with employee data if available
      setFormData(prev => ({
        ...prev,
        joiningDate: employee.joiningDate || ''
      }));
    }
  }, [employee]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!employee?.id) return;

    try {
      if (mode === 'salary') {
        const success = await setSalaryInfo(employee.id, formData);
        if (success) {
          onSuccess?.();
        }
      } else {
        const success = await addSalaryAdjustment(employee.id, adjustmentData);
        if (success) {
          onSuccess?.();
        }
      }
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const handleChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const handleAdjustmentChange = (field, value) => {
    setAdjustmentData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            {employee ? `Salary Management - ${employee.name}` : 'Salary Management'}
          </DialogTitle>
        </DialogHeader>

        {/* Mode Toggle */}
        <div className="flex items-center gap-2 mb-6">
          <Button
            type="button"
            onClick={() => setMode('salary')}
            variant={mode === 'salary' ? 'default' : 'outline'}
            size="sm"
          >
            Set Salary
          </Button>
          <Button
            type="button"
            onClick={() => setMode('adjustment')}
            variant={mode === 'adjustment' ? 'default' : 'outline'}
            size="sm"
          >
            Add Adjustment
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {mode === 'salary' ? (
            <>
              {/* Basic Salary Information */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="baseSalary">Base Salary</Label>
                  <Input
                    id="baseSalary"
                    type="number"
                    placeholder="Enter base salary"
                    value={formData.baseSalary}
                    onChange={(e) => handleChange('baseSalary', parseFloat(e.target.value) || '')}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Select value={formData.currency} onValueChange={(value) => handleChange('currency', value)}>
                    <SelectTrigger className="bg-white">
                      <SelectValue placeholder="Select currency" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                      <SelectItem value="INR">INR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="salaryType">Salary Type</Label>
                  <Select value={formData.salaryType} onValueChange={(value) => handleChange('salaryType', value)}>
                    <SelectTrigger className="bg-white">
                      <SelectValue placeholder="Select salary type" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="Monthly">Monthly</SelectItem>
                      <SelectItem value="Annual">Annual</SelectItem>
                      <SelectItem value="Hourly">Hourly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="payGrade">Pay Grade</Label>
                  <Input
                    id="payGrade"
                    placeholder="e.g., L1, L2, Senior, etc."
                    value={formData.payGrade}
                    onChange={(e) => handleChange('payGrade', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="joiningDate">Joining Date</Label>
                <Input
                  id="joiningDate"
                  type="date"
                  value={formData.joiningDate}
                  onChange={(e) => handleChange('joiningDate', e.target.value)}
                  required
                />
              </div>

              {/* Allowances */}
              <div className="space-y-4">
                <Label className="text-base font-medium">Allowances</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="housingAllowance">Housing Allowance</Label>
                    <Input
                      id="housingAllowance"
                      type="number"
                      placeholder="0"
                      value={formData.allowances.housing}
                      onChange={(e) => handleChange('allowances.housing', parseFloat(e.target.value) || '')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="transportAllowance">Transport Allowance</Label>
                    <Input
                      id="transportAllowance"
                      type="number"
                      placeholder="0"
                      value={formData.allowances.transport}
                      onChange={(e) => handleChange('allowances.transport', parseFloat(e.target.value) || '')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="medicalAllowance">Medical Allowance</Label>
                    <Input
                      id="medicalAllowance"
                      type="number"
                      placeholder="0"
                      value={formData.allowances.medical}
                      onChange={(e) => handleChange('allowances.medical', parseFloat(e.target.value) || '')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="otherAllowance">Other Allowance</Label>
                    <Input
                      id="otherAllowance"
                      type="number"
                      placeholder="0"
                      value={formData.allowances.other}
                      onChange={(e) => handleChange('allowances.other', parseFloat(e.target.value) || '')}
                    />
                  </div>
                </div>
              </div>

              {/* Bank Details */}
              <div className="space-y-4">
                <Label className="text-base font-medium">Bank Details</Label>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="accountNumber">Account Number</Label>
                    <Input
                      id="accountNumber"
                      placeholder="Account number"
                      value={formData.bankDetails.accountNumber}
                      onChange={(e) => handleChange('bankDetails.accountNumber', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="bankName">Bank Name</Label>
                    <Input
                      id="bankName"
                      placeholder="Bank name"
                      value={formData.bankDetails.bankName}
                      onChange={(e) => handleChange('bankDetails.bankName', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="routingNumber">Routing Number</Label>
                    <Input
                      id="routingNumber"
                      placeholder="Routing number"
                      value={formData.bankDetails.routingNumber}
                      onChange={(e) => handleChange('bankDetails.routingNumber', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Salary Adjustment Form */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="adjustmentType">Adjustment Type</Label>
                  <Select value={adjustmentData.type} onValueChange={(value) => handleAdjustmentChange('type', value)}>
                    <SelectTrigger className="bg-white">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="Bonus">Bonus</SelectItem>
                      <SelectItem value="Increment">Increment</SelectItem>
                      <SelectItem value="Overtime">Overtime</SelectItem>
                      <SelectItem value="Deduction">Deduction</SelectItem>
                      <SelectItem value="Commission">Commission</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="effectiveDate">Effective Date</Label>
                  <Input
                    id="effectiveDate"
                    type="date"
                    value={adjustmentData.effectiveDate}
                    onChange={(e) => handleAdjustmentChange('effectiveDate', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="adjustmentAmount">Amount</Label>
                  <Input
                    id="adjustmentAmount"
                    type="number"
                    placeholder="Enter amount"
                    value={adjustmentData.amount}
                    onChange={(e) => handleAdjustmentChange('amount', parseFloat(e.target.value) || '')}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="adjustmentPercentage">Percentage (Optional)</Label>
                  <Input
                    id="adjustmentPercentage"
                    type="number"
                    placeholder="Enter percentage"
                    value={adjustmentData.percentage}
                    onChange={(e) => handleAdjustmentChange('percentage', parseFloat(e.target.value) || '')}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="adjustmentReason">Reason</Label>
                <Textarea
                  id="adjustmentReason"
                  placeholder="Reason for adjustment..."
                  value={adjustmentData.reason}
                  onChange={(e) => handleAdjustmentChange('reason', e.target.value)}
                  required
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              disabled={loading}
            >
              Cancel
            </Button>
            
            <Button
              type="submit"
              disabled={loading}
              className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
            >
              {loading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
                  />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  {mode === 'salary' ? 'Save Salary' : 'Add Adjustment'}
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default SalaryForm;
