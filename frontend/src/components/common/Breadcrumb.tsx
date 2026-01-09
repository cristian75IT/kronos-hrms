/**
 * KRONOS - Breadcrumb Component
 * Navigation breadcrumb for page hierarchy
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { clsx } from 'clsx';

export interface BreadcrumbItem {
    label: string;
    path?: string;
}

interface BreadcrumbProps {
    items: BreadcrumbItem[];
    /** Show home icon as first item */
    showHome?: boolean;
    className?: string;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
    items,
    showHome = true,
    className,
}) => {
    const allItems = showHome
        ? [{ label: 'Home', path: '/' }, ...items]
        : items;

    return (
        <nav
            aria-label="Breadcrumb"
            className={clsx('flex items-center gap-1 text-sm', className)}
        >
            <ol className="flex items-center gap-1 list-none p-0 m-0">
                {allItems.map((item, index) => {
                    const isLast = index === allItems.length - 1;
                    const isFirst = index === 0 && showHome;

                    return (
                        <li key={index} className="flex items-center gap-1">
                            {index > 0 && (
                                <ChevronRight size={14} className="text-slate-300" aria-hidden="true" />
                            )}

                            {item.path && !isLast ? (
                                <Link
                                    to={item.path}
                                    className="flex items-center gap-1.5 text-slate-500 hover:text-primary transition-colors"
                                >
                                    {isFirst && <Home size={14} />}
                                    {!isFirst && item.label}
                                </Link>
                            ) : (
                                <span
                                    className={clsx(
                                        'flex items-center gap-1.5',
                                        isLast ? 'text-slate-900 font-medium' : 'text-slate-500'
                                    )}
                                    aria-current={isLast ? 'page' : undefined}
                                >
                                    {isFirst && showHome && !item.path && <Home size={14} />}
                                    {(!isFirst || !showHome) && item.label}
                                </span>
                            )}
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};

export default Breadcrumb;
