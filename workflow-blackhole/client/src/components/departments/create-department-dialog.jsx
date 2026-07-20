"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { useToast } from "../../hooks/use-toast"
import { api } from "../../lib/api"

export function CreateDepartmentDialog({ open, onOpenChange }) {
  const { toast } = useToast()
  const [users, setUsers] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    lead: "",
    color: "bg-blue-500",
  })

  // Fetch users when dialog opens
  useEffect(() => {
    if (open) {
      const fetchUsers = async () => {
        try {
          const usersData = await api.users.getUsers()
          setUsers(usersData)
        } catch (error) {
          console.error("Error fetching users:", error)
          toast({
            title: "Error",
            description: "Failed to load users",
            variant: "destructive",
          })
        }
      }

      fetchUsers()
    }
  }, [open, toast])

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleColorSelect = (color) => {
    handleChange("color", color)
  }

  const handleSubmit = async () => {
    if (!formData.name || !formData.lead) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      await api.departments.createDepartment({
        ...formData,
        members: [formData.lead], // Initially add the lead as a member
      })

      toast({
        title: "Success",
        description: "Department created successfully",
      })

      // Reset form
      setFormData({
        name: "",
        description: "",
        lead: "",
        color: "bg-blue-500",
      })

      onOpenChange(false)
    } catch (error) {
      console.error("Error creating department:", error)
      toast({
        title: "Error",
        description: error.message || "Failed to create department",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[92vh] overflow-hidden bg-white/10 dark:bg-black/20 backdrop-blur-2xl border border-white/30 dark:border-white/10 shadow-2xl rounded-3xl p-0" style={{backdropFilter: 'blur(20px)'}}>
        {/* Hidden title for accessibility */}
        <DialogTitle className="sr-only">Create New Department</DialogTitle>
        
        {/* Scrollable Content Area */}
        <div className="px-7 pt-7 pb-6 overflow-y-auto max-h-[calc(92vh-130px)] scrollbar-thin scrollbar-thumb-white/20 dark:scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/30 dark:hover:scrollbar-thumb-white/20">
          {/* Header Section */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Create New Department</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Add a new department to your workflow management system</p>
          </div>

          <div className="grid gap-6">
            {/* Department Name */}
            <div className="grid gap-2.5">
              <Label htmlFor="name" className="text-sm font-bold text-gray-900 dark:text-white/90 flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-primary shadow-lg shadow-primary/50"></div>
                Department Name <span className="text-red-400 ml-0.5">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Enter department name..."
                value={formData.name}
                onChange={(e) => handleChange("name", e.target.value)}
                className="h-12 px-4 bg-white/10 dark:bg-white/5 border-2 border-white/30 dark:border-white/15 hover:border-white/50 dark:hover:border-white/30 focus:border-primary focus-visible:ring-4 focus-visible:ring-primary/30 rounded-xl transition-all duration-300 text-base font-medium placeholder:text-gray-500 dark:placeholder:text-white/40 text-gray-900 dark:text-white backdrop-blur-xl"
              />
            </div>

            {/* Description */}
            <div className="grid gap-2.5">
              <Label htmlFor="description" className="text-sm font-bold text-gray-900 dark:text-white/90 flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></div>
                Description
              </Label>
              <Textarea
                id="description"
                placeholder="Enter department description..."
                value={formData.description}
                onChange={(e) => handleChange("description", e.target.value)}
                className="min-h-[120px] px-4 py-3 bg-white/10 dark:bg-white/5 border-2 border-white/30 dark:border-white/15 hover:border-white/50 dark:hover:border-white/30 focus:border-green-500 focus-visible:ring-4 focus-visible:ring-green-500/30 rounded-xl transition-all duration-300 text-base font-medium placeholder:text-gray-500 dark:placeholder:text-white/40 text-gray-900 dark:text-white backdrop-blur-xl resize-none"
              />
            </div>

            {/* Department Lead */}
            <div className="grid gap-2.5">
              <Label htmlFor="lead" className="text-sm font-bold text-gray-900 dark:text-white/90 flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-500 shadow-lg shadow-blue-500/50"></div>
                Department Lead <span className="text-red-400 ml-0.5">*</span>
              </Label>
              <Select value={formData.lead} onValueChange={(value) => handleChange("lead", value)}>
                <SelectTrigger 
                  id="lead"
                  className="h-12 px-4 bg-white/10 dark:bg-white/5 border-2 border-white/30 dark:border-white/15 hover:border-white/50 dark:hover:border-white/30 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/30 rounded-xl transition-all duration-300 text-base font-medium text-gray-900 dark:text-white placeholder:text-gray-500 dark:placeholder:text-white/40 backdrop-blur-xl"
                >
                  <SelectValue placeholder="Select department lead...">
                    {formData.lead && users.length > 0 ? (
                      <div className="flex items-center gap-2">
                        <svg className="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span className="font-semibold">
                          {users.find(u => (u._id || u.id) === formData.lead)?.name || "Select department lead..."}
                        </span>
                      </div>
                    ) : null}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="bg-white/10 dark:bg-black/20 backdrop-blur-2xl border border-white/30 dark:border-white/10 rounded-2xl shadow-2xl max-h-64 overflow-y-auto" style={{backdropFilter: 'blur(20px)'}}>
                  {users.length > 0 ? (
                    users.map((user) => (
                      <SelectItem 
                        key={user._id || user.id} 
                        value={user._id || user.id}
                        className="my-1 mx-2 px-3 py-2.5 rounded-lg hover:bg-blue-500/30 dark:hover:bg-blue-500/40 cursor-pointer transition-all duration-200 font-medium text-gray-900 dark:text-white"
                      >
                        <div className="flex items-center gap-2">
                          <svg className="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {user.name}
                        </div>
                      </SelectItem>
                    ))
                  ) : (
                    <div className="px-4 py-3 text-center text-sm text-gray-500 dark:text-gray-400">
                      No users available
                    </div>
                  )}
                </SelectContent>
              </Select>
              {users.length === 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Loading users...</p>
              )}
            </div>

            {/* Department Color */}
            <div className="grid gap-2.5">
              <Label htmlFor="color" className="text-sm font-bold text-gray-900 dark:text-white/90 flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-purple-500 shadow-lg shadow-purple-500/50"></div>
                Department Color
              </Label>
              <div className="flex flex-wrap gap-3 p-4 bg-white/5 dark:bg-white/5 border-2 border-white/20 dark:border-white/10 rounded-xl backdrop-blur-xl">
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-blue-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-blue-500" ? "ring-4 ring-offset-2 ring-blue-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-blue-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-green-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-green-500" ? "ring-4 ring-offset-2 ring-green-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-green-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-amber-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-amber-500" ? "ring-4 ring-offset-2 ring-amber-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-amber-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-red-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-red-500" ? "ring-4 ring-offset-2 ring-red-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-red-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-purple-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-purple-500" ? "ring-4 ring-offset-2 ring-purple-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-purple-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-cyan-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-cyan-500" ? "ring-4 ring-offset-2 ring-cyan-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-cyan-500")}
                />
                <Button
                  type="button"
                  className={`w-10 h-10 rounded-full bg-indigo-500 p-0 hover:scale-110 transition-all duration-300 ${formData.color === "bg-indigo-500" ? "ring-4 ring-offset-2 ring-indigo-500 scale-110" : ""}`}
                  onClick={() => handleColorSelect("bg-indigo-500")}
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Choose a color to represent this department</p>
            </div>
          </div>
        </div>

        {/* Premium Footer */}
        <DialogFooter className="px-7 py-4 border-t border-white/20 dark:border-white/10 bg-gradient-to-t from-white/10 dark:from-black/10 to-transparent backdrop-blur-xl" style={{backdropFilter: 'blur(20px)'}}>
          <div className="flex items-center gap-3 w-full sm:w-auto sm:ml-auto">
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="flex-1 sm:flex-none h-12 px-6 rounded-xl border border-white/30 dark:border-white/15 hover:border-white/50 dark:hover:border-white/30 hover:bg-white/10 dark:hover:bg-white/5 transition-all duration-300 font-semibold text-gray-900 dark:text-white/90"
            >
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </Button>
            <Button 
              type="submit" 
              onClick={handleSubmit} 
              disabled={isLoading}
              className="flex-1 sm:flex-none h-12 px-6 rounded-xl bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 border-2 border-green-400/50 text-white font-bold shadow-lg shadow-green-500/30 hover:shadow-green-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Creating...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Create Department
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
