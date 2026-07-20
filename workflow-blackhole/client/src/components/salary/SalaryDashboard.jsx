import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  DollarSign, 
  Users, 
  Calculator, 
  TrendingUp,
  TrendingDown,
  Calendar,
  Settings,
  Download,
  Upload,
  Filter,
  Search,
  Eye,
  Edit,
  Plus,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  FileText,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Progress } from '../ui/progress';
import { useAuth } from '../../context/auth-context';
import { useToast } from '../../hooks/use-toast';
import api from '../../lib/api';

const SalaryDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [salaryData, setSalaryData] = useState([]);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    totalPayroll: 0,
    avgSalary: 0,
    pendingCalculations: 0,
    completedCalculations: 0,
    discrepancies: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [workingDays, setWorkingDays] = useState(22);
  const [calculating, setCalculating] = useState(false);

  // Fetch salary data
  const fetchSalaryData = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/salary/dashboard?month=${selectedMonth}&year=${selectedYear}`);
      if (response.data.success) {
        setSalaryData(response.data.salaryData);
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error fetching salary data:', error);
      toast({
        title: "Error",
        description: "Failed to fetch salary data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Calculate salaries for all employees
  const calculateAllSalaries = async () => {
    try {
      setCalculating(true);
      const response = await api.post('/salary/calculate-bulk', {
        month: selectedMonth,
        year: selectedYear,
        workingDays
      });

      if (response.data.success) {
        toast({
          title: "Calculation Complete",
          description: `Calculated salaries for ${response.data.summary.successful} employees`,
          variant: "default"
        });
        
        // Refresh data
        await fetchSalaryData();
      }
    } catch (error) {
      console.error('Error calculating salaries:', error);
      toast({
        title: "Calculation Failed",
        description: error.response?.data?.error || "Failed to calculate salaries",
        variant: "destructive"
      });
    } finally {
      setCalculating(false);
    }
  };

  // Calculate salary for specific employee
  const calculateEmployeeSalary = async (employeeId) => {
    try {
      const response = await api.post(`/salary/calculate/${employeeId}`, {
        month: selectedMonth,
        year: selectedYear,
        workingDays
      });

      if (response.data.success) {
        toast({
          title: "Calculation Complete",
          description: `Salary calculated for ${response.data.calculation.user.name}`,
          variant: "default"
        });
        
        // Update the specific employee's data
        setSalaryData(prev => 
          prev.map(emp => 
            emp.user.id === employeeId 
              ? { ...emp, ...response.data.calculation }
              : emp
          )
        );
      }
    } catch (error) {
      console.error('Error calculating employee salary:', error);
      toast({
        title: "Calculation Failed",
        description: error.response?.data?.error || "Failed to calculate salary",
        variant: "destructive"
      });
    }
  };

  useEffect(() => {
    fetchSalaryData();
  }, [selectedMonth, selectedYear]);

  // Filter salary data
  const filteredSalaryData = salaryData.filter(emp => {
    const matchesSearch = emp.user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         emp.user.email.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesDepartment = filterDepartment === 'all' || 
                             emp.user.department?.name === filterDepartment;
    
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'calculated' && emp.salary) ||
                         (filterStatus === 'pending' && !emp.salary) ||
                         (filterStatus === 'discrepancy' && emp.recommendations?.some(r => r.severity === 'High'));
    
    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount || 0);
  };

  const getStatusColor = (employee) => {
    if (!employee.salary) return 'bg-gray-500';
    if (employee.recommendations?.some(r => r.severity === 'High')) return 'bg-red-500';
    if (employee.recommendations?.some(r => r.severity === 'Medium')) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusText = (employee) => {
    if (!employee.salary) return 'Pending';
    if (employee.recommendations?.some(r => r.severity === 'High')) return 'Needs Review';
    if (employee.recommendations?.some(r => r.severity === 'Medium')) return 'Minor Issues';
    return 'Calculated';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Calculator className="w-6 h-6 animate-pulse text-blue-500" />
          <span className="text-lg">Loading salary data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-green-50 to-blue-100 min-h-screen">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Salary Management</h1>
          <p className="text-gray-600 mt-1">
            Automated salary calculation and management system
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Select value={selectedMonth.toString()} onValueChange={(value) => setSelectedMonth(parseInt(value))}>
              <SelectTrigger className="w-32 bg-white/80 backdrop-blur-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-white/95 backdrop-blur-sm">
                {Array.from({ length: 12 }, (_, i) => (
                  <SelectItem key={i + 1} value={(i + 1).toString()}>
                    {new Date(0, i).toLocaleString('default', { month: 'long' })}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedYear.toString()} onValueChange={(value) => setSelectedYear(parseInt(value))}>
              <SelectTrigger className="w-24 bg-white/80 backdrop-blur-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-white/95 backdrop-blur-sm">
                {Array.from({ length: 5 }, (_, i) => (
                  <SelectItem key={2020 + i} value={(2020 + i).toString()}>
                    {2020 + i}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Working Days:</label>
            <Input
              type="number"
              value={workingDays}
              onChange={(e) => setWorkingDays(parseInt(e.target.value))}
              className="w-20 bg-white/80 backdrop-blur-sm"
              min="1"
              max="31"
            />
          </div>
          
          <Button 
            onClick={calculateAllSalaries}
            disabled={calculating}
            className="bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700"
          >
            {calculating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Calculating...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Calculate All
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Employees</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalEmployees}</p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Payroll</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(stats.totalPayroll)}</p>
                </div>
                <DollarSign className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Salary</p>
                  <p className="text-2xl font-bold text-blue-600">{formatCurrency(stats.avgSalary)}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Calculated</p>
                  <p className="text-2xl font-bold text-green-600">{stats.completedCalculations}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.pendingCalculations}</p>
                </div>
                <Clock className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Discrepancies</p>
                  <p className="text-2xl font-bold text-red-600">{stats.discrepancies}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Filters and Search */}
      <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search employees..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white/50"
                />
              </div>
            </div>

            <Select value={filterDepartment} onValueChange={setFilterDepartment}>
              <SelectTrigger className="w-full lg:w-48 bg-white/50">
                <SelectValue placeholder="Filter by department" />
              </SelectTrigger>
              <SelectContent className="bg-white/95 backdrop-blur-sm">
                <SelectItem value="all">All Departments</SelectItem>
                <SelectItem value="Engineering">Engineering</SelectItem>
                <SelectItem value="Marketing">Marketing</SelectItem>
                <SelectItem value="Sales">Sales</SelectItem>
                <SelectItem value="HR">HR</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full lg:w-48 bg-white/50">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent className="bg-white/95 backdrop-blur-sm">
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="calculated">Calculated</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="discrepancy">Needs Review</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 bg-white/80 backdrop-blur-sm">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="employees" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Employee Salaries
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Salary Distribution */}
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-blue-500" />
                  Salary Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Calculated</span>
                    <span className="text-sm text-gray-600">{stats.completedCalculations}/{stats.totalEmployees}</span>
                  </div>
                  <Progress
                    value={(stats.completedCalculations / stats.totalEmployees) * 100}
                    className="h-3"
                  />

                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{stats.completedCalculations}</div>
                      <div className="text-sm text-green-700">Completed</div>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">{stats.pendingCalculations}</div>
                      <div className="text-sm text-orange-700">Pending</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Calculations */}
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-green-500" />
                  Recent Calculations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {filteredSalaryData
                    .filter(emp => emp.salary)
                    .sort((a, b) => new Date(b.calculatedAt) - new Date(a.calculatedAt))
                    .slice(0, 5)
                    .map((emp, index) => (
                      <motion.div
                        key={emp.user.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg"
                      >
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={emp.user.avatar} />
                          <AvatarFallback className="bg-blue-500 text-white text-xs">
                            {emp.user.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {emp.user.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatCurrency(emp.salary?.netPay)}
                          </p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {getStatusText(emp)}
                        </Badge>
                      </motion.div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Employee Salaries Tab */}
        <TabsContent value="employees" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {filteredSalaryData.map((emp, index) => (
                <motion.div
                  key={emp.user.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{
                    scale: 1.02,
                    transition: { type: "spring", stiffness: 400, damping: 10 }
                  }}
                >
                  <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <Avatar className="w-12 h-12">
                              <AvatarImage src={emp.user.avatar} />
                              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                                {emp.user.name.split(' ').map(n => n[0]).join('')}
                              </AvatarFallback>
                            </Avatar>
                            <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${getStatusColor(emp)}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-gray-900 truncate">
                              {emp.user.name}
                            </h3>
                            <p className="text-xs text-gray-500 truncate">
                              {emp.user.email}
                            </p>
                            <Badge variant="outline" className="text-xs mt-1">
                              {emp.user.employeeType || 'Employee'}
                            </Badge>
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => calculateEmployeeSalary(emp.user.id)}
                            className="text-blue-500 hover:text-blue-700"
                          >
                            <Calculator className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-500 hover:text-gray-700"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Status:</span>
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              emp.salary ? 'border-green-500 text-green-700' : 'border-orange-500 text-orange-700'
                            }`}
                          >
                            {getStatusText(emp)}
                          </Badge>
                        </div>

                        {emp.salary && (
                          <>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Base Salary:</span>
                              <span className="font-medium">
                                {formatCurrency(emp.salary.baseSalary)}
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Net Pay:</span>
                              <span className="font-bold text-green-600">
                                {formatCurrency(emp.salary.netPay)}
                              </span>
                            </div>

                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Attendance:</span>
                              <span className={`font-medium ${
                                emp.attendance?.attendanceRate >= 90 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {emp.attendance?.attendanceRate || 0}%
                              </span>
                            </div>

                            {emp.workingHours && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">Hours:</span>
                                <span className="font-medium">
                                  {emp.workingHours.totalHours?.toFixed(1)}h
                                </span>
                              </div>
                            )}
                          </>
                        )}

                        {emp.recommendations && emp.recommendations.length > 0 && (
                          <div className="mt-3">
                            <div className="flex items-center gap-1 text-xs text-gray-600 mb-1">
                              <AlertTriangle className="w-3 h-3" />
                              <span>Issues ({emp.recommendations.length})</span>
                            </div>
                            <div className="space-y-1">
                              {emp.recommendations.slice(0, 2).map((rec, i) => (
                                <div key={i} className={`text-xs p-1 rounded ${
                                  rec.severity === 'High' ? 'bg-red-50 text-red-700' :
                                  rec.severity === 'Medium' ? 'bg-yellow-50 text-yellow-700' :
                                  'bg-blue-50 text-blue-700'
                                }`}>
                                  {rec.message}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Payroll Trends</CardTitle>
                <CardDescription>Monthly payroll analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Payroll analytics charts will be implemented here</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle>Department Breakdown</CardTitle>
                <CardDescription>Salary distribution by department</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <PieChart className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Department analytics will be implemented here</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SalaryDashboard;
