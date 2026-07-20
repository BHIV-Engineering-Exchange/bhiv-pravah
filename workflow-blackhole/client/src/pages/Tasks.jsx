"use client"

import { useState } from "react"
import { TasksHeader } from "../components/tasks/tasks-header"
import { TasksList } from "../components/tasks/tasks-list"
import { TaskFilters } from "../components/tasks/task-filters"

function Tasks() {
  const [filters, setFilters] = useState({
    status: [],
    department: [],
    priority: undefined,
  })

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
  }

  return (
    <div className="space-y-6 pb-8">
      <TasksHeader />
      
      <div className="flex flex-col md:flex-row gap-6">
        <div className="md:w-1/4">
          <TaskFilters onFilterChange={handleFilterChange} />
        </div>
        <div className="flex-1">
          <TasksList filters={filters} />
        </div>
      </div>
    </div>
  )
}

export default Tasks
