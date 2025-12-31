import React from 'react';

interface CardProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    className?: string;
    footer?: React.ReactNode;
    headerAction?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
    children,
    title,
    subtitle,
    className = '',
    footer,
    headerAction,
}) => {
    return (
        <div className={`premium-card ${className}`}>
            {(title || subtitle || headerAction) && (
                <div className="card-header">
                    <div className="header-text">
                        {title && <h3 className="card-title">{title}</h3>}
                        {subtitle && <p className="card-subtitle">{subtitle}</p>}
                    </div>
                    {headerAction && <div className="header-action">{headerAction}</div>}
                </div>
            )}

            <div className="card-body">
                {children}
            </div>

            {footer && (
                <div className="card-footer">
                    {footer}
                </div>
            )}

            <style>{`
        .premium-card {
          background: white;
          border-radius: 16px;
          border: 1px solid var(--color-border-light);
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
          overflow: hidden;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .premium-card:hover {
          box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
        }

        .card-header {
          padding: 20px 24px;
          border-bottom: 1px solid var(--color-border-light);
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .card-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0;
        }

        .card-subtitle {
          font-size: 14px;
          color: var(--color-text-secondary);
          margin: 4px 0 0 0;
        }

        .card-body {
          padding: 24px;
        }

        .card-footer {
          padding: 16px 24px;
          background: var(--color-bg-light);
          border-top: 1px solid var(--color-border-light);
        }
      `}</style>
        </div>
    );
};
