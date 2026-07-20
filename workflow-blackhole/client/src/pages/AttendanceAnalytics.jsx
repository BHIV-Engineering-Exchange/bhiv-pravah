import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, 
  Users, 
  TrendingUp, 
  Clock, 
  MapPin, 
  Upload,
  Download,
  Filter,
  RefreshCw,
  BarChart3,
  PieChart,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { useAttendanceAnalytics } from '../hooks/use-attendance';
import { useAuth } from '../context/auth-context';
import { toast } from '../hooks/use-toast';
import ExcelUpload from '../components/attendance/ExcelUpload';
import AttendanceChart from '../components/attendance/AttendanceChart';
import AttendanceSummary from '../components/attendance/AttendanceSummary';
import TopPerformers from '../components/attendance/TopPerformers';

const AttendanceAnalytics = () => {
  const { user } = useAuth();
  const [dateRange, setDateRange] = useState({
    startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [showUpload, setShowUpload] = useState(false);

  const { 
    data: analytics, 
    loading, 
    error, 
    refresh,
    startAutoRefresh,
    stopAutoRefresh,
    isAutoRefreshing
  } = useAttendanceAnalytics({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    department: selectedDepartment
  });

  // Removed auto-refresh to prevent unnecessary server calls
  // Users can manually refresh using the refresh button

  const handleDateRangeChange = (field, value) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  const handleExcelUpload = async (result) => {
    if (result.success) {
      toast({
        title: "Upload Successful",
        description: `Processed ${result.summary.processed} attendance records`,
        variant: "default"
      });
      refresh(); // Refresh analytics after upload
    }
  };

  const exportData = () => {
    if (!analytics) return;
    
    // Create CSV data
    const csvData = [
      ['Date', 'Total Employees', 'Present', 'Absent', 'Attendance Rate', 'Avg Hours'],
      ...analytics.dailyBreakdown.map(day => [
        day.date,
        day.totalEmployees,
        day.presentCount,
        day.absentCount,
        `${day.attendanceRate}%`,
        day.avgHours
      ])
    ];

    const csv = csvData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance-analytics-${dateRange.startDate}-${dateRange.endDate}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6 transition-colors duration-300">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-7xl mx-auto space-y-6"
      >
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <BarChart3 className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <motion.h1 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="text-3xl font-bold tracking-tight"
              >
                Attendance Analytics
              </motion.h1>
              <motion.p 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="text-muted-foreground"
              >
                Real-time attendance insights and analytics
              </motion.p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Date Range Filters */}
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Action Buttons */}
            <Button
              onClick={refresh}
              disabled={loading}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <Button
              onClick={() => setShowUpload(true)}
              variant="outline"
              size="sm"
              className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white border-0 hover:from-green-600 hover:to-emerald-600"
            >
              <Upload className="w-4 h-4" />
              Upload Excel
            </Button>

            <Button
              onClick={exportData}
              disabled={!analytics}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Manual refresh only - auto-refresh removed */}

        {/* Error State */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3"
            >
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span className="text-red-700">{error}</span>
              <Button
                onClick={refresh}
                variant="outline"
                size="sm"
                className="ml-auto"
              >
                Retry
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        {analytics && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4 border-2 rounded-xl p-1 bg-muted/20">
              <TabsTrigger value="overview" className="flex items-center gap-2 rounded-lg data-[state=active]:bg-green-500 data-[state=active]:text-white transition-all">
                <BarChart3 className="w-4 h-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="trends" className="flex items-center gap-2 rounded-lg data-[state=active]:bg-green-500 data-[state=active]:text-white transition-all">
                <TrendingUp className="w-4 h-4" />
                Trends
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center gap-2 rounded-lg data-[state=active]:bg-green-500 data-[state=active]:text-white transition-all">
                <Users className="w-4 h-4" />
                Performance
              </TabsTrigger>
              <TabsTrigger value="insights" className="flex items-center gap-2 rounded-lg data-[state=active]:bg-green-500 data-[state=active]:text-white transition-all">
                <Activity className="w-4 h-4" />
                AI Insights
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <AttendanceSummary data={analytics.summary} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <AttendanceChart data={analytics.dailyBreakdown} />
                <TopPerformers data={analytics.topPerformers} />
              </div>
            </TabsContent>

            <TabsContent value="trends" className="space-y-6">
              {/* Trends content will be added */}
              <Card>
                <CardHeader>
                  <CardTitle>Attendance Trends</CardTitle>
                  <CardDescription>
                    Historical attendance patterns and trends
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-gray-500">
                    Trends visualization coming soon...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="performance" className="space-y-6">
              {/* Performance content will be added */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                  <CardDescription>
                    Detailed performance analysis and metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-gray-500">
                    Performance metrics coming soon...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="insights" className="space-y-6">
              {/* AI Insights content will be added */}
              <Card>
                <CardHeader>
                  <CardTitle>AI-Powered Insights</CardTitle>
                  <CardDescription>
                    Intelligent analysis and recommendations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8 text-gray-500">
                    AI insights coming soon...
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}

        {/* Excel Upload Modal */}
        <ExcelUpload
          isOpen={showUpload}
          onClose={() => setShowUpload(false)}
          onUpload={handleExcelUpload}
        />
      </motion.div>
    </div>
  );
};

export default AttendanceAnalytics;
