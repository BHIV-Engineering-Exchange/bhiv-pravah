import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DollarSign, Clock, AlertTriangle, CheckCircle, History } from 'lucide-react';
import HoursManagement from '@/components/salary/HoursManagement';
import SalaryCalculation from '@/components/salary/SalaryCalculation';
import SpamUsers from '@/components/salary/SpamUsers';
import ConfirmedSalary from '@/components/salary/ConfirmedSalary';
import SalaryHistory from '@/components/salary/SalaryHistory';
import { useAuth } from '@/context/auth-context';

const NewSalaryManagement = () => {
  const { userId } = useParams();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('hours');

  // Use userId from params or current user
  const targetUserId = userId || user?._id || user?.id;

  // Lifted state for Salary Calculation - persists across tab changes
  const [salaryCalcState, setSalaryCalcState] = useState({
    startDate: null,
    endDate: null,
    holidays: [],
    userRates: {},
    usersData: []
  });

  // Function to switch to confirm tab (passed to SalaryCalculation)
  const goToConfirmTab = () => {
    setActiveTab('confirm');
  };

  if (!targetUserId) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Please select an employee or log in to view salary management.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Salary Management</h1>
        <p className="text-muted-foreground">
          Manage working hours and calculate salaries based on hourly rates
        </p>
      </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="hours" className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Hours
                  </TabsTrigger>
                  <TabsTrigger value="calculation" className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Calculation
                  </TabsTrigger>
                  <TabsTrigger value="confirm" className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Confirmed
                  </TabsTrigger>
                  <TabsTrigger value="history" className="flex items-center gap-2">
                    <History className="h-4 w-4" />
                    History
                  </TabsTrigger>
                  <TabsTrigger value="spam" className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Spam
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="hours" className="mt-6">
                  <HoursManagement userId={targetUserId} />
                </TabsContent>

                <TabsContent value="calculation" className="mt-6">
                  <SalaryCalculation 
                    userId={targetUserId} 
                    onConfirmSalary={goToConfirmTab}
                    persistedState={salaryCalcState}
                    onStateChange={setSalaryCalcState}
                  />
                </TabsContent>

                <TabsContent value="confirm" className="mt-6">
                  <ConfirmedSalary />
                </TabsContent>

                <TabsContent value="history" className="mt-6">
                  <SalaryHistory />
                </TabsContent>

                <TabsContent value="spam" className="mt-6">
                  <SpamUsers />
                </TabsContent>
              </Tabs>
    </div>
  );
};

export default NewSalaryManagement;

