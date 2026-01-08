import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps<T extends React.ElementType = 'button'> {
  as?: T;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  disabled?: boolean;
}

export const Button = <T extends React.ElementType = 'button'>({
  as,
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}: ButtonProps<T> & React.ComponentPropsWithoutRef<T>) => {
  const Component = as || 'button';

  // Base styles for all buttons
  const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus:ring-2 focus:ring-offset-1';

  // Variant styles
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-focus shadow-sm hover:shadow focus:ring-primary/30 border border-transparent',
    secondary: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-sm focus:ring-slate-200',
    outline: 'bg-transparent text-primary border border-primary hover:bg-primary/5 focus:ring-primary/30',
    ghost: 'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-transparent focus:ring-slate-200',
    danger: 'bg-error text-white hover:bg-red-600 shadow-sm focus:ring-error/30 border border-transparent',
    success: 'bg-success text-white hover:bg-green-600 shadow-sm focus:ring-success/30 border border-transparent',
  };

  // Size styles
  const sizes = {
    sm: 'text-xs px-3 py-1.5 h-8',
    md: 'text-sm px-4 py-2 h-10',
    lg: 'text-base px-6 py-3 h-12',
  };

  const combinedClassName = `
    ${baseStyles}
    ${variants[variant]}
    ${sizes[size]}
    ${className}
  `.trim();

  return (
    <Component
      className={combinedClassName}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <>
          {icon && <span className="shrink-0">{icon}</span>}
          {children}
        </>
      )}
    </Component>
  );
};
