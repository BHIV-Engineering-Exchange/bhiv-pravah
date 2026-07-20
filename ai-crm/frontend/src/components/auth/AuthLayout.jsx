import React from 'react';
import { Bot } from 'lucide-react';

const AuthLayout = ({ children, title, subtitle }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left side - Branding */}
        <div className="hidden lg:block">
          <div className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-16 h-16 rounded-2xl gradient-primary shadow-glow-primary flex items-center justify-center">
                <Bot className="w-10 h-10 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-heading font-bold tracking-tight">SETU</h1>
                <p className="text-muted-foreground">CRM System</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <h2 className="text-4xl font-heading font-bold tracking-tight">
                {title || 'Welcome Back'}
              </h2>
              <p className="text-lg text-muted-foreground">
                {subtitle || 'Manage your logistics with AI-powered automation'}
              </p>
            </div>

            <div className="space-y-4 pt-8">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
                  <span className="text-2xl">🚚</span>
                </div>
                <div>
                  <h3 className="font-semibold">Smart Logistics</h3>
                  <p className="text-sm text-muted-foreground">Automated order processing</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl gradient-secondary flex items-center justify-center">
                  <span className="text-2xl">AI</span>
                </div>
                <div>
                  <h3 className="font-semibold">Real-time Analytics</h3>
                  <p className="text-sm text-muted-foreground">Track everything in real-time</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl gradient-accent flex items-center justify-center">
                  <span className="text-2xl">🤖</span>
                </div>
                <div>
                  <h3 className="font-semibold">AI Automation</h3>
                  <p className="text-sm text-muted-foreground">Let AI handle the heavy lifting</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Auth Form */}
        <div className="w-full">
          <div className="bg-card shadow-xl rounded-2xl border border-border p-8 sm:p-10">
            {/* Mobile Logo */}
            <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-xl gradient-primary shadow-glow-primary flex items-center justify-center">
                <Bot className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-heading font-bold tracking-tight">SETU</h1>
                <p className="text-sm text-muted-foreground">CRM System</p>
              </div>
            </div>

            {children}
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-muted-foreground mt-6">
            © 2025 SETU. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
