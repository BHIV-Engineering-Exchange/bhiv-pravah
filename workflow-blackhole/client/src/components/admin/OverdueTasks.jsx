"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { AlertCircle, Search, Calendar, User, Building2, X } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { API_URL } from "@/lib/api"
import { format } from "date-fns"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

// Configure axios with base URL
const api = axios.create({
  baseURL: `${API_URL}`,
})

const OverdueTasks = ({ open, onOpenChange }) => {
  const { toast } = useToast()
  const [overdueTasks, setOverdueTasks] = useState([])
  const [filteredTasks, setFilteredTasks] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    // Set auth header
    const token = localStorage.getItem("WorkflowToken")
    if (token) {
      api.defaults.headers.common["x-auth-token"] = token
    }
    
    if (open) {
      fetchOverdueTasks()
    }
  }, [open])

  useEffect(() => {
    // Filter tasks based on search query
    if (!searchQuery.trim()) {
      setFilteredTasks(overdueTasks)
    } else {
      const query = searchQuery.toLowerCase()
      const filtered = overdueTasks.filter((task) => {
        const assigneeName = task.assignee?.name?.toLowerCase() || ""
        const assigneeEmail = task.assignee?.email?.toLowerCase() || ""
        const taskTitle = task.title?.toLowerCase() || ""
        const departmentName = task.department?.name?.toLowerCase() || ""
        
        return (
          assigneeName.includes(query) ||
          assigneeEmail.includes(query) ||
          taskTitle.includes(query) ||
          departmentName.includes(query)
        )
      })
      setFilteredTasks(filtered)
    }
  }, [searchQuery, overdueTasks])

  const fetchOverdueTasks = async () => {
    try {
      setIsLoading(true)
      const response = await api.get("/tasks/overdue")
      setOverdueTasks(response.data)
      setFilteredTasks(response.data)
    } catch (err) {
      console.error("Error fetching overdue tasks:", err)
      toast({
        title: "Error",
        description: err.response?.data?.error || "Failed to fetch overdue tasks",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case "High":
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-300">
            High
          </Badge>
        )
      case "Medium":
        return (
          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200 dark:bg-yellow-900 dark:text-yellow-300">
            Medium
          </Badge>
        )
      case "Low":
        return (
          <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300">
            Low
          </Badge>
        )
      default:
        return <Badge>{priority}</Badge>
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case "Pending":
        return (
          <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-900 dark:text-gray-300">
            Pending
          </Badge>
        )
      case "In Progress":
        return (
          <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300">
            In Progress
          </Badge>
        )
      case "Completed":
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-300">
            Completed
          </Badge>
        )
      default:
        return <Badge>{status}</Badge>
    }
  }

  const getDaysOverdueBadge = (days) => {
    if (days <= 0) return null
    
    if (days <= 3) {
      return (
        <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-200 dark:bg-orange-900 dark:text-orange-300">
          {days} day{days !== 1 ? 's' : ''} overdue
        </Badge>
      )
    } else if (days <= 7) {
      return (
        <Badge className="bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-300">
          {days} days overdue
        </Badge>
      )
    } else {
      return (
        <Badge className="bg-red-600 text-white hover:bg-red-700 dark:bg-red-800 dark:text-red-100">
          {days} days overdue
        </Badge>
      )
    }
  }

  const getInitials = (name) => {
    if (!name) return "??"
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .substring(0, 2)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b bg-gradient-to-r from-red-500/5 to-transparent">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex-1">
              <DialogTitle className="text-2xl font-heading font-bold tracking-tight flex items-center gap-2">
                <AlertCircle className="h-6 w-6 text-red-500" />
                Overdue Tasks
              </DialogTitle>
              <DialogDescription className="mt-2">
                {filteredTasks.length} overdue task{filteredTasks.length !== 1 ? 's' : ''} found
              </DialogDescription>
            </div>
            <div className="relative w-full md:w-64">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by user name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-full"
              />
            </div>
          </div>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-red-500 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading overdue tasks...</p>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-lg font-semibold text-foreground">
                {searchQuery ? "No tasks found matching your search" : "No overdue tasks"}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                {searchQuery
                  ? "Try adjusting your search query"
                  : "All tasks are up to date!"}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">User</TableHead>
                    <TableHead>Task Title</TableHead>
                    <TableHead>Assignee</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Days Overdue</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTasks.map((task) => (
                    <TableRow key={task._id} className="hover:bg-red-50/50 dark:hover:bg-red-950/20">
                      <TableCell>
                        {task.assignee ? (
                          <Avatar className="h-8 w-8">
                            {task.assignee.avatar ? (
                              <AvatarImage src={task.assignee.avatar} alt={task.assignee.name} />
                            ) : (
                              <AvatarFallback className="bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                                {getInitials(task.assignee.name)}
                              </AvatarFallback>
                            )}
                          </Avatar>
                        ) : (
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-gray-100 text-gray-500">
                              <User className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                        )}
                      </TableCell>
                      <TableCell className="font-medium max-w-[300px]">
                        <div className="truncate" title={task.title}>
                          {task.title}
                        </div>
                      </TableCell>
                      <TableCell>
                        {task.assignee ? (
                          <div className="flex flex-col">
                            <span className="font-medium">{task.assignee.name}</span>
                            <span className="text-xs text-muted-foreground">{task.assignee.email}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">Unassigned</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {task.department ? (
                          <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${task.department.color || "bg-gray-500"}`}></div>
                            <span>{task.department.name}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">No department</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {task.dueDate ? (
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">
                              {format(new Date(task.dueDate), "MMM dd, yyyy")}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">No due date</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {getDaysOverdueBadge(task.daysOverdue || 0)}
                      </TableCell>
                      <TableCell>{getPriorityBadge(task.priority)}</TableCell>
                      <TableCell>{getStatusBadge(task.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default OverdueTasks

