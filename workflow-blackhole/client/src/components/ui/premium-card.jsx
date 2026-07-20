import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

/**
 * Premium KPI Card Component
 * Follows the design system with gradient, glow effects, and smooth animations
 */
export function PremiumKPICard({ 
  title, 
  value, 
  icon: Icon, 
  variant = "primary",
  className,
  ...props 
}) {
  const variants = {
    primary: {
      border: "hover:border-primary",
      gradient: "gradient-primary",
      glow: "shadow-glow-primary"
    },
    secondary: {
      border: "hover:border-secondary",
      gradient: "gradient-secondary",
      glow: "shadow-glow-secondary"
    },
    accent: {
      border: "hover:border-accent",
      gradient: "gradient-accent",
      glow: "shadow-glow-accent"
    },
    success: {
      border: "hover:border-success",
      gradient: "gradient-primary", // Success uses primary gradient
      glow: "shadow-glow-primary"
    }
  }

  const variantStyles = variants[variant] || variants.primary

  return (
    <Card 
      className={cn(
        "border-l-4 border-transparent",
        variantStyles.border,
        "bg-gradient-to-br from-card to-card/50",
        "shadow-lg hover:shadow-xl hover:-translate-y-1",
        "transition-all duration-300",
        className
      )}
      {...props}
    >
      <CardContent className="pt-6">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {title}
            </p>
            <p className="text-3xl font-heading font-bold text-foreground mt-2">
              {value}
            </p>
          </div>
          {Icon && (
            <div className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center shadow-lg",
              variantStyles.gradient,
              variantStyles.glow
            )}>
              <Icon className={cn(
                "h-6 w-6",
                variant === "primary" && "text-primary-foreground",
                variant === "secondary" && "text-secondary-foreground",
                variant === "accent" && "text-accent-foreground",
                variant === "success" && "text-success-foreground"
              )} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Premium Section Card
 * Main content card with border accent
 */
export function PremiumSectionCard({ 
  children, 
  className,
  accent = "primary",
  ...props 
}) {
  const accents = {
    primary: "hover:border-primary",
    secondary: "hover:border-secondary",
    accent: "hover:border-accent"
  }

  return (
    <Card 
      className={cn(
        "border-l-4 border-transparent",
        accents[accent],
        "bg-gradient-to-br from-card to-card/50",
        "shadow-xl hover:shadow-2xl hover:-translate-y-1",
        "transition-all duration-300",
        className
      )}
      {...props}
    >
      {children}
    </Card>
  )
}

/**
 * Premium Grid Card
 * For items in grids (departments, projects, etc.)
 */
export function PremiumGridCard({ 
  children, 
  className,
  ...props 
}) {
  return (
    <Card 
      className={cn(
        "border-l-4 border-transparent hover:border-primary",
        "bg-gradient-to-br from-card to-card/50",
        "shadow-lg hover:shadow-xl hover:-translate-y-1",
        "transition-all duration-300",
        className
      )}
      {...props}
    >
      {children}
    </Card>
  )
}

/**
 * Premium Page Header
 * Consistent page title styling
 */
export function PremiumPageHeader({ title, subtitle, actions, className }) {
  return (
    <div className={cn(
      "flex flex-col md:flex-row justify-between items-start md:items-center gap-4",
      className
    )}>
      <div>
        <h1 className="text-3xl font-heading font-bold tracking-tight text-foreground">
          {title}
        </h1>
        {subtitle && (
          <p className="text-muted-foreground mt-1">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="flex gap-3">
          {actions}
        </div>
      )}
    </div>
  )
}
