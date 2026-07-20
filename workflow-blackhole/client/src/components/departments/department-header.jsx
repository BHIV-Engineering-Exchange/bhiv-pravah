"use client"

import { useState } from "react"
import { Button } from "../ui/button"
import { Plus, Building2 } from "lucide-react"
import { CreateDepartmentDialog } from "./create-department-dialog"

export function DepartmentHeader() {
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Building2 className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Departments</h1>
          <p className="text-muted-foreground">Manage departments and their tasks</p>
        </div>
      </div>
      <Button onClick={() => setIsCreateOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Department
      </Button>

      <CreateDepartmentDialog open={isCreateOpen} onOpenChange={setIsCreateOpen} />
    </div>
  )
}
