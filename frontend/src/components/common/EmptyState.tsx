/**
 * KRONOS - Empty State Component
 * standardized empty state with premium aesthetics
 */
import React from 'react';
import { clsx } from 'clsx';
import { Button } from './Button';

interface EmptyStateProps {
    title: string;
    description?: string;
    icon?: React.ElementType;
    actionLabel?: string;
    onAction?: () => void;
    className?: string;
    variant?: 'default' | 'small' | 'minimal';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
    title,
    description,
    icon: Icon,
    actionLabel,
    onAction,
    className,
    variant = 'default'
}) => {
    if (variant === 'minimal') {
        return (
            <div className={clsx("flex items-center justify-center gap-2 py-4 text-slate-400", className)}>
                {Icon && <Icon size={18} />}
                <span className="text-sm">{title}</span>
            </div>
        );
    }

    if (variant === 'small') {
        return (
            <div className={clsx("flex flex-col items-center justify-center py-8 px-4 text-center", className)}>
                {Icon && (
                    <div className="bg-slate-50 p-2 rounded-full mb-2">
                        <Icon size={20} className="text-slate-400" />
                    </div>
                )}
                <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
                {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
                {actionLabel && onAction && (
                    <Button
                        onClick={onAction}
                        size="sm"
                        variant="ghost"
                        className="mt-2 h-8 text-xs text-primary"
                    >
                        {actionLabel}
                    </Button>
                )}
            </div>
        );
    }

    // Default Variant
    return (
        <div className={clsx(
            "flex flex-col items-center justify-center py-12 px-6 text-center animate-fadeIn",
            className
        )}>
            {Icon && (
                <div className="bg-slate-50 p-4 rounded-full mb-4 shadow-sm border border-slate-100 ring-4 ring-slate-50/50">
                    <Icon size={32} className="text-slate-400" />
                </div>
            )}
            <h3 className="text-lg font-semibold text-slate-900 mb-2">{title}</h3>
            {description && (
                <p className="text-slate-500 max-w-sm mx-auto mb-6 text-sm leading-relaxed">
                    {description}
                </p>
            )}
            {actionLabel && onAction && (
                <Button onClick={onAction} variant="secondary">
                    {actionLabel}
                </Button>
            )}
        </div>
    );
};
