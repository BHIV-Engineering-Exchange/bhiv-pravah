"use client"

import { useState, useEffect } from "react"
import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Label } from "../ui/label"
import { Textarea } from "../ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { api } from "../../lib/api"
import { useToast } from "../../hooks/use-toast"
import { useAuth } from "@/context/auth-context"
import { User } from "lucide-react"

export function ProfileSettings() {
  const { toast } = useToast()
  const { user } = useAuth() // Get user from auth context
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    bio: "",
    avatar: "",
  })
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [userId, setUserId] = useState(null)

  // Set initial form data when user is available
  useEffect(() => {
    if (user) {
      setUserId(user.id)
      setFormData({
        name: user.name || "",
        email: user.email || "",
        bio: user.bio || "",
        avatar: user.avatar || "/placeholder.svg",
      })
    }
  }, [user])

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmitProfile = async (e) => {
    e.preventDefault()
    setIsLoadingProfile(true)

    try {
      // Update user profile
      await api.users.updateUser(userId, {
        name: formData.name,
        email: formData.email,
        bio: formData.bio,
      })

      toast({
        title: "Success",
        description: "Profile updated successfully!",
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message || "Failed to update profile",
      })
    } finally {
      setIsLoadingProfile(false)
    }
  }

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0]
    if (file) {
      // In a real implementation, you would upload the file to your server
      // and get back a URL. For now, we'll use a placeholder
      const reader = new FileReader()
      reader.onloadend = () => {
        setFormData((prev) => ({ ...prev, avatar: reader.result }))
      }
      reader.readAsDataURL(file)
    }
  }

  // Show loading state if user data is not yet available
  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">

      {/* 3 Separate Cards Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Card 1: Avatar Section */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="bg-gradient-to-r from-blue-500/5 to-transparent">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <User className="h-4 w-4 text-blue-500" />
              </div>
              <div>
                <CardTitle className="text-base">Profile Picture</CardTitle>
                <CardDescription className="text-xs">Update your avatar</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4">
              <Avatar className="h-32 w-32 ring-2 ring-blue-500/20">
                <AvatarImage src={formData.avatar} alt="Profile" />
                <AvatarFallback className="bg-blue-500/10 text-blue-600 dark:text-blue-400 text-3xl font-semibold">
                  {formData.name ? formData.name[0].toUpperCase() : "U"}
                </AvatarFallback>
              </Avatar>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                type="button"
                as="label"
              >
                Change Avatar
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Profile Information */}
        <Card className="border-l-4 border-l-green-500 lg:col-span-2">
          <CardHeader className="bg-gradient-to-r from-green-500/5 to-transparent">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                <User className="h-4 w-4 text-green-500" />
              </div>
              <div>
                <CardTitle className="text-base">Profile Information</CardTitle>
                <CardDescription className="text-xs">Update your personal details</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmitProfile} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    placeholder="your.email@example.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  value={formData.bio}
                  onChange={(e) => handleChange("bio", e.target.value)}
                  className="min-h-[80px] resize-none"
                  placeholder="Tell us a little about yourself..."
                />
                <p className="text-xs text-muted-foreground">
                  Brief description for your profile. Max 200 characters.
                </p>
              </div>

              <div className="flex justify-end pt-4 border-t">
                <Button type="submit" disabled={isLoadingProfile} className="min-w-[120px]">
                  {isLoadingProfile ? "Saving..." : "Save Profile"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}