# Complete Workflow Platform Design System - Single Prompt

Use this prompt to replicate the exact design system, styling, and visual language for your HR Management Platform. Copy and paste this entire prompt to maintain consistency across both projects.

---

## 🎨 DESIGN SYSTEM SPECIFICATION

### **Core Design Philosophy**
Create a premium, modern SaaS platform with:
- **Glassmorphism effects** (frosted glass aesthetic with backdrop blur)
- **Neomorphism elements** (soft, extruded UI components with depth)
- **Smooth animations** (micro-interactions with easing functions)
- **Dark mode support** with true dark (#121212) background
- **Professional color palette** with vibrant accent colors
- **Responsive and accessible** UI components

---

## 📦 TECHNOLOGY STACK

```json
{
  "framework": "React + Vite",
  "styling": "Tailwind CSS v3+",
  "components": "shadcn/ui (Radix UI primitives)",
  "animations": "Framer Motion + Tailwind Animate",
  "icons": "Lucide React",
  "fonts": "Inter (body), Space Grotesk (headings)"
}
```

---

## 🎨 COLOR PALETTE (HSL Format)

### **Light Mode Colors**
```css
--background: 220 17% 98%;           /* Off-white background */
--foreground: 222 47% 11%;           /* Dark text */
--card: 0 0% 100%;                   /* Pure white cards */
--primary: 160 84% 39%;              /* Emerald green */
--secondary: 262 83% 58%;            /* Purple */
--accent: 38 92% 50%;                /* Orange/amber */
--muted: 220 17% 96%;                /* Light gray */
--border: 220 13% 91%;               /* Subtle border */
--info: 217 91% 60%;                 /* Blue */
--success: 160 84% 39%;              /* Green (same as primary) */
--warning: 38 92% 50%;               /* Amber (same as accent) */
--destructive: 0 84% 60%;            /* Red */
```

### **Dark Mode Colors**
```css
--background: 0 0% 7%;               /* True dark gray #121212 */
--foreground: 0 0% 100%;             /* White text */
--card: 0 0% 12%;                    /* Elevated dark surface */
--primary: 160 84% 45%;              /* Brighter emerald */
--secondary: 262 83% 63%;            /* Brighter purple */
--accent: 38 92% 55%;                /* Brighter amber */
--muted: 0 0% 12%;                   /* Muted surface */
--border: 0 0% 18%;                  /* Dark border */
```

### **Gradients**
```css
--gradient-primary: linear-gradient(135deg, hsl(160 84% 39%) 0%, hsl(160 84% 49%) 100%);
--gradient-secondary: linear-gradient(135deg, hsl(262 83% 58%) 0%, hsl(262 83% 68%) 100%);
--gradient-accent: linear-gradient(135deg, hsl(38 92% 50%) 0%, hsl(38 92% 60%) 100%);
--gradient-card: linear-gradient(135deg, hsl(0 0% 100%) 0%, hsl(220 17% 98%) 100%);
```

### **Glow Shadows**
```css
--shadow-glow-primary: 0 0 30px -5px hsl(160 84% 39% / 0.3);
--shadow-glow-secondary: 0 0 30px -5px hsl(262 83% 58% / 0.3);
--shadow-glow-accent: 0 0 30px -5px hsl(38 92% 50% / 0.3);
```

### **Neomorphic Shadows (Light Mode)**
```css
--neo-shadow-light: 8px 8px 16px hsl(220 13% 85%), -8px -8px 16px hsl(0 0% 100%);
--neo-shadow-inset: inset 4px 4px 8px hsl(220 13% 85%), inset -4px -4px 8px hsl(0 0% 100%);
--neo-shadow-hover: 12px 12px 24px hsl(220 13% 80%), -12px -12px 24px hsl(0 0% 100%);
```

### **Neomorphic Shadows (Dark Mode)**
```css
--neo-shadow-light: 10px 10px 20px hsl(0 0% 3%), -10px -10px 20px hsl(0 0% 15%);
--neo-shadow-inset: inset 6px 6px 12px hsl(0 0% 3%), inset -6px -6px 12px hsl(0 0% 15%);
--neo-shadow-hover: 15px 15px 30px hsl(0 0% 2%), -15px -15px 30px hsl(0 0% 18%);
```

---

## 🔤 TYPOGRAPHY

```javascript
fontFamily: {
  sans: ['Inter', 'sans-serif'],           // Body text, UI elements
  heading: ['Space Grotesk', 'sans-serif'], // Headings, titles
}
```

**Font Import (Add to index.html or CSS)**:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Typography Scale**:
- Headings: `Space Grotesk`, `font-weight: 600-700`, `letter-spacing: -0.025em`
- Body: `Inter`, `font-weight: 400-500`
- UI Elements: `Inter`, `font-weight: 500-600`

---

## 🎯 COMPONENT STYLING PATTERNS

### **1. Buttons**
```javascript
// Primary Button
className="inline-flex items-center justify-center gap-2 rounded-xl h-11 px-6 text-sm font-bold
  bg-gradient-to-r from-primary to-primary/90 text-white 
  hover:shadow-xl hover:shadow-primary/30 hover:scale-105 
  active:scale-95 transition-all duration-300 
  disabled:opacity-50 disabled:cursor-not-allowed"

// Secondary Button
className="rounded-xl h-11 px-6 text-sm font-bold
  bg-secondary text-white 
  hover:shadow-xl hover:shadow-secondary/30 hover:scale-105 
  active:scale-95 transition-all duration-300"

// Outline Button
className="rounded-xl h-11 px-6 text-sm font-semibold
  border-2 border-border bg-background 
  hover:bg-accent hover:text-accent-foreground hover:border-accent/50 
  hover:scale-105 active:scale-95 transition-all duration-300"

// Ghost Button
className="rounded-xl h-11 px-6 text-sm font-medium
  hover:bg-accent hover:text-accent-foreground 
  hover:scale-105 active:scale-95 transition-all duration-300"
```

### **2. Cards (Neomorphic Style)**
```javascript
// Base Card (applies .neo-card class)
className="rounded-2xl bg-card text-card-foreground 
  shadow-[8px_8px_16px_hsl(220_13%_85%),-8px_-8px_16px_hsl(0_0%_100%)]
  dark:shadow-[10px_10px_20px_hsl(0_0%_3%),-10px_-10px_20px_hsl(0_0%_15%)]
  transition-all duration-400 hover:scale-[1.02]
  border border-border/30"

// Card with Gradient Background
className="rounded-2xl bg-gradient-to-br from-card to-card/50 
  shadow-xl border border-border/50 transition-all duration-300"

// Glassmorphic Card
className="rounded-2xl backdrop-blur-xl bg-white/95 dark:bg-gray-900/95 
  border-2 border-gray-300/50 dark:border-gray-600/50 
  shadow-2xl transition-all duration-300"
```

### **3. Inputs**
```javascript
className="flex h-12 w-full rounded-xl border-2 border-border 
  bg-background px-4 py-3 text-base font-medium 
  transition-all duration-300 
  focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
  placeholder:text-muted-foreground 
  disabled:cursor-not-allowed disabled:opacity-50"
```

### **4. Badges**
```javascript
// Status Badge
className="inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold 
  border bg-primary/10 text-primary border-primary/20"

// Success Badge
className="bg-success/10 text-success border-success/20"

// Warning Badge
className="bg-warning/10 text-warning border-warning/20"

// Destructive Badge
className="bg-destructive/10 text-destructive border-destructive/20"
```

### **5. Dialogs/Modals**
```javascript
// Dialog Overlay
className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm 
  data-[state=open]:animate-in data-[state=closed]:animate-out 
  data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"

// Dialog Content
className="fixed left-[50%] top-[50%] z-50 w-full max-w-lg 
  translate-x-[-50%] translate-y-[-50%] 
  rounded-2xl border-2 border-border bg-card p-6 shadow-2xl 
  duration-200 
  data-[state=open]:animate-in data-[state=closed]:animate-out 
  data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 
  data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 
  data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] 
  data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]"

// Dialog Header with Gradient
className="pb-6 border-b-2 border-purple-200 dark:border-purple-900/50 
  bg-gradient-to-r from-purple-50 via-purple-50/50 to-transparent 
  dark:from-purple-950/20 dark:via-purple-950/10 dark:to-transparent 
  -mx-6 -mt-6 px-6 pt-6 mb-4 rounded-t-lg"
```

### **6. Dropdowns/Popovers (Glassmorphic)**
```javascript
className="z-50 min-w-[8rem] overflow-hidden 
  rounded-lg border-2 border-gray-300/50 dark:border-gray-600/50 
  bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl 
  p-1.5 text-gray-900 dark:text-gray-100 shadow-2xl 
  data-[state=open]:animate-in data-[state=closed]:animate-out 
  data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 
  data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
```

### **7. Data Tables**
```javascript
// Table Container
className="rounded-xl border border-border overflow-hidden 
  shadow-lg bg-card"

// Table Header
className="bg-muted/50 border-b border-border"

// Table Row
className="border-b border-border/50 
  hover:bg-muted/30 transition-colors duration-200"
```

### **8. Status Indicators**
```javascript
// Online/Active
className="h-2 w-2 rounded-full bg-success animate-pulse"

// Offline/Inactive
className="h-2 w-2 rounded-full bg-muted-foreground"

// Warning State
className="h-2 w-2 rounded-full bg-warning animate-pulse"

// Error State
className="h-2 w-2 rounded-full bg-destructive animate-pulse"
```

---

## 🎬 ANIMATIONS & TRANSITIONS

### **Tailwind Animation Config**
```javascript
// Add to tailwind.config.js
keyframes: {
  'fade-in': {
    from: { opacity: '0', transform: 'translateY(10px)' },
    to: { opacity: '1', transform: 'translateY(0)' }
  },
  'fade-up': {
    from: { opacity: '0', transform: 'translateY(20px)' },
    to: { opacity: '1', transform: 'translateY(0)' }
  },
  'scale-in': {
    from: { opacity: '0', transform: 'scale(0.95)' },
    to: { opacity: '1', transform: 'scale(1)' }
  },
  'slide-in-right': {
    from: { transform: 'translateX(100%)' },
    to: { transform: 'translateX(0)' }
  },
  'pulse-slow': {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.7' }
  }
},
animation: {
  'fade-in': 'fade-in 0.5s ease-out',
  'fade-up': 'fade-up 0.5s ease-out',
  'scale-in': 'scale-in 0.2s ease-out',
  'slide-in-right': 'slide-in-right 0.3s ease-out',
  'pulse-slow': 'pulse-slow 3s ease-in-out infinite'
}
```

### **Transition Timing Functions**
```javascript
transitionTimingFunction: {
  'neo': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  'cyber': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
}
```

### **Common Animation Classes**
```javascript
// Fade in on mount
className="animate-fade-in"

// Scale in on mount
className="animate-scale-in"

// Hover scale effect
className="transition-transform hover:scale-105 active:scale-95"

// Smooth color transition
className="transition-colors duration-300"

// All properties transition
className="transition-all duration-300"
```

---

## 🎨 GLASSMORPHISM PATTERNS

### **Glassmorphic Background**
```javascript
className="backdrop-blur-xl bg-white/95 dark:bg-gray-900/95 
  border-2 border-gray-300/50 dark:border-gray-600/50 
  shadow-2xl"
```

### **Glassmorphic Card Overlay**
```javascript
className="absolute inset-0 rounded-2xl 
  bg-gradient-to-br from-white/10 to-transparent 
  backdrop-blur-md border border-white/20"
```

### **Frosted Header**
```javascript
className="fixed top-0 left-0 right-0 z-50 h-18
  backdrop-blur-xl bg-background/80 
  border-b border-border/50 
  shadow-lg"
```

---

## 📐 SPACING & SIZING

```javascript
// Border Radius
borderRadius: {
  lg: '0.75rem',    // 12px - large cards, modals
  md: '0.625rem',   // 10px - medium elements
  sm: '0.5rem',     // 8px - small elements
  xl: '1rem',       // 16px - buttons, inputs
  '2xl': '1.5rem',  // 24px - cards
}

// Common Heights
h-11  // 44px - buttons, inputs (default)
h-12  // 48px - larger inputs
h-14  // 56px - large buttons
h-18  // 72px - header height

// Padding Scale
p-6   // 24px - card padding
p-4   // 16px - compact padding
p-8   // 32px - spacious padding
```

---

## 🎯 LAYOUT PATTERNS

### **Dashboard Grid**
```javascript
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
```

### **Stat Cards Row**
```javascript
className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
```

### **Main Content Container**
```javascript
className="container mx-auto px-4 py-8 max-w-7xl"
```

### **Sidebar Layout**
```javascript
// Sidebar
className="fixed left-0 top-18 h-[calc(100vh-4.5rem)] w-64 
  border-r border-border bg-sidebar 
  overflow-y-auto scrollbar-thin"

// Main Content (with sidebar offset)
className="ml-64 pt-18 min-h-screen"
```

### **Responsive Stack**
```javascript
className="flex flex-col lg:flex-row gap-6"
```

---

## 🖼️ SCROLLBAR STYLING

```css
/* Thin custom scrollbar */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: hsl(var(--border)) transparent;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: hsl(var(--border));
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--muted-foreground));
}
```

---

## 🎨 GRADIENT BACKGROUNDS FOR SECTIONS

```javascript
// Primary gradient background
className="bg-gradient-to-br from-primary/10 via-primary/5 to-transparent"

// Accent gradient
className="bg-gradient-to-r from-accent/10 to-transparent"

// Card gradient overlay
className="bg-gradient-to-br from-card to-card/50"

// Multi-color gradient
className="bg-gradient-to-r from-purple-100 via-purple-50 to-blue-100 
  dark:from-purple-950/30 dark:via-purple-950/20 dark:to-blue-950/30"
```

---

## 🔔 NOTIFICATION/TOAST STYLING

```javascript
// Success Toast
className="rounded-xl border-2 border-success/50 bg-success/10 p-4 
  shadow-lg backdrop-blur-sm"

// Error Toast
className="rounded-xl border-2 border-destructive/50 bg-destructive/10 p-4 
  shadow-lg backdrop-blur-sm"

// Info Toast
className="rounded-xl border-2 border-info/50 bg-info/10 p-4 
  shadow-lg backdrop-blur-sm"
```

---

## 🎯 ACCESSIBILITY & FOCUS STATES

```javascript
// Focus ring (all interactive elements)
focus-visible:outline-none 
focus-visible:ring-2 
focus-visible:ring-ring 
focus-visible:ring-offset-2

// Disabled state
disabled:pointer-events-none 
disabled:opacity-50 
disabled:cursor-not-allowed

// High contrast for text
text-foreground 
dark:text-foreground
```

---

## 📱 RESPONSIVE BREAKPOINTS

```javascript
// Mobile first approach
sm: '640px'   // Small devices
md: '768px'   // Tablets
lg: '1024px'  // Laptops
xl: '1280px'  // Desktops
2xl: '1400px' // Large screens
```

**Usage Pattern**:
```javascript
className="text-sm md:text-base lg:text-lg
  grid-cols-1 md:grid-cols-2 lg:grid-cols-3
  p-4 md:p-6 lg:p-8"
```

---

## 🎨 ICON PATTERNS (Lucide React)

```javascript
import { Plus, Edit, Trash, Check, X, AlertCircle } from 'lucide-react'

// Standard icon size
<Plus className="h-4 w-4" />

// Large icon (in buttons)
<Plus className="h-5 w-5" />

// Icon with color
<Check className="h-4 w-4 text-success" />

// Animated icon
<Loader2 className="h-4 w-4 animate-spin" />
```

---

## 🎯 COMMON UI PATTERNS

### **Empty State**
```javascript
<div className="flex flex-col items-center justify-center py-12 text-center">
  <div className="rounded-full bg-muted p-6 mb-4">
    <Icon className="h-8 w-8 text-muted-foreground" />
  </div>
  <h3 className="text-lg font-semibold mb-2">No data found</h3>
  <p className="text-sm text-muted-foreground max-w-sm">
    Get started by creating your first item.
  </p>
  <Button className="mt-6">
    <Plus className="h-4 w-4 mr-2" />
    Create New
  </Button>
</div>
```

### **Loading Skeleton**
```javascript
<div className="space-y-4">
  <div className="h-12 bg-muted rounded-xl animate-pulse" />
  <div className="h-24 bg-muted rounded-xl animate-pulse" />
  <div className="h-16 bg-muted rounded-xl animate-pulse" />
</div>
```

### **Avatar with Status**
```javascript
<div className="relative">
  <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary to-primary/70 
    flex items-center justify-center text-white font-bold">
    JD
  </div>
  <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-success 
    border-2 border-background animate-pulse" />
</div>
```

### **Stat Card**
```javascript
<Card className="neo-card">
  <CardHeader className="flex flex-row items-center justify-between pb-2">
    <CardTitle className="text-sm font-medium text-muted-foreground">
      Total Users
    </CardTitle>
    <Users className="h-4 w-4 text-muted-foreground" />
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold">1,234</div>
    <p className="text-xs text-muted-foreground mt-2">
      <span className="text-success font-semibold">+12%</span> from last month
    </p>
  </CardContent>
</Card>
```

---

## 🚀 IMPLEMENTATION CHECKLIST

When creating your HR Management Platform, ensure:

- [ ] Install dependencies: `tailwindcss`, `tailwindcss-animate`, `tailwind-scrollbar`, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`
- [ ] Copy the entire CSS variables from `:root` and `.dark` to your `index.css`
- [ ] Add custom animations and keyframes to `index.css`
- [ ] Configure Tailwind with extended colors, shadows, gradients, animations
- [ ] Import Google Fonts: Inter + Space Grotesk
- [ ] Create reusable component variants using `class-variance-authority`
- [ ] Use `cn()` utility function for className merging (from `tailwind-merge` + `clsx`)
- [ ] Implement dark mode toggle using `class` strategy
- [ ] Add `.neo-card` custom class for neomorphic shadows
- [ ] Use `backdrop-blur-xl` for glassmorphism effects
- [ ] Apply consistent spacing (p-6 for cards, gap-6 for grids)
- [ ] Add hover states with `hover:scale-105` and `active:scale-95`
- [ ] Include loading states with `animate-pulse` or `Loader2` icon
- [ ] Implement responsive breakpoints (mobile-first)
- [ ] Use semantic color variables (`primary`, `success`, `destructive`)
- [ ] Add focus states for accessibility

---

## 🌌 TRI-THEME UNIVERSE SYSTEM (Light + Dark + Universe Modern)

### **Universe Modern Theme Colors**
```css
/* Universe Modern - Cosmic/Cyberpunk Aesthetic */
--background: 230 35% 7%;              /* Deep space blue-black */
--foreground: 210 100% 95%;            /* Bright white-blue */
--card: 230 30% 10%;                   /* Elevated cosmic surface */
--card-accent: 230 25% 15%;            /* Lighter card variation */
--primary: 280 100% 70%;               /* Neon purple/magenta */
--secondary: 180 100% 50%;             /* Cyan electric */
--accent: 320 100% 60%;                /* Hot pink/magenta */
--tertiary: 160 100% 50%;              /* Neon green */
--muted: 230 20% 20%;                  /* Muted cosmic */
--border: 230 30% 18%;                 /* Subtle glow border */
--glow-primary: 0 0 40px hsl(280 100% 70% / 0.5);
--glow-secondary: 0 0 40px hsl(180 100% 50% / 0.5);
--glow-accent: 0 0 40px hsl(320 100% 60% / 0.5);
--gradient-cosmic: linear-gradient(135deg, hsl(280 100% 70%) 0%, hsl(320 100% 60%) 50%, hsl(180 100% 50%) 100%);
--gradient-aurora: linear-gradient(135deg, hsl(280 80% 60%) 0%, hsl(320 90% 65%) 25%, hsl(180 85% 55%) 50%, hsl(160 90% 50%) 75%, hsl(280 80% 60%) 100%);
--mesh-gradient: radial-gradient(at 40% 20%, hsl(280 100% 30%) 0px, transparent 50%),
                 radial-gradient(at 80% 0%, hsl(180 100% 20%) 0px, transparent 50%),
                 radial-gradient(at 0% 50%, hsl(320 100% 20%) 0px, transparent 50%);
```

### **Universe Modern Component Patterns**
```javascript
// Neon Card with Glow
className="rounded-2xl bg-card border-2 border-primary/30 
  shadow-[0_0_40px_-10px_hsl(280_100%_70%/0.3)]
  hover:shadow-[0_0_60px_-5px_hsl(280_100%_70%/0.5)]
  hover:border-primary/60 transition-all duration-500
  backdrop-blur-xl bg-gradient-to-br from-card via-card to-card-accent/50"

// Cyberpunk Button
className="rounded-xl h-11 px-6 font-bold 
  bg-gradient-to-r from-primary via-accent to-secondary 
  text-white uppercase tracking-wider
  hover:shadow-[0_0_40px_hsl(280_100%_70%/0.6)]
  hover:scale-105 active:scale-95
  transition-all duration-300 
  border border-primary/50 hover:border-primary
  relative overflow-hidden
  before:absolute before:inset-0 before:bg-gradient-to-r 
  before:from-transparent before:via-white/20 before:to-transparent
  before:translate-x-[-200%] hover:before:translate-x-[200%]
  before:transition-transform before:duration-700"

// Holographic Input
className="h-12 w-full rounded-xl border-2 border-secondary/40
  bg-card/50 backdrop-blur-xl px-4 py-3
  text-foreground font-medium
  focus:outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/50
  focus:shadow-[0_0_30px_hsl(180_100%_50%/0.3)]
  placeholder:text-muted-foreground/60
  transition-all duration-300"

// Aurora Gradient Background
className="fixed inset-0 -z-10 
  bg-[radial-gradient(ellipse_at_top,_hsl(280_100%_15%)_0%,_hsl(230_35%_7%)_50%)]
  before:absolute before:inset-0 
  before:bg-[radial-gradient(circle_at_40%_20%,_hsl(280_100%_30%/0.3)_0%,_transparent_50%)]
  after:absolute after:inset-0
  after:bg-[radial-gradient(circle_at_80%_80%,_hsl(180_100%_30%/0.2)_0%,_transparent_50%)]
  animate-pulse-slow"

// Neon Badge
className="inline-flex items-center rounded-md px-3 py-1 text-xs font-bold uppercase
  bg-primary/10 text-primary border border-primary/50
  shadow-[0_0_20px_hsl(280_100%_70%/0.3)]
  hover:bg-primary/20 hover:shadow-[0_0_30px_hsl(280_100%_70%/0.5)]
  transition-all duration-300"

// Glowing Divider
className="h-px w-full bg-gradient-to-r from-transparent via-primary to-transparent 
  shadow-[0_0_10px_hsl(280_100%_70%/0.5)]
  animate-pulse-slow"
```

### **Universe Modern Animations**
```javascript
// Neon pulse
'neon-pulse': {
  '0%, 100%': { 
    opacity: '1', 
    boxShadow: '0 0 20px hsl(280 100% 70% / 0.3)' 
  },
  '50%': { 
    opacity: '0.8', 
    boxShadow: '0 0 40px hsl(280 100% 70% / 0.6)' 
  }
}

// Holographic shimmer
'holo-shimmer': {
  '0%': { backgroundPosition: '-200% center' },
  '100%': { backgroundPosition: '200% center' }
}

// Glitch effect
'glitch': {
  '0%, 100%': { transform: 'translate(0)' },
  '20%': { transform: 'translate(-2px, 2px)' },
  '40%': { transform: 'translate(-2px, -2px)' },
  '60%': { transform: 'translate(2px, 2px)' },
  '80%': { transform: 'translate(2px, -2px)' }
}

// Floating
'float': {
  '0%, 100%': { transform: 'translateY(0px)' },
  '50%': { transform: 'translateY(-10px)' }
}
```

---

## 📋 COMPLETE TRI-THEME SINGLE PROMPT

**Copy this complete prompt for Light + Dark + Universe Modern themes:**

> "Build a modern React + Vite + Tailwind CSS platform with THREE complete themes: **LIGHT MODE**, **DARK MODE**, and **UNIVERSE MODERN** (cosmic/cyberpunk). 
>
> **Fonts:** Inter (body), Space Grotesk (headings).
>
> **LIGHT MODE:** Background off-white `220 17% 98%`, primary emerald `160 84% 39%`, secondary purple `262 83% 58%`, accent amber `38 92% 50%`. Cards with neomorphic shadows (8px 8px 16px gray), soft 3D depth, rounded-2xl borders.
>
> **DARK MODE:** True dark background `#121212` (0 0% 7%), elevated card `0 0% 12%`, brighter primary `160 84% 45%`, secondary `262 83% 63%`, accent `38 92% 55%`. Neomorphic shadows (10px 10px 20px black).
>
> **UNIVERSE MODERN:** Deep space blue-black background `230 35% 7%`, neon purple primary `280 100% 70%`, cyan secondary `180 100% 50%`, hot pink accent `320 100% 60%`, neon green tertiary `160 100% 50%`. Aurora gradient backgrounds with radial-gradient mesh overlays. All cards have neon glow borders with `border-2 border-primary/30` and `shadow-[0_0_40px_-10px_hsl(280_100%_70%/0.3)]`. Buttons use cosmic gradients `from-primary via-accent to-secondary` with holographic shimmer effect on hover (before:pseudo-element sliding shine). Inputs have cyan glowing focus states `focus:shadow-[0_0_30px_hsl(180_100%_50%/0.3)]`. Add neon-pulse animation (1-3s), holographic shimmer, glitch effects, and floating animations. Badges glow with uppercase text. Use backdrop-blur-xl for glassmorphic overlays.
>
> **SHARED STYLES:** Buttons `rounded-xl h-11 px-6 font-bold` with `hover:scale-105 active:scale-95 transition-all duration-300`. Cards `rounded-2xl` with `hover:scale-[1.02]`. Inputs `h-12 rounded-xl border-2`. Smooth animations: fade-in 0.5s, scale-in 0.2s. Icons lucide-react `h-4 w-4`. Layout: fixed header `h-18` (72px) with backdrop-blur, sidebar `w-64`, main `ml-64 pt-18 max-w-7xl`. Responsive grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6`. Spacing: `p-6` cards, `gap-6` grids.
>
> **Theme Toggle:** Implement three-way toggle button (Light/Dark/Universe) using class strategy with `[data-theme="light"]`, `[data-theme="dark"]`, `[data-theme="universe"]` on root element. Universe theme includes animated cosmic backgrounds with mesh gradients, neon borders on all interactive elements, and pulsing glow effects. All components accessible with `focus-visible:ring-2`. Use shadcn/ui (Button, Card, Dialog, Input, Badge, Table, Select). Ensure smooth theme transitions with `transition-colors duration-500` on root element. Universe mode should feel futuristic, high-tech, and immersive with constant subtle animations."

---

## 🎨 QUICK THEME REFERENCE

**LIGHT:** Clean, professional, soft shadows, green/purple/amber palette, neomorphic depth
**DARK:** Sophisticated, true dark, elevated surfaces, brighter accents, premium feel  
**UNIVERSE:** Cosmic, cyberpunk, neon glows, purple/cyan/pink palette, holographic effects, animated backgrounds

**Use this tri-theme system for ultimate flexibility and modern visual appeal across all user preferences!**
