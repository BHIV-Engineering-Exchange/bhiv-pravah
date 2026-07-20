import React from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  PieChart, 
  TrendingUp, 
  TrendingDown,
  Users,
  Clock,
  Calendar,
  Target,
  Award,
  AlertTriangle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';

const AttendanceStats = ({ data }) => {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded mb-4" />
              <div className="h-8 bg-gray-200 rounded mb-2" />
              <div className="h-3 bg-gray-200 rounded w-2/3" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const statsCards = [
    {
      title: "Total Employees",
      value: data.totalEmployees || 0,
      icon: Users,
      color: "blue",
      description: "Active employees in system"
    },
    {
      title: "Present Today",
      value: data.presentToday || 0,
      icon: Target,
      color: "green",
      description: `${((data.presentToday / data.totalEmployees) * 100).toFixed(1)}% attendance rate`
    },
    {
      title: "Average Hours",
      value: `${(data.avgHoursToday || 0).toFixed(1)}h`,
      icon: Clock,
      color: "purple",
      description: "Per employee today"
    },
    {
      title: "On Time Rate",
      value: `${(data.onTimePercentage || 0).toFixed(1)}%`,
      icon: Award,
      color: "yellow",
      description: "Punctuality score"
    },
    {
      title: "Overtime Hours",
      value: `${(data.totalOvertimeHours || 0).toFixed(1)}h`,
      icon: TrendingUp,
      color: "red",
      description: "Total overtime today"
    },
    {
      title: "Late Arrivals",
      value: data.lateToday || 0,
      icon: AlertTriangle,
      color: "orange",
      description: "Employees late today"
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: "from-blue-50 to-cyan-50 text-blue-600 bg-blue-100",
      green: "from-green-50 to-emerald-50 text-green-600 bg-green-100",
      purple: "from-purple-50 to-violet-50 text-purple-600 bg-purple-100",
      yellow: "from-yellow-50 to-amber-50 text-yellow-600 bg-yellow-100",
      red: "from-red-50 to-rose-50 text-red-600 bg-red-100",
      orange: "from-orange-50 to-yellow-50 text-orange-600 bg-orange-100"
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statsCards.map((stat, index) => {
          const colorClasses = getColorClasses(stat.color);
          const [bgGradient, textColor, iconBg] = colorClasses.split(' ');
          
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className={`border-0 shadow-lg bg-gradient-to-br ${bgGradient}`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-sm font-medium ${textColor}`}>
                        {stat.title}
                      </p>
                      <p className={`text-2xl font-bold ${textColor.replace('text-', 'text-').replace('-600', '-900')}`}>
                        {stat.value}
                      </p>
                      <p className={`text-xs ${textColor.replace('-600', '-700')} mt-1`}>
                        {stat.description}
                      </p>
                    </div>
                    <div className={`p-3 ${iconBg} rounded-full`}>
                      <stat.icon className={`w-6 h-6 ${textColor}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Attendance Breakdown
            </CardTitle>
            <CardDescription>Today's attendance distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Present</span>
                <span className="text-sm text-green-600 font-semibold">
                  {data.presentToday || 0} ({((data.presentToday / data.totalEmployees) * 100).toFixed(1)}%)
                </span>
              </div>
              <Progress 
                value={(data.presentToday / data.totalEmployees) * 100} 
                className="h-2"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Absent</span>
                <span className="text-sm text-red-600 font-semibold">
                  {data.absentToday || 0} ({((data.absentToday / data.totalEmployees) * 100).toFixed(1)}%)
                </span>
              </div>
              <Progress 
                value={(data.absentToday / data.totalEmployees) * 100} 
                className="h-2"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Late</span>
                <span className="text-sm text-yellow-600 font-semibold">
                  {data.lateToday || 0} ({((data.lateToday / data.totalEmployees) * 100).toFixed(1)}%)
                </span>
              </div>
              <Progress 
                value={(data.lateToday / data.totalEmployees) * 100} 
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Performance Metrics
            </CardTitle>
            <CardDescription>Key performance indicators</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {(data.avgHoursToday || 0).toFixed(1)}h
                </div>
                <div className="text-sm text-blue-700">Avg Hours</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {(data.onTimePercentage || 0).toFixed(1)}%
                </div>
                <div className="text-sm text-green-700">On Time</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {(data.totalOvertimeHours || 0).toFixed(1)}h
                </div>
                <div className="text-sm text-purple-700">Overtime</div>
              </div>
              
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {data.productivityScore || 85}%
                </div>
                <div className="text-sm text-yellow-700">Productivity</div>
              </div>
            </div>

            {/* Trends */}
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Trends</h4>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-sm">Attendance up 5% from last week</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-red-500" />
                <span className="text-sm">Late arrivals down 2%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department Breakdown */}
      {data.departmentStats && (
        <Card>
          <CardHeader>
            <CardTitle>Department Breakdown</CardTitle>
            <CardDescription>Attendance by department</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.departmentStats.map((dept, index) => (
                <div key={dept.name} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{dept.name}</h4>
                    <Badge variant="outline">
                      {dept.present}/{dept.total}
                    </Badge>
                  </div>
                  <Progress 
                    value={(dept.present / dept.total) * 100} 
                    className="h-2"
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    {((dept.present / dept.total) * 100).toFixed(1)}% present
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AttendanceStats;
