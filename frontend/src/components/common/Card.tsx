import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  footer?: React.ReactNode;
  headerAction?: React.ReactNode;
  /** Make the card non-hoverable */
  static?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  className = '',
  footer,
  headerAction,
  static: isStatic = false,
}) => {
  return (
    <div
      className={clsx(
        'bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden transition-shadow duration-200',
        !isStatic && 'hover:shadow-md',
        className
      )}
    >
      {(title || subtitle || headerAction) && (
        <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-start">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-slate-900 m-0">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-slate-500 mt-1 m-0">{subtitle}</p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}

      <div className="p-6">
        {children}
      </div>

      {footer && (
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100">
          {footer}
        </div>
      )}
    </div>
  );
};
