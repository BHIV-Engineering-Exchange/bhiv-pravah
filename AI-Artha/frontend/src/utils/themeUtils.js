/**
 * Theme Utilities
 * Helper functions and constants for working with the theme system
 */

import clsx from 'clsx';

// ============================================
// BUTTON VARIANTS
// ============================================
export const buttonVariants = {
  primary: 'btn btn-primary btn-md',
  secondary: 'btn btn-secondary btn-md',
  accent: 'btn btn-accent btn-md',
  outline: 'btn btn-outline btn-md',
  ghost: 'btn btn-ghost btn-md',
  destructive: 'btn btn-destructive btn-md',
  success: 'btn btn-success btn-md',
};

export const buttonSizes = {
  sm: 'btn-sm',
  md: 'btn-md',
  lg: 'btn-lg',
  icon: 'btn-icon',
};

/**
 * Get button classes with variants and sizes
 */
export const getButtonClasses = (variant = 'primary', size = 'md', className = '') => {
  return clsx(
    'btn',
    variant && `btn-${variant}`,
    size && buttonSizes[size],
    className
  );
};

// ============================================
// CARD VARIANTS
// ============================================
export const cardVariants = {
  default: 'card',
  neo: 'card-neo',
  glow: 'card-glow',
  glass: 'glass rounded-2xl p-6',
};

/**
 * Get card classes with variants
 */
export const getCardClasses = (variant = 'default', className = '') => {
  return clsx(cardVariants[variant] || cardVariants.default, className);
};

// ============================================
// BADGE VARIANTS
// ============================================
export const badgeVariants = {
  primary: 'badge badge-primary',
  secondary: 'badge badge-secondary',
  accent: 'badge badge-accent',
  success: 'badge badge-success',
  warning: 'badge badge-warning',
  destructive: 'badge badge-destructive',
  info: 'badge badge-info',
  muted: 'badge badge-muted',
};

/**
 * Get badge classes with variants
 */
export const getBadgeClasses = (variant = 'primary', className = '') => {
  return clsx(badgeVariants[variant] || badgeVariants.primary, className);
};

// ============================================
// INPUT VARIANTS
// ============================================
export const inputSizes = {
  sm: 'input-sm',
  md: '',
  lg: 'input-lg',
};

/**
 * Get input classes with sizes
 */
export const getInputClasses = (size = 'md', className = '') => {
  return clsx('input', inputSizes[size], className);
};

// ============================================
// FOCUS RING UTILITY
// ============================================
export const focusRing = 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background';

// ============================================
// DISABLED STATE UTILITY
// ============================================
export const disabledState = 'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed';

// ============================================
// TRANSITION UTILITIES
// ============================================
export const transitions = {
  fast: 'transition-all duration-150 ease-out',
  normal: 'transition-all duration-300 ease-neo',
  slow: 'transition-all duration-500 ease-out',
  cyber: 'transition-all duration-300 ease-cyber',
};

// ============================================
// ANIMATION UTILITIES
// ============================================
export const animations = {
  fadeIn: 'animate-fade-in',
  fadeInUp: 'animate-fade-in-up',
  scaleIn: 'animate-scale-in',
  slideUp: 'animate-slide-up',
  slideDown: 'animate-slide-down',
  pulseSlow: 'animate-pulse-slow',
  glow: 'animate-glow',
  float: 'animate-float',
};

// ============================================
// SHADOW UTILITIES
// ============================================
export const shadows = {
  neo: 'shadow-neo',
  neoDark: 'shadow-neo-dark',
  glow: 'shadow-glow',
  glowLg: 'shadow-glow-lg',
  glowXl: 'shadow-glow-xl',
  neon: 'shadow-neon',
  neonCyan: 'shadow-neon-cyan',
  neonPink: 'shadow-neon-pink',
  glass: 'shadow-glass',
  glassLg: 'shadow-glass-lg',
};

// ============================================
// GRADIENT UTILITIES
// ============================================
export const gradients = {
  primary: 'bg-gradient-primary',
  secondary: 'bg-gradient-secondary',
  accent: 'bg-gradient-accent',
  card: 'bg-gradient-card',
  cosmic: 'bg-gradient-cosmic',
  aurora: 'bg-gradient-aurora',
};

// ============================================
// GLASSMORPHISM UTILITY
// ============================================
export const glass = {
  light: 'glass',
  heavy: 'glass-heavy',
};

// ============================================
// SEMANTIC COLOR CLASSES (for status indicators)
// ============================================
export const statusColors = {
  success: {
    bg: 'bg-success/10',
    text: 'text-success',
    border: 'border-success/20',
  },
  warning: {
    bg: 'bg-warning/10',
    text: 'text-warning',
    border: 'border-warning/20',
  },
  error: {
    bg: 'bg-destructive/10',
    text: 'text-destructive',
    border: 'border-destructive/20',
  },
  info: {
    bg: 'bg-info/10',
    text: 'text-info',
    border: 'border-info/20',
  },
  muted: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
  },
};

/**
 * Get status indicator classes
 */
export const getStatusClasses = (status = 'muted') => {
  const colors = statusColors[status] || statusColors.muted;
  return clsx(colors.bg, colors.text, colors.border, 'border');
};

export default {
  buttonVariants,
  buttonSizes,
  getButtonClasses,
  cardVariants,
  getCardClasses,
  badgeVariants,
  getBadgeClasses,
  inputSizes,
  getInputClasses,
  focusRing,
  disabledState,
  transitions,
  animations,
  shadows,
  gradients,
  glass,
  statusColors,
  getStatusClasses,
};
