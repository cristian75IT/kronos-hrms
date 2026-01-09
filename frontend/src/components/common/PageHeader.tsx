/**
 * KRONOS - PageHeader Component  
 * Page title with optional breadcrumbs, description, and action buttons
 */
import React from 'react';
import { Breadcrumb, type BreadcrumbItem } from './Breadcrumb';

export interface PageHeaderProps {
    title: string;
    description?: string;
    breadcrumbs?: BreadcrumbItem[];
    actions?: React.ReactNode;
    /** Sticky header that stays at top when scrolling */
    sticky?: boolean;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
    title,
    description,
    breadcrumbs,
    actions,
    sticky = false,
}) => {
    return (
        <div
            className={`
                flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6
                ${sticky ? 'sticky top-0 z-10 bg-slate-50/95 backdrop-blur-sm py-4 -mx-6 px-6 border-b border-slate-100' : ''}
            `}
        >
            <div className="min-w-0 flex-1">
                {/* Breadcrumbs */}
                {breadcrumbs && breadcrumbs.length > 0 && (
                    <Breadcrumb items={breadcrumbs} className="mb-2" />
                )}

                <h1 className="text-2xl font-bold text-slate-900 truncate">{title}</h1>
                {description && (
                    <p className="mt-1 text-sm text-slate-500 line-clamp-2">{description}</p>
                )}
            </div>

            {actions && (
                <div className="flex items-center gap-3 shrink-0">
                    {actions}
                </div>
            )}
        </div>
    );
};

export default PageHeader;
