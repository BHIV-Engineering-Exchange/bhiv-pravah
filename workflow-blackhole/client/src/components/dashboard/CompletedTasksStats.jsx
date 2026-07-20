"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { Progress } from "../ui/progress"
import { Loader2, CheckCircle2, Clock, AlertTriangle } from "lucide-react"
import { useToast } from "../../hooks/use-toast"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { api } from "@/lib/api"

export function CompletedTasksStats() {
  const { toast } = useToast()
  const [stats, setStats] = useState({
    total: 0,
    approved: 0,
    pending: 0,
    rejected: 0,
    noSubmission: 0,
    byDepartment: [],
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true)
        
        // Fetch completed tasks using the proper API method with authentication
        const tasks = await api.tasks.getTasks({ status: 'Completed' })

        // Fetch all submissions using the proper API method with authentication
        let submissions = []
        try {
          submissions = await api.get('/submissions')
        } catch (submissionError) {
          console.warn('Could not fetch submissions:', submissionError)
          // Continue without submissions data
          submissions = []
        }

        // Fetch departments using the proper API method
        const departmentsResponse = await api.departments.getDepartments()
        console.log('Departments response:', departmentsResponse)
        
        // Handle different response formats - check if it's wrapped in success/data structure
        let departments = []
        if (Array.isArray(departmentsResponse)) {
          departments = departmentsResponse
        } else if (departmentsResponse?.success && Array.isArray(departmentsResponse.data)) {
          departments = departmentsResponse.data
        } else if (departmentsResponse?.data && Array.isArray(departmentsResponse.data)) {
          departments = departmentsResponse.data
        } else {
          console.warn('Unexpected departments response format:', departmentsResponse)
          departments = []
        }

        console.log('Processed departments:', departments)

        // Calculate stats
        const total = Array.isArray(tasks) ? tasks.length : 0
        let approved = 0
        let pending = 0
        let rejected = 0
        let noSubmission = 0

        // Department stats initialization - ensure departments is an array
        const departmentStats = departments.map((dept) => ({
          id: dept._id,
          name: dept.name,
          color: dept.color,
          total: 0,
          approved: 0,
          pending: 0,
          rejected: 0,
          noSubmission: 0,
        }))

        // Process tasks and submissions
        if (Array.isArray(tasks)) {
          tasks.forEach((task) => {
            const submission = Array.isArray(submissions) ? submissions.find((sub) => sub.task?._id === task._id) : null
            const deptIndex = task.department ? departmentStats.findIndex((d) => d.id === task.department._id) : -1

            if (deptIndex >= 0) {
              departmentStats[deptIndex].total++
            }

            if (submission) {
              if (submission.status === "Approved") {
                approved++
                if (deptIndex >= 0) departmentStats[deptIndex].approved++
              } else if (submission.status === "Rejected") {
                rejected++
                if (deptIndex >= 0) departmentStats[deptIndex].rejected++
              } else {
                pending++
                if (deptIndex >= 0) departmentStats[deptIndex].pending++
              }
            } else {
              noSubmission++
              if (deptIndex >= 0) departmentStats[deptIndex].noSubmission++
            }
          })
        }

        // Filter out departments with no completed tasks
        const filteredDeptStats = departmentStats.filter((dept) => dept.total > 0)

        setStats({
          total,
          approved,
          pending,
          rejected,
          noSubmission,
          byDepartment: filteredDeptStats,
        })
      } catch (error) {
        console.error("Error fetching stats:", error)
        toast({
          title: "Error",
          description: "Failed to load completion statistics",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchStats()
  }, [toast])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Completion Statistics</CardTitle>
          <CardDescription>Overview of task submissions and approvals</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const submissionData = [
    { name: "Approved", value: stats.approved, color: "#22c55e" },
    { name: "Pending", value: stats.pending, color: "#f59e0b" },
    { name: "Rejected", value: stats.rejected, color: "#ef4444" },
    { name: "No Submission", value: stats.noSubmission, color: "#94a3b8" },
  ].filter((item) => item.value > 0)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* ========== COMPLETION STATISTICS CARD ========== */}
      <Card className="border-l-4 border-l-green-500 overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-green-500/5 to-transparent">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-green-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
            <CardTitle className="text-base">Completion Statistics</CardTitle>
          </div>
          <CardDescription>Quick overview of all submissions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          <div className="grid grid-cols-2 gap-4">
            <Card className="bg-green-50 dark:bg-green-900/20 border-none">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-green-600 dark:text-green-400">Approved</p>
                    <p className="text-2xl font-bold text-green-700 dark:text-green-300">{stats.approved}</p>
                  </div>
                  <div className="bg-green-100 dark:bg-green-800/30 p-2 rounded-full">
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-amber-50 dark:bg-amber-900/20 border-none">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-amber-600 dark:text-amber-400">Pending</p>
                    <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">{stats.pending}</p>
                  </div>
                  <div className="bg-amber-100 dark:bg-amber-800/30 p-2 rounded-full">
                    <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-red-50 dark:bg-red-900/20 border-none">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-red-600 dark:text-red-400">Rejected</p>
                    <p className="text-2xl font-bold text-red-700 dark:text-red-300">{stats.rejected}</p>
                  </div>
                  <div className="bg-red-100 dark:bg-red-800/30 p-2 rounded-full">
                    <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-50 dark:bg-slate-800/50 border-none">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-600 dark:text-slate-400">No Submission</p>
                    <p className="text-2xl font-bold text-slate-700 dark:text-slate-300">{stats.noSubmission}</p>
                  </div>
                  <div className="bg-slate-200 dark:bg-slate-700 p-2 rounded-full">
                    <Clock className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* ========== SUBMISSION STATUS CARD ========== */}
      <Card className="border-l-4 border-l-blue-500 overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-blue-500/5 to-transparent">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Clock className="h-4 w-4 text-blue-500" />
            </div>
            <CardTitle className="text-base">Submission Status</CardTitle>
          </div>
          <CardDescription>Percentage breakdown of submissions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-sm">Approved</span>
            <span className="text-sm font-medium">{stats.total > 0 ? Math.round((stats.approved / stats.total) * 100) : 0}%</span>
          </div>
          <Progress value={stats.total > 0 ? (stats.approved / stats.total) * 100 : 0} className="h-2 bg-slate-100 dark:bg-slate-800" />
          
          <div className="flex items-center justify-between">
            <span className="text-sm">Pending Review</span>
            <span className="text-sm font-medium">{stats.total > 0 ? Math.round((stats.pending / stats.total) * 100) : 0}%</span>
          </div>
          <Progress value={stats.total > 0 ? (stats.pending / stats.total) * 100 : 0} className="h-2 bg-slate-100 dark:bg-slate-800" />
          
          <div className="flex items-center justify-between">
            <span className="text-sm">Rejected</span>
            <span className="text-sm font-medium">{stats.total > 0 ? Math.round((stats.rejected / stats.total) * 100) : 0}%</span>
          </div>
          <Progress value={stats.total > 0 ? (stats.rejected / stats.total) * 100 : 0} className="h-2 bg-slate-100 dark:bg-slate-800" />
          
          <div className="flex items-center justify-between">
            <span className="text-sm">No Submission</span>
            <span className="text-sm font-medium">{stats.total > 0 ? Math.round((stats.noSubmission / stats.total) * 100) : 0}%</span>
          </div>
          <Progress value={stats.total > 0 ? (stats.noSubmission / stats.total) * 100 : 0} className="h-2 bg-slate-100 dark:bg-slate-800" />
        </CardContent>
      </Card>

      {/* ========== SUBMISSION DISTRIBUTION CARD ========== */}
      <Card className="border-l-4 border-l-purple-500 overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-purple-500/5 to-transparent">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4 text-purple-500" />
            </div>
            <CardTitle className="text-base">Submission Distribution</CardTitle>
          </div>
          <CardDescription>Visual breakdown of all submissions</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={submissionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {submissionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* ========== COMPLETION BY DEPARTMENT CARD ========== */}
      {stats.byDepartment.length > 0 && (
        <Card className="border-l-4 border-l-orange-500 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-orange-500/5 to-transparent">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
              </div>
              <CardTitle className="text-base">Completion by Department</CardTitle>
            </div>
            <CardDescription>Department-wise submission breakdown</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {stats.byDepartment.map((dept) => (
              <div key={dept.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${dept.color}`} />
                    <span className="text-sm font-medium">{dept.name}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {dept.approved}/{dept.total} approved
                  </span>
                </div>
                <div className="flex h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <div
                    className="bg-green-500 h-full"
                    style={{ width: `${dept.total > 0 ? (dept.approved / dept.total) * 100 : 0}%` }}
                  ></div>
                  <div
                    className="bg-amber-500 h-full"
                    style={{ width: `${dept.total > 0 ? (dept.pending / dept.total) * 100 : 0}%` }}
                  ></div>
                  <div
                    className="bg-red-500 h-full"
                    style={{ width: `${dept.total > 0 ? (dept.rejected / dept.total) * 100 : 0}%` }}
                  ></div>
                  <div
                    className="bg-slate-400 h-full"
                    style={{ width: `${dept.total > 0 ? (dept.noSubmission / dept.total) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}