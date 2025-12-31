import React from 'react';

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
  const baseClass = 'btn-shared';
  const variantClass = `btn-${variant}`;
  const sizeClass = `btn-${size}`;

  return (
    <Component
      className={`${baseClass} ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="btn-spinner"></span>
      ) : (
        <>
          {icon && <span className="btn-icon">{icon}</span>}
          {children}
        </>
      )}

      <style>{`
        .btn-shared {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-weight: 500;
          border-radius: 8px;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
          border: 1px solid transparent;
          font-family: inherit;
        }

        .btn-shared:active {
          transform: scale(0.98);
        }

        .btn-shared:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          pointer-events: none;
        }

        /* Sizes */
        .btn-sm { padding: 6px 12px; font-size: 13px; }
        .btn-md { padding: 10px 18px; font-size: 14px; }
        .btn-lg { padding: 12px 24px; font-size: 16px; }

        /* Variants */
        .btn-primary {
          background: var(--color-primary);
          color: white;
          box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.3);
        }
        .btn-primary:hover {
          filter: brightness(1.1);
          transform: translateY(-1px);
        }

        .btn-secondary {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          color: var(--color-text-primary);
        }
        .btn-secondary:hover {
          background: var(--color-bg);
        }

        .btn-outline {
          background: transparent;
          border: 1.5px solid var(--color-primary);
          color: var(--color-primary);
        }
        .btn-outline:hover {
          background: var(--color-primary-light);
        }

        .btn-ghost {
          background: transparent;
          color: var(--color-text-secondary);
        }
        .btn-ghost:hover {
          background: rgba(0,0,0,0.05);
          color: var(--color-text-primary);
        }

        .btn-danger {
          background: var(--color-danger);
          color: white;
        }
        .btn-success {
          background: var(--color-success);
          color: white;
        }

        .btn-spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: btn-spin 0.8s linear infinite;
        }

        @keyframes btn-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Component>
  );
};
