"use client"

import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Eye, EyeOff, Lock, Mail, Sparkles } from "lucide-react"
import { useAuth } from "../context/auth-context" // Import the context

export default function Login() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // Use login from AuthContext
  const { login } = useAuth()

  useEffect(() => {
    const isSystemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    // Force theme detection (optional future use)
    const _ = isSystemDark ? "light" : "dark";
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })

    // Clear error when user types
    if (errors[name]) {
      setErrors({ ...errors, [name]: "" })
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.email) {
      newErrors.email = "Email is required"
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid"
    }

    if (!formData.password) {
      newErrors.password = "Password is required"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
  
    if (validateForm()) {
      setLoading(true)
  
      try {
        await login(formData) // The login function handles navigation automatically
        console.log("Login successful - user data stored in localStorage")
      } catch (error) {
        console.error("Login error:", error)
        setErrors({ password: "Invalid email or password" })
      } finally {
        setLoading(false)
      }
    }
  }
  

  return (
    <div className="h-screen w-full flex items-center justify-center px-4 py-4 relative overflow-hidden bg-background">
      {/* Enhanced Cyber Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-accent/10"></div>
      <div className="absolute inset-0">
        <div className="absolute inset-0 opacity-20" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, hsl(var(--primary) / 0.15) 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }}></div>
      </div>

      {/* Animated Floating Elements */}
      <div className="absolute top-20 left-20 w-32 h-32 bg-primary/20 rounded-full blur-3xl animate-float-cyber"></div>
      <div className="absolute bottom-20 right-20 w-40 h-40 bg-accent/20 rounded-full blur-3xl animate-float-cyber" style={{animationDelay: '2s'}}></div>
      <div className="absolute top-1/2 left-10 w-24 h-24 bg-secondary/15 rounded-full blur-3xl animate-float-cyber" style={{animationDelay: '4s'}}></div>
      <div className="absolute bottom-1/3 right-1/3 w-28 h-28 bg-info/15 rounded-full blur-3xl animate-float-cyber" style={{animationDelay: '1s'}}></div>

      <Card className="w-full max-w-md relative z-10 neo-card animate-scale-in shadow-2xl border-border/50 my-auto">
        <CardHeader className="space-y-1 text-center pb-8">
          {/* Logo with enhanced animation */}
          <div className="mx-auto w-20 h-20 gradient-primary rounded-2xl flex items-center justify-center mb-6 shadow-glow-primary animate-glow-pulse transform hover:scale-110 transition-all duration-300 relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/50 to-transparent rounded-2xl animate-pulse-cyber"></div>
            <Lock className="w-10 h-10 text-primary-foreground relative z-10" />
          </div>
          
          <CardTitle className="text-4xl font-bold text-foreground mb-2 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
            Welcome Back
          </CardTitle>
          <CardDescription className="text-muted-foreground text-base flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            Sign in to your workspace
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <CardContent className="space-y-6 px-8">
            {/* Email Field */}
            <div className="space-y-2 group">
              <Label htmlFor="email" className="text-sm font-medium text-foreground flex items-center gap-2">
                <Mail className="w-4 h-4 text-primary" />
                Email Address
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={loading}
                  className={`pl-4 pr-4 h-12 transition-all duration-300 bg-background/50 backdrop-blur-sm border-border hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 ${
                    errors.email ? "border-destructive focus:border-destructive focus:ring-destructive/20" : ""
                  }`}
                />
              </div>
              {errors.email && (
                <p className="text-sm text-destructive animate-slide-up flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.email}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div className="space-y-2 group">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Lock className="w-4 h-4 text-primary" />
                  Password
                </Label>
                <Link to="/forgot-password" className="text-sm text-primary hover:text-primary/80 transition-colors duration-200 font-medium">
                  Forgot?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  disabled={loading}
                  className={`pl-4 pr-12 h-12 transition-all duration-300 bg-background/50 backdrop-blur-sm border-border hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 ${
                    errors.password ? "border-destructive focus:border-destructive focus:ring-destructive/20" : ""
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  disabled={loading}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-destructive animate-slide-up flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {errors.password}
                </p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4 px-8 pb-8">
            <Button
              type="submit"
              className="w-full h-12 relative overflow-hidden group gradient-primary hover:shadow-glow-primary transition-all duration-300 transform hover:scale-[1.02] text-primary-foreground font-semibold text-base"
              disabled={loading}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700"></div>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Signing In...
                </>
              ) : (
                <>
                  <Lock className="mr-2 h-5 w-5" />
                  Sign In
                </>
              )}
            </Button>

            {/* Google sign-in removed: using email/password only */}

            <div className="text-center">
              <Link
                to="/register"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
              >
                Don't have an account?{" "}
                <span className="text-primary hover:text-primary/80 font-semibold underline-offset-4 hover:underline">
                  Create one now
                </span>
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}