"use client"

import { useState } from "react"
import { Button } from "../ui/button"
import { Switch } from "../ui/switch"
import { Label } from "../ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { RadioGroup, RadioGroupItem } from "../ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Bell, BellRing, Mail, MessageSquare, Sparkles, FileText, Clock, Zap } from "lucide-react"
import { useToast } from "../../hooks/use-toast"

export function NotificationSettings() {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const [settings, setSettings] = useState({
    emailNotifications: true,
    taskAssigned: true,
    taskUpdated: true,
    taskCompleted: true,
    commentAdded: true,
    aiSuggestions: true,
    dailyDigest: false,
    weeklyReport: true,
    notificationMethod: "email-and-app",
    notificationFrequency: "immediate",
  })

  const handleToggle = (field) => {
    setSettings((prev) => ({ ...prev, [field]: !prev[field] }))
  }

  const handleChange = (field, value) => {
    setSettings((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))
      
      toast({
        title: "Success",
        description: "Notification settings updated successfully!",
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error?.message || "Failed to update notification settings",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Main Email Toggle Card */}
        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="bg-gradient-to-r from-purple-500/5 to-transparent">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <Mail className="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <CardTitle className="text-lg">Email Notifications</CardTitle>
                  <CardDescription>Receive email notifications for important updates</CardDescription>
                </div>
              </div>
              <Switch
                id="email-notifications"
                checked={settings.emailNotifications}
                onCheckedChange={() => handleToggle("emailNotifications")}
                className="data-[state=checked]:bg-purple-500"
              />
            </div>
          </CardHeader>
        </Card>

        {/* Notification Categories Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 1: Task Notifications */}
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="bg-gradient-to-r from-blue-500/5 to-transparent pb-3">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <BellRing className="h-4 w-4 text-blue-500" />
                </div>
                <div>
                  <CardTitle className="text-base">Task Notifications</CardTitle>
                  <CardDescription className="text-xs">Get notified about task activities</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <Zap className="h-4 w-4 text-blue-500/60" />
                  <Label htmlFor="task-assigned" className="cursor-pointer text-sm">
                    Task assigned to me
                  </Label>
                </div>
                <Switch
                  id="task-assigned"
                  checked={settings.taskAssigned}
                  onCheckedChange={() => handleToggle("taskAssigned")}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <Bell className="h-4 w-4 text-blue-500/60" />
                  <Label htmlFor="task-updated" className="cursor-pointer text-sm">
                    Task updates
                  </Label>
                </div>
                <Switch
                  id="task-updated"
                  checked={settings.taskUpdated}
                  onCheckedChange={() => handleToggle("taskUpdated")}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-blue-500/60" />
                  <Label htmlFor="task-completed" className="cursor-pointer text-sm">
                    Task completed
                  </Label>
                </div>
                <Switch
                  id="task-completed"
                  checked={settings.taskCompleted}
                  onCheckedChange={() => handleToggle("taskCompleted")}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-blue-500/60" />
                  <Label htmlFor="comment-added" className="cursor-pointer text-sm">
                    Comments on my tasks
                  </Label>
                </div>
                <Switch
                  id="comment-added"
                  checked={settings.commentAdded}
                  onCheckedChange={() => handleToggle("commentAdded")}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
            </CardContent>
          </Card>

          {/* Card 2: AI & Reports */}
          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="bg-gradient-to-r from-green-500/5 to-transparent pb-3">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-green-500" />
                </div>
                <div>
                  <CardTitle className="text-base">AI & Reports</CardTitle>
                  <CardDescription className="text-xs">Insights and performance updates</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-green-500/60" />
                  <Label htmlFor="ai-suggestions" className="cursor-pointer text-sm">
                    AI optimization suggestions
                  </Label>
                </div>
                <Switch
                  id="ai-suggestions"
                  checked={settings.aiSuggestions}
                  onCheckedChange={() => handleToggle("aiSuggestions")}
                  className="data-[state=checked]:bg-green-500"
                />
              </div>
              
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-green-500/60" />
                  <Label htmlFor="daily-digest" className="cursor-pointer text-sm">
                    Daily activity digest
                  </Label>
                </div>
                <Switch
                  id="daily-digest"
                  checked={settings.dailyDigest}
                  onCheckedChange={() => handleToggle("dailyDigest")}
                  className="data-[state=checked]:bg-green-500"
                />
              </div>
              
              <div className="flex items-center justify-between py-2 hover:bg-muted/50 px-3 rounded-lg transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-green-500/60" />
                  <Label htmlFor="weekly-report" className="cursor-pointer text-sm">
                    Weekly performance report
                  </Label>
                </div>
                <Switch
                  id="weekly-report"
                  checked={settings.weeklyReport}
                  onCheckedChange={() => handleToggle("weeklyReport")}
                  className="data-[state=checked]:bg-green-500"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Notification Preferences Card */}
        <Card className="border-l-4 border-l-amber-500">
          <CardHeader className="bg-gradient-to-r from-amber-500/5 to-transparent">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Bell className="h-4 w-4 text-amber-500" />
              </div>
              <div>
                <CardTitle className="text-base">Notification Preferences</CardTitle>
                <CardDescription className="text-xs">Customize how and when you receive notifications</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Notification Method */}
              <div className="space-y-3">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <Mail className="h-4 w-4 text-amber-500" />
                  Notification Method
                </Label>
                <RadioGroup
                  value={settings.notificationMethod}
                  onValueChange={(value) => handleChange("notificationMethod", value)}
                  className="space-y-2"
                >
                  <div className="flex items-center space-x-2 hover:bg-muted/50 p-2 rounded-lg transition-colors">
                    <RadioGroupItem value="email-only" id="email-only" className="border-amber-500 text-amber-500" />
                    <Label htmlFor="email-only" className="cursor-pointer font-normal">Email only</Label>
                  </div>
                  <div className="flex items-center space-x-2 hover:bg-muted/50 p-2 rounded-lg transition-colors">
                    <RadioGroupItem value="app-only" id="app-only" className="border-amber-500 text-amber-500" />
                    <Label htmlFor="app-only" className="cursor-pointer font-normal">In-app only</Label>
                  </div>
                  <div className="flex items-center space-x-2 hover:bg-muted/50 p-2 rounded-lg transition-colors">
                    <RadioGroupItem value="email-and-app" id="email-and-app" className="border-amber-500 text-amber-500" />
                    <Label htmlFor="email-and-app" className="cursor-pointer font-normal">Email and in-app</Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Notification Frequency */}
              <div className="space-y-3">
                <Label htmlFor="notification-frequency" className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-500" />
                  Notification Frequency
                </Label>
                <Select
                  value={settings.notificationFrequency}
                  onValueChange={(value) => handleChange("notificationFrequency", value)}
                >
                  <SelectTrigger id="notification-frequency" className="border-amber-500/30 focus:border-amber-500 focus:ring-amber-500">
                    <SelectValue placeholder="Select frequency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="immediate">
                      <div className="flex items-center gap-2">
                        <Zap className="h-3 w-3" />
                        <span>Immediate</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="hourly">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        <span>Hourly digest</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="daily">
                      <div className="flex items-center gap-2">
                        <FileText className="h-3 w-3" />
                        <span>Daily digest</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Choose how often you want to receive notifications
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <Button 
            type="submit" 
            disabled={isLoading}
            className="min-w-[140px] bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
            size="lg"
          >
            {isLoading ? "Saving..." : "Save Preferences"}
          </Button>
        </div>
      </form>
    </div>
  )
}
