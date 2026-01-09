/**
 * KRONOS - LoadingState Component
 * Standardized loading states: skeleton for content, spinner for actions
 */
import React from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

interface SkeletonProps {
    className?: string;
    /** Preset skeleton types */
    variant?: 'text' | 'title' | 'avatar' | 'card' | 'button' | 'table-row';
    /** Number of items to render */
    count?: number;
}

/**
 * Skeleton loader for content placeholders
 */
export const Skeleton: React.FC<SkeletonProps> = ({
    className,
    variant = 'text',
    count = 1
}) => {
    const variants = {
        text: 'h-4 w-full rounded',
        title: 'h-6 w-3/4 rounded',
        avatar: 'h-10 w-10 rounded-full',
        card: 'h-32 w-full rounded-xl',
        button: 'h-10 w-24 rounded-lg',
        'table-row': 'h-12 w-full rounded',
    };

    return (
        <>
            {Array.from({ length: count }).map((_, i) => (
                <div
                    key={i}
                    className={clsx(
                        'animate-pulse bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%]',
                        variants[variant],
                        className,
                        count > 1 && i > 0 && 'mt-2'
                    )}
                    style={{
                        animation: 'shimmer 1.5s infinite',
                    }}
                />
            ))}
        </>
    );
};

interface SpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

/**
 * Spinner for action loading states
 */
export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
    const sizes = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
    };

    return (
        <Loader2
            className={clsx(
                'animate-spin text-primary',
                sizes[size],
                className
            )}
        />
    );
};

interface LoadingOverlayProps {
    /** Message to display below spinner */
    message?: string;
}

/**
 * Full overlay loading state
 */
export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = 'Caricamento...' }) => {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
                <Spinner size="lg" />
                <span className="text-sm font-medium text-slate-600">{message}</span>
            </div>
        </div>
    );
};

interface PageLoadingProps {
    /** Show skeleton placeholders for content areas */
    variant?: 'spinner' | 'skeleton';
}

/**
 * Page-level loading state
 */
export const PageLoading: React.FC<PageLoadingProps> = ({ variant = 'skeleton' }) => {
    if (variant === 'spinner') {
        return (
            <div className="flex items-center justify-center py-20">
                <Spinner size="lg" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header skeleton */}
            <div className="space-y-2">
                <Skeleton variant="text" className="w-32 h-3" />
                <Skeleton variant="title" />
                <Skeleton variant="text" className="w-1/2 h-3" />
            </div>

            {/* Content skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Skeleton variant="card" />
                <Skeleton variant="card" />
                <Skeleton variant="card" />
            </div>

            {/* Table skeleton */}
            <div className="space-y-2">
                <Skeleton variant="table-row" />
                <Skeleton variant="table-row" />
                <Skeleton variant="table-row" />
                <Skeleton variant="table-row" />
            </div>
        </div>
    );
};

export default { Skeleton, Spinner, LoadingOverlay, PageLoading };
