"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import { Label } from "../ui/label"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { Checkbox } from "../ui/checkbox"
import { Button } from "../ui/button"
import { api } from "../../lib/api"

export function TaskFilters({ onFilterChange }) {
  const [status, setStatus] = useState([])
  const [department, setDepartment] = useState([])
  const [priority, setPriority] = useState("all")
  const [departments, setDepartments] = useState([])

  // Fetch departments on mount
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await api.departments.getDepartments()
        console.log('TaskFilters - Departments response:', response)

        // Handle new API response format
        const data = response.success ? response.data : response
        setDepartments(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error("Error fetching departments:", error)
        setDepartments([])
      }
    }
    fetchDepartments()
  }, [])

  const handleStatusChange = (value, checked) => {
    setStatus(prev => 
      checked ? [...prev, value] : prev.filter(item => item !== value)
    )
  }

  const handleDepartmentChange = (value, checked) => {
    setDepartment(prev => 
      checked ? [...prev, value] : prev.filter(item => item !== value)
    )
  }

  const handleApplyFilters = () => {
    onFilterChange({
      status,
      department,
      priority: priority === "all" ? undefined : priority,
    })
  }

  return (
    <Card className="border-2 rounded-xl shadow-lg">
      <CardHeader className="border-b bg-muted/30">
        <CardTitle className="text-lg font-semibold">Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-foreground/90">Status</h3>
          <div className="space-y-2.5">
            {["Completed", "In Progress", "Pending"].map(stat => (
              <div key={stat} className="flex items-center space-x-2.5 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                <Checkbox 
                  id={`status-${stat.toLowerCase()}`} 
                  onCheckedChange={(checked) => handleStatusChange(stat, checked)}
                  className="data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                />
                <Label htmlFor={`status-${stat.toLowerCase()}`} className="cursor-pointer font-medium">{stat}</Label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-foreground/90">Department</h3>
          <div className="space-y-2.5 max-h-48 overflow-y-auto custom-scrollbar">
            {Array.isArray(departments) && departments.map(dept => (
              <div key={dept._id} className="flex items-center space-x-2.5 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                <Checkbox
                  id={`dept-${dept._id}`}
                  onCheckedChange={(checked) => handleDepartmentChange(dept._id, checked)}
                  className="data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                />
                <Label htmlFor={`dept-${dept._id}`} className="cursor-pointer font-medium">{dept.name}</Label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-foreground/90">Priority</h3>
          <RadioGroup value={priority} onValueChange={setPriority}>
            {["all", "High", "Medium", "Low"].map(prio => (
              <div key={prio} className="flex items-center space-x-2.5 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                <RadioGroupItem value={prio} id={`priority-${prio.toLowerCase()}`} className="border-2" />
                <Label htmlFor={`priority-${prio.toLowerCase()}`} className="cursor-pointer font-medium">
                  {prio === "all" ? "All" : prio}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <Button className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold" onClick={handleApplyFilters}>
          Apply Filters
        </Button>
      </CardContent>
    </Card>
  )
}
