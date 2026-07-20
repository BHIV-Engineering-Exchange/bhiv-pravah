"use client"

import { useState, useEffect } from "react"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { Badge } from "../ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog"
import { useToast } from "../../hooks/use-toast"
import { useAuth } from "@/context/auth-context"
import { KeyRound, Search, Users, Eye, EyeOff, RefreshCw, Filter, UserCheck, UserX } from "lucide-react"
import { API_URL } from "@/lib/api"

export function PasswordSettings() {
  const { toast } = useToast()
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all") // "all", "existing", "exited"
  
  console.log("🔑 PasswordSettings Component Loaded")
  console.log("- Current User:", currentUser)
  const [showPasswordDialog, setShowPasswordDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingUsers, setIsLoadingUsers] = useState(true)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Fetch users on component mount
  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setIsLoadingUsers(true)
      const token = localStorage.getItem("WorkflowToken")
      
      const response = await fetch(`${API_URL}/admin/users/all`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "x-auth-token": token,
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.status}`)
      }

      const data = await response.json()
      setUsers(data)
    } catch (err) {
      console.error("Error fetching users:", err)
      toast({
        title: "Error",
        description: "Failed to load employees. Please refresh the page.",
        variant: "destructive",
      })
    } finally {
      setIsLoadingUsers(false)
    }
  }

  const handleChangePassword = async () => {
    if (!selectedUser) {
      toast({
        title: "Error",
        description: "No user selected",
        variant: "destructive",
      })
      return
    }

    if (!newPassword || !confirmPassword) {
      toast({
        title: "Validation Error",
        description: "Please enter and confirm the new password",
        variant: "destructive",
      })
      return
    }

    if (newPassword.length < 6) {
      toast({
        title: "Validation Error",
        description: "Password must be at least 6 characters",
        variant: "destructive",
      })
      return
    }

    if (newPassword !== confirmPassword) {
      toast({
        title: "Validation Error",
        description: "Passwords do not match",
        variant: "destructive",
      })
      return
    }

    try {
      setIsLoading(true)
      const token = localStorage.getItem("WorkflowToken")
      
      const response = await fetch(`${API_URL}/admin/users/${selectedUser._id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "x-auth-token": token,
        },
        body: JSON.stringify({
          password: newPassword
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || "Failed to update password")
      }

      setShowPasswordDialog(false)
      setSelectedUser(null)
      setNewPassword("")
      setConfirmPassword("")
      setShowNewPassword(false)
      setShowConfirmPassword(false)

      toast({
        title: "Success",
        description: `Password updated successfully for ${selectedUser.name}`,
      })
    } catch (err) {
      console.error("Error changing password:", err)
      toast({
        title: "Error",
        description: err.message || "Failed to change password",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getInitials = (name) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .substring(0, 2)
  }

  const getRoleBadge = (role) => {
    switch (role) {
      case "Admin":
        return (
          <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-200 dark:bg-purple-900 dark:text-purple-300">
            Admin
          </Badge>
        )
      case "Manager":
        return (
          <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300">
            Manager
          </Badge>
        )
      case "User":
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-300">
            User
          </Badge>
        )
      default:
        return <Badge>{role}</Badge>
    }
  }

  const getStatusBadge = (stillExist) => {
    if (stillExist === 1) {
      return (
        <Badge className="bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-300">
          <UserCheck className="h-3 w-3 mr-1" />
          Active
        </Badge>
      )
    } else {
      return (
        <Badge className="bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-300">
          <UserX className="h-3 w-3 mr-1" />
          Exited
        </Badge>
      )
    }
  }

  const filteredUsers = users.filter((user) => {
    // Search filter
    const matchesSearch = 
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
    
    // Status filter
    let matchesStatus = true
    if (statusFilter === "existing") {
      matchesStatus = user.stillExist === 1
    } else if (statusFilter === "exited") {
      matchesStatus = user.stillExist === 0
    }
    // "all" shows everyone
    
    return matchesSearch && matchesStatus
  })

  console.log("📊 Password Settings Debug:")
  console.log("- Total Users:", users.length)
  console.log("- Status Filter:", statusFilter)
  console.log("- Filtered Users:", filteredUsers.length)
  console.log("- Existing Count:", users.filter(u => u.stillExist === 1).length)
  console.log("- Exited Count:", users.filter(u => u.stillExist === 0).length)

  return (
    <div className="space-y-6">
      {/* Employee Password Management */}
      <Card className="border-l-4 border-l-amber-500">
        <CardHeader className="bg-gradient-to-r from-amber-500/5 to-transparent">
          <div className="flex justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <KeyRound className="h-4 w-4 text-amber-500" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">Employee Password Management</CardTitle>
                <CardDescription className="mt-1">Search and select employee to change password</CardDescription>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchUsers}
              disabled={isLoadingUsers}
              className="flex-shrink-0"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingUsers ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {/* Search Bar */}
          <div className="space-y-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Search employees by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-12 text-base border-2 focus:border-amber-500 dark:focus:border-amber-500"
              />
              {searchTerm && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-2 h-8 w-8 p-0 hover:bg-amber-100 dark:hover:bg-amber-900/30"
                  onClick={() => setSearchTerm("")}
                >
                  ✕
                </Button>
              )}
            </div>

            {/* Status Filter Buttons */}
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-2 mr-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Filter:</span>
              </div>
              <Button
                variant={statusFilter === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter("all")}
                className={statusFilter === "all" ? "bg-amber-500 hover:bg-amber-600 text-white" : "border-2"}
              >
                <Users className="h-4 w-4 mr-2" />
                All Users
                <Badge variant="secondary" className="ml-2 bg-white/20 text-white dark:bg-black/20">
                  {users.length}
                </Badge>
              </Button>
              <Button
                variant={statusFilter === "existing" ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter("existing")}
                className={statusFilter === "existing" ? "bg-green-500 hover:bg-green-600 text-white" : "border-2"}
              >
                <UserCheck className="h-4 w-4 mr-2" />
                Existing
                <Badge variant="secondary" className="ml-2 bg-white/20 text-white dark:bg-black/20">
                  {users.filter(u => u.stillExist === 1).length}
                </Badge>
              </Button>
              <Button
                variant={statusFilter === "exited" ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter("exited")}
                className={statusFilter === "exited" ? "bg-red-500 hover:bg-red-600 text-white" : "border-2"}
              >
                <UserX className="h-4 w-4 mr-2" />
                Exited
                <Badge variant="secondary" className="ml-2 bg-white/20 text-white dark:bg-black/20">
                  {users.filter(u => u.stillExist === 0).length}
                </Badge>
              </Button>
            </div>

            {users.length > 0 && (
              <div className="flex items-center justify-between text-sm">
                <p className="text-muted-foreground">
                  {filteredUsers.length === users.length 
                    ? `Showing all ${users.length} employees`
                    : `Found ${filteredUsers.length} of ${users.length} employees`
                  }
                  {statusFilter !== "all" && (
                    <span className="ml-2 text-amber-600 dark:text-amber-400 font-medium">
                      ({statusFilter === "existing" ? "Existing only" : "Exited only"})
                    </span>
                  )}
                </p>
                {searchTerm && (
                  <p className="text-amber-600 dark:text-amber-400 font-medium">
                    Searching for: "{searchTerm}"
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Employee List */}
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
            {isLoadingUsers ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading employees...</p>
              </div>
            ) : filteredUsers.length > 0 ? (
              filteredUsers.map((user) => (
                <Card
                  key={user._id}
                  className="border-l-4 border-l-amber-300 hover:border-l-amber-500 border-r border-t border-b border-gray-200 dark:border-gray-700 hover:shadow-lg hover:scale-[1.02] transition-all duration-200 cursor-pointer group bg-white dark:bg-gray-800"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedUser(user)
                    setShowPasswordDialog(true)
                  }}
                >
                  <CardContent className="p-5 bg-gradient-to-r from-amber-50/50 to-transparent dark:from-amber-900/10 dark:to-transparent">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <Avatar className="h-14 w-14 flex-shrink-0 ring-2 ring-amber-300 group-hover:ring-amber-500 transition-all duration-200 shadow-md">
                          {user.avatar ? (
                            <AvatarImage src={user.avatar} alt={user.name} />
                          ) : (
                            <AvatarFallback className="bg-gradient-to-br from-amber-100 to-amber-200 dark:from-amber-800 dark:to-amber-900 text-amber-800 dark:text-amber-200 font-bold text-lg group-hover:from-amber-200 group-hover:to-amber-300 dark:group-hover:from-amber-700 dark:group-hover:to-amber-800 transition-colors">
                              {getInitials(user.name)}
                            </AvatarFallback>
                          )}
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-lg truncate text-gray-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                            {user.name}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{user.email}</p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            {getRoleBadge(user.role)}
                            {getStatusBadge(user.stillExist)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="hidden sm:flex flex-col items-end">
                          <span className="text-xs text-gray-500 dark:text-gray-400">Click to</span>
                          <span className="text-xs font-bold text-amber-600 dark:text-amber-400">Change Password</span>
                        </div>
                        <KeyRound className="h-6 w-6 text-amber-500 group-hover:text-amber-600 dark:group-hover:text-amber-400 group-hover:scale-110 transition-all duration-200" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : users.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Users className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-semibold mb-2">No Employees Found</p>
                <p className="text-sm">There are no employees in the system yet.</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchUsers}
                  className="mt-4"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh List
                </Button>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Search className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-semibold mb-2">No Match Found</p>
                <p className="text-sm mb-4">No employees match "{searchTerm}"</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSearchTerm("")}
                  className="bg-amber-50 hover:bg-amber-100 dark:bg-amber-900/20 dark:hover:bg-amber-900/40"
                >
                  Clear Search
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Change Password Dialog with Show/Hide Password */}
      <Dialog 
        open={showPasswordDialog} 
        onOpenChange={(open) => {
          setShowPasswordDialog(open)
          if (!open) {
            setSelectedUser(null)
            setNewPassword("")
            setConfirmPassword("")
            setShowNewPassword(false)
            setShowConfirmPassword(false)
          }
        }}
      >
        <DialogContent className="sm:max-w-[500px] border-l-4 border-l-amber-500 bg-gradient-to-br from-amber-50 to-white dark:from-gray-800 dark:to-gray-900">
          <DialogHeader className="pb-4 border-b border-amber-100 dark:border-amber-900">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg">
                <KeyRound className="h-6 w-6 text-white" />
              </div>
              <div>
                <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-amber-600 to-amber-800 dark:from-amber-400 dark:to-amber-600 bg-clip-text text-transparent">
                  Update Password
                </DialogTitle>
                <DialogDescription className="text-gray-600 dark:text-gray-400 mt-1">
                  {selectedUser && (
                    <>
                      Change password for <strong className="text-gray-900 dark:text-gray-100">{selectedUser.name}</strong>
                    </>
                  )}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>
          
          <div className="grid gap-6 py-6">
            {/* New Password Field */}
            <div className="space-y-2">
              <Label htmlFor="new-password" className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                New Password
              </Label>
              <div className="relative group">
                <Input
                  id="new-password"
                  type={showNewPassword ? "text" : "password"}
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="pr-12 h-12 border-2 border-gray-200 dark:border-gray-700 focus:border-amber-500 dark:focus:border-amber-500 bg-white dark:bg-gray-800 transition-all duration-200"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 h-10 w-10 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-all duration-200"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? (
                    <EyeOff className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-amber-600 dark:text-gray-500 dark:hover:text-amber-400 transition-colors" />
                  )}
                </Button>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className={`w-1.5 h-1.5 rounded-full ${newPassword.length >= 6 ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                <p className={`${newPassword.length >= 6 ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                  Must be at least 6 characters
                </p>
              </div>
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <Label htmlFor="confirm-password" className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                Confirm New Password
              </Label>
              <div className="relative group">
                <Input
                  id="confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Re-enter new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="pr-12 h-12 border-2 border-gray-200 dark:border-gray-700 focus:border-amber-500 dark:focus:border-amber-500 bg-white dark:bg-gray-800 transition-all duration-200"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 h-10 w-10 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-all duration-200"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-amber-600 dark:text-gray-500 dark:hover:text-amber-400 transition-colors" />
                  )}
                </Button>
              </div>
              {confirmPassword && (
                <div className="flex items-center gap-2 text-xs">
                  <div className={`w-1.5 h-1.5 rounded-full ${newPassword === confirmPassword && confirmPassword.length >= 6 ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <p className={`${newPassword === confirmPassword && confirmPassword.length >= 6 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {newPassword === confirmPassword && confirmPassword.length >= 6 ? 'Passwords match!' : 'Passwords must match'}
                  </p>
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="pt-4 border-t border-amber-100 dark:border-amber-900 gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowPasswordDialog(false)
                setSelectedUser(null)
                setNewPassword("")
                setConfirmPassword("")
                setShowNewPassword(false)
                setShowConfirmPassword(false)
              }}
              className="border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 h-11 px-6"
            >
              Cancel
            </Button>
            <Button
              onClick={handleChangePassword}
              disabled={isLoading || !newPassword || !confirmPassword || newPassword !== confirmPassword || newPassword.length < 6}
              className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 h-11 px-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Updating...
                </>
              ) : (
                <>
                  <KeyRound className="mr-2 h-4 w-4" />
                  Update Password
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

