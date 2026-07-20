import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, 
  UserCheck, 
  UserX, 
  Clock, 
  Calendar,
  TrendingUp,
  TrendingDown,
  MapPin,
  Activity,
  Timer,
  Building,
  Wifi,
  WifiOff,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  PieChart,
  RefreshCw,
  Filter,
  Search,
  Eye,
  MoreVertical,
  Sparkles,
  Zap,
  Radio
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
import { useSocketContext } from '../../context/socket-context';
import api from '../../lib/api';
import { useToast } from '../../hooks/use-toast';

const LiveAttendanceDashboard = () => {
  const { user } = useAuth();
  const { socket } = useSocketContext();
  const { toast } = useToast();
  
  const [attendanceData, setAttendanceData] = useState([]);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentToday: 0,
    absentToday: 0,
    avgAttendance: 0,
    lateArrivals: 0,
    earlyDepartures: 0
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [activeTab, setActiveTab] = useState('overview');
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Fetch live attendance data
  const fetchLiveAttendance = async (showRefreshing = false) => {
    try {
      if (showRefreshing) setRefreshing(true);
      const response = await api.get('/attendance/live');
      if (response.data.success) {
        setAttendanceData(response.data.attendance);
        setStats(response.data.stats);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Error fetching live attendance:', error);
      toast({
        title: "Error",
        description: "Failed to fetch live attendance data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Socket event listeners for real-time updates
  useEffect(() => {
    if (socket) {
      socket.on('attendance:day-started', (data) => {
        setAttendanceData(prev => {
          const updated = prev.map(record => 
            record.user._id === data.userId 
              ? { ...record, startDayTime: data.startTime, isPresent: true }
              : record
          );
          return updated;
        });
        
        setStats(prev => ({
          ...prev,
          presentToday: prev.presentToday + 1,
          absentToday: Math.max(0, prev.absentToday - 1)
        }));
        
        toast({
          title: "Live Update",
          description: `${data.userName || 'Employee'} started their day`,
          variant: "default"
        });
      });

      socket.on('attendance:day-ended', (data) => {
        setAttendanceData(prev => 
          prev.map(record => 
            record.user._id === data.userId 
              ? { ...record, endDayTime: data.endTime, hoursWorked: data.hoursWorked }
              : record
          )
        );
      });

      return () => {
        socket.off('attendance:day-started');
        socket.off('attendance:day-ended');
      };
    }
  }, [socket, toast]);

  useEffect(() => {
    fetchLiveAttendance();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => fetchLiveAttendance(false), 30000);
    return () => clearInterval(interval);
  }, []);

  // Filter attendance data
  const filteredAttendance = attendanceData.filter(record => {
    const matchesSearch = record.user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         record.user.email.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterType === 'all' || 
                         (filterType === 'present' && record.isPresent) ||
                         (filterType === 'absent' && !record.isPresent) ||
                         (filterType === 'late' && record.isLate) ||
                         (filterType === 'remote' && record.isRemote);
    
    return matchesSearch && matchesFilter;
  });

  const calculateWorkingHours = (startTime, endTime) => {
    if (!startTime) return 0;
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    return Math.max(0, (end - start) / (1000 * 60 * 60));
  };

  const getStatusColor = (record) => {
    if (!record.isPresent) return 'bg-red-500';
    if (record.endDayTime) return 'bg-gray-500';
    if (calculateWorkingHours(record.startDayTime) >= 8) return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusText = (record) => {
    if (!record.isPresent) return 'Absent';
    if (record.endDayTime) return 'Completed';
    if (calculateWorkingHours(record.startDayTime) >= 8) return 'Full Day';
    return 'Working';
  };

  const getStatusBadgeVariant = (record) => {
    if (!record.isPresent) return 'destructive';
    if (record.endDayTime) return 'secondary';
    if (calculateWorkingHours(record.startDayTime) >= 8) return 'default';
    return 'default';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="mx-auto"
          >
            <Activity className="w-12 h-12 text-blue-600" />
          </motion.div>
          <div className="space-y-2">
            <p className="text-lg font-semibold text-gray-900">Loading Live Attendance</p>
            <p className="text-sm text-gray-500">Fetching real-time data...</p>
        </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Professional SaaS Header */}
      <div className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-4"
            >
              <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
        <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
                  Live Attendance Dashboard
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5 flex items-center gap-2">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Radio className="w-3 h-3 text-green-500" />
                  </motion.div>
                  Real-time monitoring • Updated {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-3"
            >
          <Button 
                onClick={() => fetchLiveAttendance(true)}
            variant="outline"
            size="sm"
                className="border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-200 shadow-sm"
                disabled={refreshing}
          >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          
              <div className="flex items-center gap-2 text-sm text-gray-700 bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Activity className="w-4 h-4 text-green-600" />
                </motion.div>
                <span className="font-medium text-green-700">Live Updates Active</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Professional Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[
            { label: 'Total Employees', value: stats.totalEmployees, icon: Users, color: 'blue', bgColor: 'bg-blue-50', iconBg: 'bg-blue-100', textColor: 'text-blue-700', iconColor: 'text-blue-600' },
            { label: 'Present Today', value: stats.presentToday, icon: UserCheck, color: 'green', bgColor: 'bg-green-50', iconBg: 'bg-green-100', textColor: 'text-green-700', iconColor: 'text-green-600' },
            { label: 'Absent Today', value: stats.absentToday, icon: UserX, color: 'red', bgColor: 'bg-red-50', iconBg: 'bg-red-100', textColor: 'text-red-700', iconColor: 'text-red-600' },
            { label: 'Avg Attendance', value: `${stats.avgAttendance}%`, icon: TrendingUp, color: 'purple', bgColor: 'bg-purple-50', iconBg: 'bg-purple-100', textColor: 'text-purple-700', iconColor: 'text-purple-600' },
            { label: 'Late Arrivals', value: stats.lateArrivals, icon: Clock, color: 'orange', bgColor: 'bg-orange-50', iconBg: 'bg-orange-100', textColor: 'text-orange-700', iconColor: 'text-orange-600' },
            { label: 'Early Departures', value: stats.earlyDepartures, icon: Timer, color: 'pink', bgColor: 'bg-pink-50', iconBg: 'bg-pink-100', textColor: 'text-pink-700', iconColor: 'text-pink-600' }
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
        <motion.div
                key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ y: -4 }}
        >
                <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
                  <CardContent className="p-5">
              <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 truncate">
                          {stat.label}
                        </p>
                        <p className={`text-2xl font-bold ${stat.textColor} leading-none`}>
                          {stat.value}
                        </p>
                </div>
                      <div className={`${stat.iconBg} p-3 rounded-lg flex-shrink-0 ml-3`}>
                        <Icon className={`w-5 h-5 ${stat.iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
            );
          })}
              </div>

        {/* Professional Filters */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
            <CardContent className="p-5">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-5 h-5" />
                  <Input
                    placeholder="Search employees by name or email..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-12 h-11 bg-white dark:bg-gray-700 dark:text-white border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>

                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-full lg:w-56 h-11 bg-white border-gray-300">
                    <Filter className="w-4 h-4 mr-2 text-gray-500" />
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent className="bg-white">
                    <SelectItem value="all">All Employees</SelectItem>
                    <SelectItem value="present">✅ Present</SelectItem>
                    <SelectItem value="absent">❌ Absent</SelectItem>
                    <SelectItem value="late">⏰ Late Arrivals</SelectItem>
                    <SelectItem value="remote">🏠 Remote Work</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Professional Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white border border-gray-200 shadow-sm p-1.5 rounded-lg h-auto">
            <TabsTrigger 
              value="overview" 
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-sm transition-all rounded-md py-2.5"
            >
            <Activity className="w-4 h-4" />
              <span className="font-medium">Live Overview</span>
          </TabsTrigger>
            <TabsTrigger 
              value="grid" 
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-sm transition-all rounded-md py-2.5"
            >
            <Users className="w-4 h-4" />
              <span className="font-medium">Employee Grid</span>
          </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-sm transition-all rounded-md py-2.5"
            >
            <BarChart3 className="w-4 h-4" />
              <span className="font-medium">Analytics</span>
          </TabsTrigger>
        </TabsList>

        {/* Live Overview Tab */}
          <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Attendance Progress Card */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                  <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-700">
                    <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white\">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <PieChart className="w-5 h-5 text-blue-600" />
                      </div>
                      <span className="text-lg font-semibold">Today's Attendance</span>
                </CardTitle>
              </CardHeader>
                  <CardContent className="pt-6 space-y-6">
                    <div className="space-y-3">
                  <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Present</span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{stats.presentToday}/{stats.totalEmployees}</span>
                  </div>
                  <Progress
                        value={stats.totalEmployees > 0 ? (stats.presentToday / stats.totalEmployees) * 100 : 0}
                        className="h-2.5 bg-gray-200 dark:bg-gray-700"
                  />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <motion.div 
                        whileHover={{ scale: 1.02 }}
                        className="text-center p-4 bg-green-50 rounded-xl border border-green-200"
                      >
                        <div className="text-3xl font-bold text-green-700">{stats.presentToday}</div>
                        <div className="text-sm font-medium text-green-600 mt-1">Present</div>
                      </motion.div>
                      <motion.div 
                        whileHover={{ scale: 1.02 }}
                        className="text-center p-4 bg-red-50 rounded-xl border border-red-200"
                      >
                        <div className="text-3xl font-bold text-red-700">{stats.absentToday}</div>
                        <div className="text-sm font-medium text-red-600 mt-1">Absent</div>
                      </motion.div>
                </div>
              </CardContent>
            </Card>
              </motion.div>

              {/* Recent Activity Card */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                  <CardHeader className="pb-4 border-b border-gray-100 dark:border-gray-700">
                    <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Zap className="w-5 h-5 text-green-600" />
                      </div>
                      <span className="text-lg font-semibold">Recent Activity</span>
                </CardTitle>
              </CardHeader>
                  <CardContent className="pt-6">
                    <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
                      <AnimatePresence>
                  {filteredAttendance
                    .filter(record => record.startDayTime)
                    .sort((a, b) => new Date(b.startDayTime) - new Date(a.startDayTime))
                    .slice(0, 5)
                    .map((record, index) => (
                      <motion.div
                        key={record._id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: 20 }}
                              transition={{ delay: index * 0.05 }}
                              whileHover={{ x: 4 }}
                              className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-600 hover:border-blue-200 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/20 transition-all cursor-pointer"
                      >
                              <Avatar className="w-10 h-10 ring-2 ring-white shadow-sm">
                          <AvatarImage src={record.user.avatar} />
                                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white text-sm font-semibold">
                            {record.user.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                            {record.user.name}
                          </p>
                                <p className="text-xs text-gray-500 dark:text-gray-300 flex items-center gap-1 mt-0.5">
                                  <Clock className="w-3 h-3" />
                                  Started at {new Date(record.startDayTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                              <Badge 
                                variant={getStatusBadgeVariant(record)}
                                className="text-xs font-medium flex-shrink-0"
                              >
                          {getStatusText(record)}
                        </Badge>
                      </motion.div>
                    ))}
                        {filteredAttendance.filter(record => record.startDayTime).length === 0 && (
                          <div className="text-center py-12 text-gray-500">
                            <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p className="font-medium">No recent activity</p>
                            <p className="text-sm mt-1">Activity will appear here when employees start their day</p>
                          </div>
                        )}
                      </AnimatePresence>
                </div>
              </CardContent>
            </Card>
              </motion.div>
          </div>
        </TabsContent>

        {/* Employee Grid Tab */}
          <TabsContent value="grid" className="space-y-6 mt-6">
            {filteredAttendance.length === 0 ? (
              <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                <CardContent className="py-16 text-center">
                  <UserX className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-500" />
                  <p className="text-lg font-semibold text-gray-700 dark:text-white mb-2">No employees found</p>
                  <p className="text-sm text-gray-500 dark:text-gray-300">Try adjusting your search or filter criteria</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            <AnimatePresence>
              {filteredAttendance.map((record, index) => {
                const workingHours = calculateWorkingHours(record.startDayTime, record.endDayTime);
                const isOnline = record.isPresent && !record.endDayTime;
                    const progress = Math.min(100, (workingHours / 8) * 100);

                return (
                  <motion.div
                    key={record._id}
                        initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ delay: index * 0.03 }}
                        whileHover={{ y: -4 }}
                  >
                        <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden h-full">
                          <CardContent className="p-5">
                            {/* Header with Avatar */}
                            <div className="flex items-start justify-between mb-5">
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div className="relative flex-shrink-0">
                                  <Avatar className="w-12 h-12 ring-2 ring-gray-100 shadow-sm">
                                <AvatarImage src={record.user.avatar} />
                                    <AvatarFallback className="bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 text-white font-semibold text-sm">
                                  {record.user.name.split(' ').map(n => n[0]).join('')}
                                </AvatarFallback>
                              </Avatar>
                                  <motion.div
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-white shadow-sm ${getStatusColor(record)}`}
                                  />
                            </div>
                            <div className="flex-1 min-w-0">
                                  <h3 className="font-bold text-gray-900 dark:text-white truncate text-base leading-tight">
                                {record.user.name}
                              </h3>
                                  <p className="text-xs text-gray-500 dark:text-gray-300 truncate mt-0.5">
                                {record.user.email}
                              </p>
                            </div>
                          </div>

                              <div className="flex-shrink-0">
                            {isOnline ? (
                                  <motion.div
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                  >
                                    <Wifi className="w-5 h-5 text-green-500" />
                                  </motion.div>
                            ) : (
                                  <WifiOff className="w-5 h-5 text-gray-300" />
                            )}
                          </div>
                        </div>

                            {/* Status and Info */}
                            <div className="space-y-3.5">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Status</span>
                            <Badge
                                  variant={getStatusBadgeVariant(record)}
                                  className="text-xs font-semibold"
                            >
                              {getStatusText(record)}
                            </Badge>
                          </div>

                          {record.startDayTime && (
                                <div className="flex items-center justify-between text-sm py-1.5 border-b border-gray-100 dark:border-gray-700">
                                  <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
                                    <Clock className="w-3.5 h-3.5" />
                                    Start:
                                  </span>
                                  <span className="font-semibold text-gray-900 dark:text-white">
                                {new Date(record.startDayTime).toLocaleTimeString([], {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                          )}

                          {record.endDayTime && (
                                <div className="flex items-center justify-between text-sm py-1.5 border-b border-gray-100 dark:border-gray-700">
                                  <span className="text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
                                    <CheckCircle className="w-3.5 h-3.5" />
                                    End:
                                  </span>
                                  <span className="font-semibold text-gray-900 dark:text-white">
                                {new Date(record.endDayTime).toLocaleTimeString([], {
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                          )}

                              <div className="flex items-center justify-between text-sm pt-1">
                                <span className="text-gray-600 dark:text-gray-400 font-medium">Hours Worked</span>
                                <span className={`font-bold text-lg ${workingHours >= 8 ? 'text-green-600' : workingHours >= 6 ? 'text-orange-600' : 'text-red-600'}`}>
                              {workingHours.toFixed(1)}h
                            </span>
                          </div>

                              {record.isPresent && !record.endDayTime && (
                                <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                                  <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-2">
                                    <span className="font-medium">Daily Progress</span>
                                    <span className="font-bold">{progress.toFixed(0)}%</span>
                              </div>
                              <Progress
                                    value={progress}
                                    className="h-2 bg-gray-200 dark:bg-gray-700"
                              />
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
            )}
        </TabsContent>

        {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                <CardHeader className="border-b border-gray-100 dark:border-gray-700">
                  <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <BarChart3 className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-lg font-semibold">Attendance Trends</span>
                  </CardTitle>
                  <CardDescription className="mt-2">Weekly attendance patterns</CardDescription>
              </CardHeader>
                <CardContent className="pt-6">
                  <div className="text-center py-16 text-gray-500 dark:text-gray-400">
                    <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-20" />
                    <p className="font-medium text-gray-700 dark:text-white">Analytics charts coming soon</p>
                    <p className="text-sm mt-2 text-gray-500 dark:text-gray-400">Visual insights will be displayed here</p>
                </div>
              </CardContent>
            </Card>

              <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                <CardHeader className="border-b border-gray-100 dark:border-gray-700">
                  <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <PieChart className="w-5 h-5 text-purple-600" />
                    </div>
                    <span className="text-lg font-semibold">Department Breakdown</span>
                  </CardTitle>
                  <CardDescription className="mt-2">Attendance by department</CardDescription>
              </CardHeader>
                <CardContent className="pt-6">
                  <div className="text-center py-16 text-gray-500 dark:text-gray-400">
                    <PieChart className="w-16 h-16 mx-auto mb-4 opacity-20" />
                    <p className="font-medium text-gray-700 dark:text-gray-300">Department analytics coming soon</p>
                    <p className="text-sm mt-2 text-gray-500 dark:text-gray-400">Detailed breakdowns will be available here</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
};

export default LiveAttendanceDashboard;
